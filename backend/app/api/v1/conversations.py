from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_conversation_service, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdate,
    MessageCreate,
    MessageFeedbackRequest,
    MessageResponse,
)
from app.services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["Conversations & Legal Chat"])


@router.get("", response_model=APIResponse[List[ConversationResponse]])
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    items = await service.list_conversations(current_user, limit=limit, offset=offset)
    return APIResponse(
        success=True,
        data=items,
        message="Conversations listed successfully",
    )


@router.post("", response_model=APIResponse[ConversationResponse], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    conv = await service.create_conversation(current_user, payload)
    return APIResponse(
        success=True,
        data=conv,
        message="Conversation created successfully",
    )


@router.get("/{conversation_id}", response_model=APIResponse[ConversationDetailResponse])
async def get_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    detail = await service.get_conversation_detail(conversation_id, current_user)
    return APIResponse(
        success=True,
        data=detail,
        message="Conversation retrieved successfully",
    )


@router.patch("/{conversation_id}", response_model=APIResponse[ConversationResponse])
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    updated = await service.update_conversation(conversation_id, current_user, payload)
    return APIResponse(
        success=True,
        data=updated,
        message="Conversation updated successfully",
    )


@router.delete("/{conversation_id}", response_model=APIResponse[Dict[str, bool]])
async def delete_conversation(
    conversation_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    await service.delete_conversation(conversation_id, current_user)
    return APIResponse(
        success=True,
        data={"deleted": True},
        message="Conversation deleted successfully",
    )


@router.post("/{conversation_id}/messages", response_model=APIResponse[MessageResponse])
async def send_message(
    conversation_id: str,
    payload: MessageCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    assistant_msg = await service.send_message(conversation_id, current_user, payload)
    return APIResponse(
        success=True,
        data=assistant_msg,
        message="Message processed and response generated",
    )


@router.post("/{conversation_id}/messages/{message_id}/feedback", response_model=APIResponse[Dict[str, Any]])
async def submit_message_feedback(
    conversation_id: str,
    message_id: str,
    payload: MessageFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ConversationService = Depends(get_conversation_service),
):
    res = await service.submit_feedback(conversation_id, message_id, current_user, payload)
    return APIResponse(
        success=True,
        data=res,
        message="Feedback submitted successfully",
    )
