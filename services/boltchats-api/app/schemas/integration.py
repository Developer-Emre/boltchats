"""
Request/Response schemas for Integration & Notification domains
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IntegrationCreateRequest(BaseModel):
    """Create integration request"""
    provider: str = Field(..., description="Provider name (instagram, facebook, whatsapp, email, sendgrid)")
    name: str = Field(..., min_length=1, description="Integration display name")
    credentials: dict = Field(..., description="Provider-specific credentials")


class IntegrationUpdateRequest(BaseModel):
    """Update integration request"""
    name: Optional[str] = None
    credentials: Optional[dict] = None


class IntegrationResponse(BaseModel):
    """Integration response"""
    id: str
    organization_id: str
    provider: str
    provider_account_id: Optional[str]
    display_name: str
    name: str
    is_active: bool
    metadata: dict
    last_webhook_at: Optional[datetime]
    created_at: datetime


class WebhookResponse(BaseModel):
    """Webhook response"""
    url: str
    events: list[str]
    active: bool


class NotificationCreateRequest(BaseModel):
    """Send notification request"""
    recipient_id: str  # Member or user ID
    channel: str  # email, push, websocket
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    data: Optional[dict] = None


class NotificationResponse(BaseModel):
    """Notification response"""
    id: str
    organization_id: str
    recipient_id: str
    channel: str
    title: str
    message: str
    status: str  # pending, delivered, failed, bounced
    read_at: Optional[datetime]
    clicked_at: Optional[datetime]
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification list"""
    items: list[NotificationResponse]
    total: int
    limit: int
    offset: int


class EventResponse(BaseModel):
    """Event response"""
    id: str
    organization_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    status: str  # published, pending, processed, failed
    data: dict
    correlation_id: Optional[str]
    causation_id: Optional[str]
    created_at: datetime


class WorkflowStatusResponse(BaseModel):
    """Workflow execution status"""
    workflow_id: str
    workflow_name: str
    status: str  # pending, running, completed, failed, cancelled
    current_step: int
    total_steps: int
    results: dict
    error: Optional[str]
