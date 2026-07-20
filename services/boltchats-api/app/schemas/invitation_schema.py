from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreateInvitationRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member")  # member, admin


class InvitationResponse(BaseModel):
    id: str
    workspace_id: str
    invited_email: str
    role: str
    code: str
    status: str  # pending, accepted, expired, revoked
    invited_by: str
    created_at: datetime
    expires_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AcceptInvitationRequest(BaseModel):
    code: str


class InvitationListResponse(BaseModel):
    items: list[InvitationResponse]
    next_cursor: str | None = None
