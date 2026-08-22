from typing import Any, Dict, List, Optional
from app.database.repositories.conversation_repo import ConversationRepository
from app.integrations.rag_client import RAGClient
from app.schemas.auth import CurrentUser
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdate,
    FeedbackType,
    MessageCreate,
    MessageFeedbackRequest,
    MessageResponse,
    MessageRole,
)
from app.utils.exceptions import NotFoundError


class ConversationService:
    def __init__(
        self,
        conversation_repo: Optional[ConversationRepository] = None,
        rag_client: Optional[RAGClient] = None,
    ):
        self.repo = conversation_repo or ConversationRepository()
        self.rag = rag_client or RAGClient()

    async def create_conversation(
        self,
        user: CurrentUser,
        data: ConversationCreate,
    ) -> ConversationResponse:
        title = data.title
        if not title and data.initial_message:
            # Generate a brief title from initial message
            title = data.initial_message[:50].strip() + ("..." if len(data.initial_message) > 50 else "")

        conv_record = await self.repo.create_conversation(
            user_id=user.id,
            title=title or "New Legal Query",
            category=data.category,
            jurisdiction=data.jurisdiction,
        )

        if data.initial_message:
            await self.send_message(
                conversation_id=conv_record["id"],
                user=user,
                data=MessageCreate(
                    content=data.initial_message,
                    category=data.category,
                    jurisdiction=data.jurisdiction,
                ),
            )

        return await self.get_conversation(conv_record["id"], user)

    async def get_conversation(self, conversation_id: str, user: CurrentUser) -> ConversationResponse:
        conv = await self.repo.get_conversation(conversation_id, user.id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)

        messages = await self.repo.get_messages(conversation_id)
        return ConversationResponse(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv["title"],
            category=conv.get("category"),
            jurisdiction=conv.get("jurisdiction"),
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            message_count=len(messages),
        )

    async def get_conversation_detail(
        self,
        conversation_id: str,
        user: CurrentUser,
    ) -> ConversationDetailResponse:
        conv = await self.repo.get_conversation(conversation_id, user.id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)

        raw_messages = await self.repo.get_messages(conversation_id)
        messages = [
            MessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                role=MessageRole(m["role"]),
                content=m["content"],
                citations=m.get("citations", []),
                suggested_followups=m.get("suggested_followups", []),
                feedback=FeedbackType(m.get("feedback", "none")),
                metadata=m.get("metadata", {}),
                created_at=m["created_at"],
            )
            for m in raw_messages
        ]

        return ConversationDetailResponse(
            id=conv["id"],
            user_id=conv["user_id"],
            title=conv["title"],
            category=conv.get("category"),
            jurisdiction=conv.get("jurisdiction"),
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            message_count=len(messages),
            messages=messages,
        )

    async def list_conversations(
        self,
        user: CurrentUser,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ConversationResponse]:
        records = await self.repo.list_conversations(user.id, limit=limit, offset=offset)
        result = []
        for r in records:
            msgs = await self.repo.get_messages(r["id"])
            result.append(
                ConversationResponse(
                    id=r["id"],
                    user_id=r["user_id"],
                    title=r["title"],
                    category=r.get("category"),
                    jurisdiction=r.get("jurisdiction"),
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                    message_count=len(msgs),
                )
            )
        return result

    async def update_conversation(
        self,
        conversation_id: str,
        user: CurrentUser,
        data: ConversationUpdate,
    ) -> ConversationResponse:
        updates = data.model_dump(exclude_unset=True)
        updated = await self.repo.update_conversation(conversation_id, user.id, updates)
        if not updated:
            raise NotFoundError("Conversation", conversation_id)
        return await self.get_conversation(conversation_id, user)

    async def delete_conversation(self, conversation_id: str, user: CurrentUser) -> bool:
        success = await self.repo.delete_conversation(conversation_id, user.id)
        if not success:
            raise NotFoundError("Conversation", conversation_id)
        return True

    async def send_message(
        self,
        conversation_id: str,
        user: CurrentUser,
        data: MessageCreate,
    ) -> MessageResponse:
        # 1. Verify ownership
        conv = await self.repo.get_conversation(conversation_id, user.id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)

        # 2. Save user message
        user_msg = await self.repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=data.content,
        )

        # 3. Retrieve past messages for conversation context
        past_msgs = await self.repo.get_messages(conversation_id)
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in past_msgs[:-1]  # Exclude current message
        ]

        # 4. Call isolated RAG client
        jurisdiction = data.jurisdiction or conv.get("jurisdiction")
        category = data.category or conv.get("category")
        language = data.language or "en"

        rag_result = await self.rag.query_legal_knowledge(
            query=data.content,
            conversation_history=history,
            jurisdiction=jurisdiction,
            language=language,
            category=category,
        )

        # 5. Save assistant message with citations and suggested followups
        assistant_msg = await self.repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=rag_result.answer,
            citations=[c.model_dump() for c in rag_result.citations],
            suggested_followups=rag_result.suggested_followups,
            metadata={
                "detected_legal_domain": rag_result.detected_legal_domain,
                "applicable_remedies": rag_result.applicable_remedies,
            },
        )

        # Update conversation title if still default
        if conv["title"] in ["New Conversation", "New Legal Query"]:
            auto_title = data.content[:50].strip() + ("..." if len(data.content) > 50 else "")
            await self.repo.update_conversation(conversation_id, user.id, {"title": auto_title})

        return MessageResponse(
            id=assistant_msg["id"],
            conversation_id=assistant_msg["conversation_id"],
            role=MessageRole(assistant_msg["role"]),
            content=assistant_msg["content"],
            citations=[c.model_dump() for c in rag_result.citations],
            suggested_followups=rag_result.suggested_followups,
            feedback=FeedbackType.NONE,
            metadata=assistant_msg.get("metadata", {}),
            created_at=assistant_msg["created_at"],
        )

    async def submit_feedback(
        self,
        conversation_id: str,
        message_id: str,
        user: CurrentUser,
        data: MessageFeedbackRequest,
    ) -> Dict[str, Any]:
        conv = await self.repo.get_conversation(conversation_id, user.id)
        if not conv:
            raise NotFoundError("Conversation", conversation_id)

        updated = await self.repo.update_message_feedback(
            message_id=message_id,
            conversation_id=conversation_id,
            feedback=data.feedback.value,
            notes=data.feedback_notes,
        )
        if not updated:
            raise NotFoundError("Message", message_id)
        return updated
