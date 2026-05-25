from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    is_active: bool


class UpdateUserRequest(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=32)
