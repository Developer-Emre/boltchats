from datetime import datetime, timezone

from pydantic import BaseModel, Field


class RoomDocument(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    name: str
    description: str = ""
    owner_id: str
    member_ids: list[str] = Field(default_factory=list)
    is_private: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    model_config = {"populate_by_name": True}
