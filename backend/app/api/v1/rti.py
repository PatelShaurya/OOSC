"""
API Router for RTI Drafting Agent endpoints under /api/v1/rti.
"""
from typing import Optional
from fastapi import APIRouter, Depends, status

from app.api.deps import get_optional_user, get_rti_service
from app.schemas.auth import CurrentUser
from app.schemas.common import APIResponse
from app.schemas.rti import RTIDraftRequest, RTIDraftResponse
from app.services.rti_service import RTIDraftingService

router = APIRouter(prefix="/rti", tags=["RTI Drafting Agent"])


@router.post(
    "/draft",
    response_model=APIResponse[RTIDraftResponse],
    status_code=status.HTTP_200_OK,
    summary="Draft RTI Application",
    description="Converts citizen plain-language information request into a structured RTI Application draft with verified citations.",
)
async def draft_rti_application(
    payload: RTIDraftRequest,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    rti_service: RTIDraftingService = Depends(get_rti_service),
) -> APIResponse[RTIDraftResponse]:
    """
    Generates structured RTI application draft using grounded RAG retrieval.
    """
    result = await rti_service.generate_rti_draft(payload=payload, user=current_user)
    return APIResponse(
        success=True,
        data=result,
        message="RTI application draft generated successfully",
    )
