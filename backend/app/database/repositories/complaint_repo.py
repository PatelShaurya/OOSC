import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database.repositories.base import BaseRepository
from app.utils.logger import logger


class ComplaintRepository(BaseRepository):
    _complaints: Dict[str, Dict[str, Any]] = {}

    async def create_complaint(
        self,
        user_id: str,
        complaint_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        comp_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "id": comp_id,
            "user_id": user_id,
            "title": complaint_data.get("title", "Untitled Complaint"),
            "category": complaint_data.get("category", "other"),
            "status": complaint_data.get("status", "draft"),
            "jurisdiction": complaint_data.get("jurisdiction"),
            "authority_or_opponent_name": complaint_data.get("authority_or_opponent_name"),
            "incident_date": complaint_data.get("incident_date"),
            "facts_description": complaint_data.get("facts_description", ""),
            "relief_sought": complaint_data.get("relief_sought", []),
            "applicant_details": complaint_data.get("applicant_details", {}),
            "respondent_details": complaint_data.get("respondent_details", {}),
            "generated_document": complaint_data.get("generated_document"),
            "filing_instructions": complaint_data.get("filing_instructions", []),
            "required_attachments": complaint_data.get("required_attachments", []),
            "metadata": complaint_data.get("metadata", {}),
            "created_at": now,
            "updated_at": now,
        }

        if self.client:
            try:
                res = self.client.table("complaints").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase create_complaint failed: {e}")

        self._complaints[comp_id] = record
        return record

    async def get_complaint(self, complaint_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.client:
            try:
                res = (
                    self.client.table("complaints")
                    .select("*")
                    .eq("id", complaint_id)
                    .eq("user_id", user_id)
                    .maybe_single()
                    .execute()
                )
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase get_complaint failed: {e}")

        comp = self._complaints.get(complaint_id)
        if comp and comp.get("user_id") == user_id:
            return comp
        return None

    async def list_complaints(
        self,
        user_id: str,
        category: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if self.client:
            try:
                query = self.client.table("complaints").select("*").eq("user_id", user_id)
                if category:
                    query = query.eq("category", category)
                if status:
                    query = query.eq("status", status)
                res = query.order("updated_at", desc=True).range(offset, offset + limit - 1).execute()
                if res and res.data is not None:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase list_complaints failed: {e}")

        user_comps = [c for c in self._complaints.values() if c.get("user_id") == user_id]
        if category:
            user_comps = [c for c in user_comps if c.get("category") == category]
        if status:
            user_comps = [c for c in user_comps if c.get("status") == status]
        user_comps.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return user_comps[offset : offset + limit]

    async def update_complaint(
        self,
        complaint_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {**updates, "updated_at": now}

        if self.client:
            try:
                res = (
                    self.client.table("complaints")
                    .update(payload)
                    .eq("id", complaint_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase update_complaint failed: {e}")

        comp = self._complaints.get(complaint_id)
        if comp and comp.get("user_id") == user_id:
            comp.update(payload)
            return comp
        return None

    async def delete_complaint(self, complaint_id: str, user_id: str) -> bool:
        if self.client:
            try:
                res = (
                    self.client.table("complaints")
                    .delete()
                    .eq("id", complaint_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return bool(res and res.data)
            except Exception as e:
                logger.error(f"Supabase delete_complaint failed: {e}")

        comp = self._complaints.get(complaint_id)
        if comp and comp.get("user_id") == user_id:
            del self._complaints[complaint_id]
            return True
        return False
