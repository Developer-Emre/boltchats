"""
Conversations Router

Endpoints for customers, conversations, messages, labels, drafts
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.schemas import (
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdateRequest,
    CustomerCreateRequest,
    CustomerResponse,
    DraftResponse,
    LabelCreateRequest,
    LabelResponse,
    LabelUpdateRequest,
    MessageCreateRequest,
    MessageDeleteRequest,
    MessageListResponse,
    MessageResponse,
    MessageUpdateRequest,
)
from app.services import (
    ConversationService,
    CustomerService,
    MessageService,
    LabelService,
    DraftService,
)

router = APIRouter(prefix="/conversations", tags=["conversations"])


# Customer endpoints
@router.post("/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreateRequest,
    current_user = Depends(get_current_user),
    service: CustomerService = Depends(),
):
    """Create customer"""
    try:
        customer = await service.create_customer(
            org_id=current_user["organization_id"],
            **payload.dict(),
        )
        return customer
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    current_user = Depends(get_current_user),
    service: CustomerService = Depends(),
):
    """Get customer by ID"""
    customer = await service.get_customer(
        org_id=current_user["organization_id"],
        customer_id=customer_id,
    )
    if not customer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return customer


# Conversation endpoints
@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreateRequest,
    current_user = Depends(get_current_user),
    service: ConversationService = Depends(),
):
    """Create conversation"""
    try:
        conversation = await service.create_conversation(
            org_id=current_user["organization_id"],
            **payload.dict(),
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    current_user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: ConversationService = Depends(),
):
    """List conversations"""
    conversations = await service.list_conversations(
        org_id=current_user["organization_id"],
        limit=limit,
        offset=offset,
    )
    return {
        "items": conversations,
        "total": len(conversations),
        "limit": limit,
        "offset": offset,
    }


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user = Depends(get_current_user),
    service: ConversationService = Depends(),
):
    """Get conversation by ID"""
    conversation = await service.get_conversation(
        org_id=current_user["organization_id"],
        conversation_id=conversation_id,
    )
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdateRequest,
    current_user = Depends(get_current_user),
    service: ConversationService = Depends(),
):
    """Update conversation"""
    try:
        conversation = await service.update_conversation(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            data=payload.dict(exclude_none=True),
        )
        return conversation
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Message endpoints
@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    payload: MessageCreateRequest,
    current_user = Depends(get_current_user),
    service: MessageService = Depends(),
):
    """Send message in conversation"""
    try:
        message = await service.send_message(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            sender_id=current_user["member_id"],
            **payload.dict(),
        )
        return message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def list_messages(
    conversation_id: str,
    current_user = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: MessageService = Depends(),
):
    """List messages in conversation"""
    messages = await service.list_messages(
        org_id=current_user["organization_id"],
        conversation_id=conversation_id,
        limit=limit,
        offset=offset,
    )
    return {
        "items": messages,
        "total": len(messages),
        "limit": limit,
        "offset": offset,
    }


@router.patch("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def edit_message(
    conversation_id: str,
    message_id: str,
    payload: MessageUpdateRequest,
    current_user = Depends(get_current_user),
    service: MessageService = Depends(),
):
    """Edit message"""
    try:
        message = await service.edit_message(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            message_id=message_id,
            text=payload.text,
            edited_by=current_user["member_id"],
        )
        return message
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{conversation_id}/messages/{message_id}")
async def delete_message(
    conversation_id: str,
    message_id: str,
    payload: MessageDeleteRequest = None,
    current_user = Depends(get_current_user),
    service: MessageService = Depends(),
):
    """Delete message (soft delete)"""
    try:
        await service.delete_message(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            message_id=message_id,
            deleted_by=current_user["member_id"],
            reason=payload.reason if payload else None,
        )
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Label endpoints
@router.post("/{conversation_id}/labels", response_model=LabelResponse, status_code=status.HTTP_201_CREATED)
async def add_label_to_conversation(
    conversation_id: str,
    payload: LabelCreateRequest,
    current_user = Depends(get_current_user),
    service: LabelService = Depends(),
):
    """Add label to conversation"""
    try:
        label = await service.add_label_to_conversation(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            **payload.dict(),
        )
        return label
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{conversation_id}/labels/{label_id}")
async def remove_label_from_conversation(
    conversation_id: str,
    label_id: str,
    current_user = Depends(get_current_user),
    service: LabelService = Depends(),
):
    """Remove label from conversation"""
    try:
        await service.remove_label_from_conversation(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            label_id=label_id,
        )
        return {"status": "removed"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Draft endpoints
@router.get("/{conversation_id}/draft", response_model=DraftResponse)
async def get_draft(
    conversation_id: str,
    current_user = Depends(get_current_user),
    service: DraftService = Depends(),
):
    """Get draft for conversation"""
    draft = await service.get_draft(
        org_id=current_user["organization_id"],
        conversation_id=conversation_id,
        member_id=current_user["member_id"],
    )
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return draft


@router.post("/{conversation_id}/draft")
async def save_draft(
    conversation_id: str,
    payload: dict,
    current_user = Depends(get_current_user),
    service: DraftService = Depends(),
):
    """Save draft (auto-save)"""
    try:
        draft = await service.save_draft(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            member_id=current_user["member_id"],
            content=payload.get("content", ""),
        )
        return draft
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{conversation_id}/draft")
async def delete_draft(
    conversation_id: str,
    current_user = Depends(get_current_user),
    service: DraftService = Depends(),
):
    """Delete draft"""
    try:
        await service.delete_draft(
            org_id=current_user["organization_id"],
            conversation_id=conversation_id,
            member_id=current_user["member_id"],
        )
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
