"""Custom exceptions for SparkQuark API"""

from .base import AppError, NotFoundError, ConflictError, ValidationError, UnauthorizedError, ForbiddenError, InternalError
from .http_exceptions import RateLimitException

__all__ = [
    "AppError",
    "NotFoundError",
    "ConflictError",
    "ValidationError",
    "UnauthorizedError",
    "ForbiddenError",
    "InternalError",
    "RateLimitException",
]
