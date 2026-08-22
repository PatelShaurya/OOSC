from typing import Any, Dict, Optional
from app.database.repositories.user_repo import UserRepository
from app.schemas.auth import CurrentUser, UserProfileResponse, UserProfileUpdate
from app.utils.exceptions import NotFoundError


class UserService:
    def __init__(self, user_repo: Optional[UserRepository] = None):
        self.user_repo = user_repo or UserRepository()

    async def get_profile(self, user: CurrentUser) -> UserProfileResponse:
        profile = await self.user_repo.get_profile(user.id)
        if not profile:
            # Create default profile if not exists
            profile = await self.user_repo.create_or_update_profile(
                user.id,
                {"email": user.email, "preferred_language": "en"},
            )
        return UserProfileResponse(**profile)

    async def update_profile(self, user: CurrentUser, updates: UserProfileUpdate) -> UserProfileResponse:
        data = updates.model_dump(exclude_unset=True)
        if user.email and "email" not in data:
            data["email"] = user.email

        updated = await self.user_repo.create_or_update_profile(user.id, data)
        return UserProfileResponse(**updated)
