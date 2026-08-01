"""Base application exceptions"""


class AppError(Exception):
    """Base application error"""
    pass


class NotFoundError(AppError):
    """Resource not found"""
    pass


class ConflictError(AppError):
    """Resource conflict (e.g., duplicate creation)"""
    pass


class ValidationError(AppError):
    """Validation failed"""
    pass


class UnauthorizedError(AppError):
    """Authentication failed"""
    pass


class ForbiddenError(AppError):
    """Authorization failed"""
    pass


class InternalError(AppError):
    """Internal server error"""
    pass
