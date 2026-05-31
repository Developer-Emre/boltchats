import asyncio
import re
import structlog
from functools import partial
from jose import JWTError
from pymongo.errors import PyMongoError
from redis.asyncio import Redis

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.exceptions.http_exceptions import (
    ConflictException,
    DatabaseException,
    UnauthorizedException,
)
from app.schemas.auth_schema import (
    AccessTokenResponse,
    AuthResponse,
    GoogleAuthRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    UserInfo,
)
from app.utils.constants import (
    REDIS_PREFIX_REFRESH_TOKEN,
    Collection,
    ErrorMessage,
    TokenType,
)

logger = structlog.get_logger()


async def google_login(payload: GoogleAuthRequest, db, redis: Redis) -> AuthResponse:
    """Verify a Google id_token, then find-or-create the user."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    if not settings.google_client_id:
        raise UnauthorizedException("Google login is not configured on this server")

    try:
        # verify_oauth2_token is blocking — run in executor to avoid blocking the loop
        verify = partial(
            google_id_token.verify_oauth2_token,
            payload.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )
        id_info: dict = await asyncio.get_event_loop().run_in_executor(None, verify)
    except ValueError as exc:
        raise UnauthorizedException("Invalid Google token") from exc

    email: str = id_info["email"]
    google_sub: str = id_info["sub"]

    # Derive a clean username from the Google display name or email prefix
    raw_name: str = id_info.get("name", email.split("@")[0])
    username: str = re.sub(r"[^a-z0-9_]", "_", raw_name.lower().replace(" ", "_"))

    try:
        user = await db[Collection.USERS].find_one({"email": email})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query users") from exc

    if user:
        user_id = str(user["_id"])
        # Backfill google_id on first Google login for an email-registered account
        if not user.get("google_id"):
            await db[Collection.USERS].update_one(
                {"_id": user["_id"]},
                {"$set": {"google_id": google_sub}},
            )
    else:
        doc = {
            "username": username,
            "email": email,
            "google_id": google_sub,
            "hashed_password": None,
            "is_active": True,
        }
        try:
            result = await db[Collection.USERS].insert_one(doc)
        except PyMongoError as exc:
            raise DatabaseException("Failed to create user") from exc

        user_id = str(result.inserted_id)
        user = {"username": username, "email": email}

    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    ttl = settings.refresh_token_expire_days * 86400
    redis_key = f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}"
    await redis.set(redis_key, refresh_token, ex=ttl)

    await logger.ainfo("google_login", user_id=user_id, email=email)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user_id, username=user["username"], email=email),
    )


async def register(payload: RegisterRequest, db, redis: Redis) -> AuthResponse:
    try:
        existing = await db[Collection.USERS].find_one({"email": payload.email})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query users") from exc

    if existing:
        raise ConflictException(ErrorMessage.USER_ALREADY_EXISTS)

    hashed = hash_password(payload.password)
    doc = {
        "username": payload.username,
        "email": payload.email,
        "hashed_password": hashed,
        "is_active": True,
    }

    try:
        result = await db[Collection.USERS].insert_one(doc)
    except PyMongoError as exc:
        raise DatabaseException("Failed to create user") from exc

    user_id = str(result.inserted_id)
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    ttl = settings.refresh_token_expire_days * 86400
    redis_key = f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}"
    await redis.set(redis_key, refresh_token, ex=ttl)

    await logger.ainfo("user_registered", user_id=user_id, email=payload.email)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user_id, username=payload.username, email=payload.email),
    )


async def login(payload: LoginRequest, db, redis: Redis) -> AuthResponse:
    try:
        user = await db[Collection.USERS].find_one({"email": payload.email})
    except PyMongoError as exc:
        raise DatabaseException("Failed to query users") from exc

    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise UnauthorizedException(ErrorMessage.INVALID_CREDENTIALS)

    user_id = str(user["_id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)

    ttl = settings.refresh_token_expire_days * 86400
    redis_key = f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}"
    await redis.set(redis_key, refresh_token, ex=ttl)

    await logger.ainfo("user_logged_in", user_id=user_id)
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserInfo(id=user_id, username=user["username"], email=user["email"]),
    )


async def refresh(payload: RefreshRequest, redis: Redis) -> AccessTokenResponse:
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    if claims.get("type") != TokenType.REFRESH:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    user_id: str = claims["sub"]
    redis_key = f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}"
    stored = await redis.get(redis_key)

    if stored != payload.refresh_token:
        raise UnauthorizedException(ErrorMessage.REFRESH_TOKEN_NOT_FOUND)

    access_token = create_access_token(user_id)
    await logger.ainfo("token_refreshed", user_id=user_id)
    return AccessTokenResponse(access_token=access_token)


async def logout(payload: RefreshRequest, redis: Redis) -> None:
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    if claims.get("type") != TokenType.REFRESH:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    user_id: str = claims["sub"]
    redis_key = f"{REDIS_PREFIX_REFRESH_TOKEN}{user_id}"
    await redis.delete(redis_key)
    await logger.ainfo("user_logged_out", user_id=user_id)
