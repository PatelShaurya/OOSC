from fastapi import Depends
from app.auth.dependencies import get_current_user, get_optional_user
from app.database.repositories.complaint_repo import ComplaintRepository
from app.database.repositories.conversation_repo import ConversationRepository
from app.database.repositories.form_session_repo import FormSessionRepository
from app.database.repositories.user_repo import UserRepository
from app.integrations.rag_client import RAGClient
from app.schemas.auth import CurrentUser
from app.services.complaint_service import ComplaintService
from app.services.conversation_service import ConversationService
from app.services.form_service import FormService
from app.services.user_service import UserService


def get_user_service() -> UserService:
    return UserService(user_repo=UserRepository())


def get_rag_client() -> RAGClient:
    return RAGClient()


def get_conversation_service(
    rag_client: RAGClient = Depends(get_rag_client),
) -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(),
        rag_client=rag_client,
    )


def get_form_service(
    rag_client: RAGClient = Depends(get_rag_client),
) -> FormService:
    return FormService(
        session_repo=FormSessionRepository(),
        complaint_repo=ComplaintRepository(),
        rag_client=rag_client,
    )


def get_complaint_service(
    rag_client: RAGClient = Depends(get_rag_client),
) -> ComplaintService:
    return ComplaintService(
        complaint_repo=ComplaintRepository(),
        rag_client=rag_client,
    )
