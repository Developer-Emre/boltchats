"""HTTP-related exceptions"""

from .base import AppError


class RateLimitException(AppError):
    """Rate limit exceeded"""
    pass
