import structlog
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
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserInfo,
)
from app.utils.constants import (
    REDIS_PREFIX_REFRESH_TOKEN,
    Collection,
    ErrorMessage,
    TokenType,
)

logger = structlog.get_logger()


async def register(payload: RegisterRequest, db) -> UserInfo:
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

    await logger.ainfo(
        "user_registered", user_id=str(result.inserted_id), email=payload.email
    )
    return UserInfo(
        id=str(result.inserted_id),
        username=payload.username,
        email=payload.email,
    )


async def login(payload: LoginRequest, db, redis: Redis) -> TokenResponse:
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
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


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
