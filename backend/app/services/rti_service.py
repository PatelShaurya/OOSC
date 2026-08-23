"""
Service handling RTI application drafting requests by orchestrating RAGClient integration.
"""
from typing import Optional

from app.integrations.rag_client import RAGClient
from app.schemas.auth import CurrentUser
from app.schemas.rti import RTIDraftRequest, RTIDraftResponse


class RTIDraftingService:
    """
    Orchestrates RTI application drafting using RAG service legal retrieval and grounded generation.
    """

    def __init__(self, rag_client: Optional[RAGClient] = None):
        self.rag = rag_client or RAGClient()

    async def generate_rti_draft(
        self,
        payload: RTIDraftRequest,
        user: Optional[CurrentUser] = None,
    ) -> RTIDraftResponse:
        """
        Processes plain-language citizen request into a structured RTI Application draft.
        """
        rag_response = await self.rag.draft_rti_application(
            request_text=payload.request,
            applicant_name=payload.applicant_name,
            applicant_address=payload.applicant_address,
            public_authority=payload.public_authority,
        )

        return RTIDraftResponse(
            draft=rag_response.answer,
            limitations=rag_response.limitations,
            citations=rag_response.citations,
        )
