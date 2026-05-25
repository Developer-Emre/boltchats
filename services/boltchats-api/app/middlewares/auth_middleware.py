from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.core.security import decode_token
from app.exceptions.http_exceptions import UnauthorizedException
from app.utils.constants import ErrorMessage, TokenType

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> str:
    """FastAPI dependency — validates access JWT and returns user_id."""
    try:
        claims = decode_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    if claims.get("type") != TokenType.ACCESS:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    user_id: str | None = claims.get("sub")
    if not user_id:
        raise UnauthorizedException(ErrorMessage.INVALID_TOKEN)

    return user_id
