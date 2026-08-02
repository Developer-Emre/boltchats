"""
Request/Response schemas for Auth domain
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: str = Field(..., min_length=1)
    organization_name: str = Field(..., min_length=1)


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh access token"""
    refresh_token: str


class TokenResponse(BaseModel):
    """Access + refresh token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user_id: Optional[str] = None  # Added for register/login responses
    member_id: Optional[str] = None  # Added for register/login responses
    organization_id: Optional[str] = None  # Added for register/login responses
    workspace_id: Optional[str] = None  # Added for register/login responses

class CurrentUserResponse(BaseModel):
    """Current authenticated user info"""
    user_id: str
    email: str
    full_name: str
    organization_id: str
    workspace_id: str
    member_id: str
    roles: list[str]
    permissions: list[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    version: Optional[str] = None
    timestamp: datetime


class RegisterResponse(BaseModel):
    """Response after user registration (email verification required)"""
    user_id: str
    email: str
    message: str = "Registration successful. Please verify your email."
    verification_token: Optional[str] = None  # For development/testing
    verification_link: Optional[str] = None  # For production (with frontend URL)


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str


class VerifyEmailResponse(BaseModel):
    """Email verification response"""
    user_id: str
    email: str
    verified: bool
    message: str = "Email verified successfully. You can now login."
