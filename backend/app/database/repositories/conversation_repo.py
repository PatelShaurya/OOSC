import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database.repositories.base import BaseRepository
from app.utils.logger import logger


class ConversationRepository(BaseRepository):
    # In-memory storage for fallback/testing
    _conversations: Dict[str, Dict[str, Any]] = {}
    _messages: Dict[str, List[Dict[str, Any]]] = {}

    async def create_conversation(
        self,
        user_id: str,
        title: Optional[str] = None,
        category: Optional[str] = None,
        jurisdiction: Optional[str] = None,
    ) -> Dict[str, Any]:
        conv_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        final_title = title or "New Conversation"

        record = {
            "id": conv_id,
            "user_id": user_id,
            "title": final_title,
            "category": category,
            "jurisdiction": jurisdiction,
            "created_at": now,
            "updated_at": now,
        }

        if self.client:
            try:
                res = self.client.table("conversations").insert(record).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase create_conversation failed: {e}. Storing in-memory.")

        self._conversations[conv_id] = record
        self._messages[conv_id] = []
        return record

    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        if self.client:
            try:
                res = (
                    self.client.table("conversations")
                    .select("*")
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .maybe_single()
                    .execute()
                )
                if res and res.data:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase get_conversation failed: {e}")

        conv = self._conversations.get(conversation_id)
        if conv and conv.get("user_id") == user_id:
            return conv
        return None

    async def list_conversations(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if self.client:
            try:
                res = (
                    self.client.table("conversations")
                    .select("*")
                    .eq("user_id", user_id)
                    .order("updated_at", desc=True)
                    .range(offset, offset + limit - 1)
                    .execute()
                )
                if res and res.data is not None:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase list_conversations failed: {e}")

        user_convs = [c for c in self._conversations.values() if c.get("user_id") == user_id]
        user_convs.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return user_convs[offset : offset + limit]

    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        now = datetime.now(timezone.utc).isoformat()
        payload = {**updates, "updated_at": now}

        if self.client:
            try:
                res = (
                    self.client.table("conversations")
                    .update(payload)
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase update_conversation failed: {e}")

        conv = self._conversations.get(conversation_id)
        if conv and conv.get("user_id") == user_id:
            conv.update(payload)
            return conv
        return None

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        if self.client:
            try:
                self.client.table("messages").delete().eq("conversation_id", conversation_id).execute()
                res = (
                    self.client.table("conversations")
                    .delete()
                    .eq("id", conversation_id)
                    .eq("user_id", user_id)
                    .execute()
                )
                return bool(res and res.data)
            except Exception as e:
                logger.error(f"Supabase delete_conversation failed: {e}")

        conv = self._conversations.get(conversation_id)
        if conv and conv.get("user_id") == user_id:
            del self._conversations[conversation_id]
            self._messages.pop(conversation_id, None)
            return True
        return False

    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        citations: Optional[List[Dict[str, Any]]] = None,
        suggested_followups: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        record = {
            "id": msg_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "citations": citations or [],
            "suggested_followups": suggested_followups or [],
            "feedback": "none",
            "metadata": metadata or {},
            "created_at": now,
        }

        # Update conversation updated_at
        if conversation_id in self._conversations:
            self._conversations[conversation_id]["updated_at"] = now

        if self.client:
            try:
                res = self.client.table("messages").insert(record).execute()
                self.client.table("conversations").update({"updated_at": now}).eq("id", conversation_id).execute()
                if res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase add_message failed: {e}")

        if conversation_id not in self._messages:
            self._messages[conversation_id] = []
        self._messages[conversation_id].append(record)
        return record

    async def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        if self.client:
            try:
                res = (
                    self.client.table("messages")
                    .select("*")
                    .eq("conversation_id", conversation_id)
                    .order("created_at", desc=False)
                    .execute()
                )
                if res and res.data is not None:
                    return res.data
            except Exception as e:
                logger.error(f"Supabase get_messages failed: {e}")

        return self._messages.get(conversation_id, [])

    async def update_message_feedback(
        self,
        message_id: str,
        conversation_id: str,
        feedback: str,
        notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        payload = {"feedback": feedback}
        if notes:
            payload["feedback_notes"] = notes

        if self.client:
            try:
                res = (
                    self.client.table("messages")
                    .update(payload)
                    .eq("id", message_id)
                    .eq("conversation_id", conversation_id)
                    .execute()
                )
                if res and res.data:
                    return res.data[0]
            except Exception as e:
                logger.error(f"Supabase update_message_feedback failed: {e}")

        msgs = self._messages.get(conversation_id, [])
        for m in msgs:
            if m.get("id") == message_id:
                m.update(payload)
                return m
        return None
