from pydantic import BaseModel, EmailStr, Field


class GoogleAuthRequest(BaseModel):
    """Google id_token received from the frontend after Google Sign-In popup."""

    id_token: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    username: str
    email: str


class AuthResponse(BaseModel):
    """Returned by both /register and /login — includes tokens + user info."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserInfo
