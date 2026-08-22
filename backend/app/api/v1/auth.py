from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_user_service
from app.schemas.auth import CurrentUser, UserProfileResponse, UserProfileUpdate
from app.schemas.common import APIResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication & User"])


@router.get("/me", response_model=APIResponse[UserProfileResponse])
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    profile = await user_service.get_profile(current_user)
    return APIResponse(
        success=True,
        data=profile,
        message="User profile retrieved successfully",
    )


@router.patch("/profile", response_model=APIResponse[UserProfileResponse])
async def update_my_profile(
    updates: UserProfileUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    updated = await user_service.update_profile(current_user, updates)
    return APIResponse(
        success=True,
        data=updated,
        message="User profile updated successfully",
    )
