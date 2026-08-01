"""
Integrations Router

Endpoints for provider integrations, webhooks, notifications
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.dependencies import get_integration_service

from app.schemas import (
    IntegrationCreateRequest,
    IntegrationResponse,
    IntegrationUpdateRequest,
    NotificationCreateRequest,
    NotificationListResponse,
    NotificationResponse,
    WebhookResponse,
)
from app.services import (
    IntegrationService,
    NotificationService,
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# Integration endpoints
@router.post("", response_model=IntegrationResponse, status_code=status.HTTP_201_CREATED)
async def create_integration(
    payload: IntegrationCreateRequest,
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Create provider integration"""
    try:
        integration = await service.create_integration(
            org_id=current_user["organization_id"],
            **payload.dict(),
        )
        return integration
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """List integrations for organization"""
    integrations = await service.list_integrations(
        org_id=current_user["organization_id"],
    )
    return integrations


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: str,
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Get integration by ID"""
    integration = await service.get_integration(
        org_id=current_user["organization_id"],
        integration_id=integration_id,
    )
    if not integration:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return integration


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: str,
    payload: IntegrationUpdateRequest,
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Update integration"""
    try:
        integration = await service.update_integration(
            org_id=current_user["organization_id"],
            integration_id=integration_id,
            data=payload.dict(exclude_none=True),
        )
        return integration
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: str,
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Delete integration"""
    try:
        await service.delete_integration(
            org_id=current_user["organization_id"],
            integration_id=integration_id,
        )
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Webhook endpoints
@router.get("/{integration_id}/webhook", response_model=WebhookResponse)
async def get_webhook_config(
    integration_id: str,
    current_user = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    """Get webhook configuration for integration"""
    config = await service.get_webhook_config(
        org_id=current_user["organization_id"],
        integration_id=integration_id,
    )
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return config


# Webhook receiver (public, no auth required)
@router.post("/webhooks/{provider}")
async def handle_webhook(
    provider: str,
    payload: dict,
    signature: str = None,
    timestamp: str = None,
    service: IntegrationService = Depends(get_integration_service),
):
    """
    Receive webhook from external provider.
    
    Provider-specific signature validation and payload processing.
    """
    try:
        result = await service.handle_webhook(
            provider=provider,
            payload=payload,
            signature=signature,
            timestamp=timestamp,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Notification endpoints
@router.post("/notifications", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def send_notification(
    payload: NotificationCreateRequest,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(),
):
    """Send notification to user"""
    try:
        notification_id = await service.send_notification(
            org_id=current_user["organization_id"],
            **payload.dict(),
        )
        notification = await service.notifications.read(notification_id)
        return notification
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/notifications", response_model=NotificationListResponse)
async def list_notifications(
    current_user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: NotificationService = Depends(),
):
    """List notifications for current user"""
    notifications = await service.get_notifications(
        org_id=current_user["organization_id"],
        recipient_id=current_user["member_id"],
        limit=limit,
    )
    return {
        "items": notifications,
        "total": len(notifications),
        "limit": limit,
        "offset": offset,
    }


@router.patch("/notifications/{notification_id}/read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(),
):
    """Mark notification as read"""
    try:
        notification = await service.mark_as_read(notification_id)
        return notification
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/notifications/{notification_id}/clicked", response_model=NotificationResponse)
async def mark_notification_clicked(
    notification_id: str,
    current_user = Depends(get_current_user),
    service: NotificationService = Depends(),
):
    """Mark notification as clicked (action taken)"""
    try:
        notification = await service.mark_as_clicked(notification_id)
        return notification
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
