import structlog
from jose import JWTError, jwt

logger = structlog.get_logger()


def decode_token(token: str, secret_key: str, algorithm: str) -> dict:
    """Decode and verify a JWT.

    Raises ValueError on invalid or expired token.
    The WS service only verifies tokens — it never issues them.
    """
    try:
        payload: dict = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError as exc:
        logger.warning("security.decode_failed", reason=str(exc))
        raise ValueError("Invalid or expired token") from exc
