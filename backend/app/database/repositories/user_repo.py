from datetime import datetime, timezone
from typing import Any, Dict, Optional
from app.database.repositories.base import BaseRepository
from app.utils.logger import logger


class UserRepository(BaseRepository):
    # In-memory storage fallback for local dev / tests
    _memory_store: Dict[str, Dict[str, Any]] = {}

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        if self.client:
            try:
                res = self.client.table("user_profiles").select("*").eq("id", user_id).maybe_single().execute()
                return res.data if res else None
            except Exception as e:
                logger.error(f"Error fetching user profile from Supabase: {e}")

        return self._memory_store.get(user_id)

    async def create_or_update_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        if self.client:
            try:
                payload = {**data, "id": user_id, "updated_at": now}
                res = self.client.table("user_profiles").upsert(payload).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Error upserting user profile in Supabase: {e}")

        existing = self._memory_store.get(user_id, {"id": user_id, "created_at": now})
        updated = {**existing, **data, "id": user_id, "updated_at": now}
        self._memory_store[user_id] = updated
        return updated
