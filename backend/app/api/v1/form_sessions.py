from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_current_user, get_form_service
from app.schemas.auth import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.form_session import (
    FormCompleteResponse,
    FormSessionCreate,
    FormSessionResponse,
    FormSessionStatus,
    FormStepSubmit,
)
from app.services.form_service import FormService

router = APIRouter(prefix="/form-sessions", tags=["Civic Form Sessions (RTI / Grievance)"])


@router.get("", response_model=APIResponse[List[FormSessionResponse]])
async def list_form_sessions(
    status: Optional[FormSessionStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: FormService = Depends(get_form_service),
):
    sessions = await service.list_sessions(current_user, status=status, limit=limit, offset=offset)
    return APIResponse(
        success=True,
        data=sessions,
        message="Form sessions retrieved successfully",
    )


@router.post("", response_model=APIResponse[FormSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_form_session(
    payload: FormSessionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: FormService = Depends(get_form_service),
):
    session = await service.create_session(current_user, payload)
    return APIResponse(
        success=True,
        data=session,
        message="Form session initiated successfully",
    )


@router.get("/{session_id}", response_model=APIResponse[FormSessionResponse])
async def get_form_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: FormService = Depends(get_form_service),
):
    session = await service.get_session(session_id, current_user)
    return APIResponse(
        success=True,
        data=session,
        message="Form session details retrieved",
    )


@router.post("/{session_id}/steps", response_model=APIResponse[FormSessionResponse])
async def submit_form_step(
    session_id: str,
    payload: FormStepSubmit,
    current_user: CurrentUser = Depends(get_current_user),
    service: FormService = Depends(get_form_service),
):
    updated_session = await service.submit_step(session_id, current_user, payload)
    return APIResponse(
        success=True,
        data=updated_session,
        message="Form step updated successfully",
    )


@router.post("/{session_id}/complete", response_model=APIResponse[FormCompleteResponse])
async def complete_form_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: FormService = Depends(get_form_service),
):
    completion = await service.complete_session(session_id, current_user)
    return APIResponse(
        success=True,
        data=completion,
        message="Form session completed and converted to filing draft",
    )
