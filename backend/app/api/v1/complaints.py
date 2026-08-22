from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import get_complaint_service, get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.complaint import (
    ComplaintCategory,
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatus,
    ComplaintUpdate,
    DocumentDraftResponse,
    ExportDocumentResponse,
    GenerateDocumentRequest,
)
from app.services.complaint_service import ComplaintService

router = APIRouter(prefix="/complaints", tags=["Complaints & Legal Document Drafting"])


@router.get("", response_model=APIResponse[List[ComplaintResponse]])
async def list_complaints(
    category: Optional[ComplaintCategory] = None,
    status: Optional[ComplaintStatus] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    items = await service.list_complaints(
        current_user,
        category=category,
        status=status,
        limit=limit,
        offset=offset,
    )
    return APIResponse(
        success=True,
        data=items,
        message="Complaints retrieved successfully",
    )


@router.post("", response_model=APIResponse[ComplaintResponse], status_code=status.HTTP_201_CREATED)
async def create_complaint(
    payload: ComplaintCreate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    complaint = await service.create_complaint(current_user, payload)
    return APIResponse(
        success=True,
        data=complaint,
        message="Complaint created successfully",
    )


@router.get("/{complaint_id}", response_model=APIResponse[ComplaintResponse])
async def get_complaint(
    complaint_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    complaint = await service.get_complaint(complaint_id, current_user)
    return APIResponse(
        success=True,
        data=complaint,
        message="Complaint details retrieved",
    )


@router.patch("/{complaint_id}", response_model=APIResponse[ComplaintResponse])
async def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    updated = await service.update_complaint(complaint_id, current_user, payload)
    return APIResponse(
        success=True,
        data=updated,
        message="Complaint updated successfully",
    )


@router.delete("/{complaint_id}", response_model=APIResponse[Dict[str, bool]])
async def delete_complaint(
    complaint_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    await service.delete_complaint(complaint_id, current_user)
    return APIResponse(
        success=True,
        data={"deleted": True},
        message="Complaint deleted successfully",
    )


@router.post("/{complaint_id}/generate-document", response_model=APIResponse[DocumentDraftResponse])
async def generate_complaint_document(
    complaint_id: str,
    payload: GenerateDocumentRequest,
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    draft = await service.generate_document(complaint_id, current_user, payload)
    return APIResponse(
        success=True,
        data=draft,
        message="Legal document synthesized and drafted successfully",
    )


@router.post("/{complaint_id}/export", response_model=APIResponse[ExportDocumentResponse])
async def export_complaint_document(
    complaint_id: str,
    format: str = Query("markdown", pattern="^(markdown|text)$"),
    current_user: CurrentUser = Depends(get_current_user),
    service: ComplaintService = Depends(get_complaint_service),
):
    exported = await service.export_document(complaint_id, current_user, file_format=format)
    return APIResponse(
        success=True,
        data=exported,
        message="Document export payload prepared",
    )
