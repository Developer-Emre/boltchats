import re

from bson import ObjectId
from bson.errors import InvalidId

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_-]{3,32}$")


def is_valid_object_id(value: str) -> bool:
    """Return True when *value* is a valid 24-char hex MongoDB ObjectId."""
    try:
        ObjectId(value)
        return True
    except (InvalidId, TypeError):
        return False


def is_strong_password(value: str) -> bool:
    """Return True when *value* meets minimum password strength requirements.

    Rules: at least 8 chars, one digit, one letter.
    """
    if len(value) < 8:
        return False
    has_digit = any(c.isdigit() for c in value)
    has_alpha = any(c.isalpha() for c in value)
    return has_digit and has_alpha


def is_valid_username(value: str) -> bool:
    """Return True when *value* is a valid username (3-32 alphanumeric/_/-)."""
    return bool(_USERNAME_RE.match(value))
