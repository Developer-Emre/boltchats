from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, Field


class UserDocument(BaseModel):
    """Represents a user document as stored in MongoDB."""

    id: str | None = Field(default=None, alias="_id")
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
