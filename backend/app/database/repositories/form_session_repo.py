import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database.repositories.base import BaseRepository
from app.utils.logger import logger


class FormSessionRepository(BaseRepository):
    _sessions: Dict[str, Dict[str, Any]] = {}

    async def create_form_session(
        self,
        user_id: str,
        form_type: str,
        title: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None,
        total_steps: int = 4,
    ) -> Dict[str, Any]:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        final_title = title or f"{form_type.replace('_', ' ').title()} Session"

        record = {
            "id": session_id,
            "user_id": user_id,
            "form_type": form_type,
            "title": final_title,
            "status": "in_progress",
            "current_step": 1,
            "total_steps": total_steps,
            "collected_data": initial_data or {},
            "missing_fields": [],
            "jurisdiction": jurisdiction,
            "created_at": now,
            "updated_at": now,
        }

        if self.client:
            try:
                res = self.client.table("form_sessions").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase create_form_session failed: {e}")

        self._sessions[session_id] = record
        return record

    async def get_form_session(self, session_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.client:
            try:
                res = (
                    self.client.table("form_sessions")
                    .select("*")
                    .eq("id", session_id)
                    .eq("user_id", user_id)
                    .maybe_single()
                    .execute()
                )
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase get_form_session failed: {e}")

        session = self._sessions.get(session_id)
        if session and session.get("user_id") == user_id:
            return session
        return None

    async def list_form_sessions(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if self.client:
            try:
                query = self.client.table("form_sessions").select("*").eq("user_id", user_id)
                if status:
                    query = query.eq("status", status)
                res = query.order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
                if res and res.data is not None:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase list_form_sessions failed: {e}")

        user_sessions = [s for s in self._sessions.values() if s.get("user_id") == user_id]
        if status:
            user_sessions = [s for s in user_sessions if s.get("status") == status]
        user_sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return user_sessions[offset : offset + limit]

    async def update_form_session(
        self,
        session_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {**updates, "updated_at": now}

        if self.client:
            try:
                res = (
                    self.client.table("form_sessions")
                    .update(payload)
                    .eq("id", session_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase update_form_session failed: {e}")

        session = self._sessions.get(session_id)
        if session and session.get("user_id") == user_id:
            session.update(payload)
            return session
        return None

    async def delete_form_session(self, session_id: str, user_id: str) -> bool:
        if self.client:
            try:
                res = (
                    self.client.table("form_sessions")
                    .delete()
                    .eq("id", session_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return bool(res and res.data)
            except Exception as e:
                logger.error(f"Supabase delete_form_session failed: {e}")

        session = self._sessions.get(session_id)
        if session and session.get("user_id") == user_id:
            del self._sessions[session_id]
            return True
        return False
