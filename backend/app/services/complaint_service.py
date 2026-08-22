from typing import Any, Dict, List, Optional
from app.database.repositories.complaint_repo import ComplaintRepository
from app.integrations.rag_client import RAGClient
from app.schemas.auth import CurrentUser
from app.schemas.complaint import (
    ComplaintCategory,
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatus,
    ComplaintUpdate,
    DocumentDraftResponse,
    ExportDocumentResponse,
    GenerateDocumentRequest,
)
from app.utils.exceptions import NotFoundError, ValidationError


class ComplaintService:
    def __init__(
        self,
        complaint_repo: Optional[ComplaintRepository] = None,
        rag_client: Optional[RAGClient] = None,
    ):
        self.repo = complaint_repo or ComplaintRepository()
        self.rag = rag_client or RAGClient()

    async def create_complaint(
        self,
        user: CurrentUser,
        data: ComplaintCreate,
    ) -> ComplaintResponse:
        record = await self.repo.create_complaint(
            user_id=user.id,
            complaint_data=data.model_dump(),
        )
        return self._to_response(record)

    async def get_complaint(self, complaint_id: str, user: CurrentUser) -> ComplaintResponse:
        record = await self.repo.get_complaint(complaint_id, user.id)
        if not record:
            raise NotFoundError("Complaint", complaint_id)
        return self._to_response(record)

    async def list_complaints(
        self,
        user: CurrentUser,
        category: Optional[ComplaintCategory] = None,
        status: Optional[ComplaintStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[ComplaintResponse]:
        cat_val = category.value if category else None
        stat_val = status.value if status else None
        records = await self.repo.list_complaints(
            user_id=user.id,
            category=cat_val,
            status=stat_val,
            limit=limit,
            offset=offset,
        )
        return [self._to_response(r) for r in records]

    async def update_complaint(
        self,
        complaint_id: str,
        user: CurrentUser,
        data: ComplaintUpdate,
    ) -> ComplaintResponse:
        updates = data.model_dump(exclude_unset=True)
        if "category" in updates and updates["category"] is not None:
            updates["category"] = updates["category"].value
        if "status" in updates and updates["status"] is not None:
            updates["status"] = updates["status"].value

        updated = await self.repo.update_complaint(complaint_id, user.id, updates)
        if not updated:
            raise NotFoundError("Complaint", complaint_id)
        return self._to_response(updated)

    async def delete_complaint(self, complaint_id: str, user: CurrentUser) -> bool:
        success = await self.repo.delete_complaint(complaint_id, user.id)
        if not success:
            raise NotFoundError("Complaint", complaint_id)
        return True

    async def generate_document(
        self,
        complaint_id: str,
        user: CurrentUser,
        data: GenerateDocumentRequest,
    ) -> DocumentDraftResponse:
        comp = await self.repo.get_complaint(complaint_id, user.id)
        if not comp:
            raise NotFoundError("Complaint", complaint_id)

        # Call isolated RAG client for legal document synthesis
        rag_doc = await self.rag.generate_complaint_document(
            document_type=comp["category"],
            applicant_details=comp.get("applicant_details", {"name": "Applicant"}),
            respondent_details=comp.get("respondent_details", {"name": comp.get("authority_or_opponent_name", "Opposite Party")}),
            facts_and_events=[comp["facts_description"]],
            grievance_description=comp["facts_description"],
            relief_sought=comp.get("relief_sought", []),
            jurisdiction=comp.get("jurisdiction"),
            language=data.language,
        )

        # Update complaint record with generated draft and status
        await self.repo.update_complaint(
            complaint_id=complaint_id,
            user_id=user.id,
            updates={
                "status": "generated",
                "generated_document": rag_doc.content_markdown,
                "filing_instructions": rag_doc.filing_instructions,
                "required_attachments": rag_doc.required_attachments,
            },
        )

        return DocumentDraftResponse(
            complaint_id=complaint_id,
            document_title=rag_doc.document_title,
            content_markdown=rag_doc.content_markdown,
            filing_instructions=rag_doc.filing_instructions,
            required_attachments=rag_doc.required_attachments,
            sections=rag_doc.sections,
        )

    async def export_document(
        self,
        complaint_id: str,
        user: CurrentUser,
        file_format: str = "markdown",
    ) -> ExportDocumentResponse:
        comp = await self.repo.get_complaint(complaint_id, user.id)
        if not comp:
            raise NotFoundError("Complaint", complaint_id)

        doc_content = comp.get("generated_document")
        if not doc_content:
            # If not yet generated, auto-generate first
            draft = await self.generate_document(complaint_id, user, GenerateDocumentRequest())
            doc_content = draft.content_markdown

        title = comp.get("title", "civic_complaint_draft").replace(" ", "_").lower()
        ext = "md" if file_format == "markdown" else "txt"
        filename = f"{title}_{complaint_id[:8]}.{ext}"

        return ExportDocumentResponse(
            complaint_id=complaint_id,
            document_title=comp.get("title", "Legal Complaint Draft"),
            format=file_format,
            content=doc_content,
            filename=filename,
        )

    def _to_response(self, r: Dict[str, Any]) -> ComplaintResponse:
        return ComplaintResponse(
            id=r["id"],
            user_id=r["user_id"],
            title=r["title"],
            category=ComplaintCategory(r["category"]),
            status=ComplaintStatus(r["status"]),
            jurisdiction=r.get("jurisdiction"),
            authority_or_opponent_name=r.get("authority_or_opponent_name"),
            incident_date=r.get("incident_date"),
            facts_description=r["facts_description"],
            relief_sought=r.get("relief_sought", []),
            applicant_details=r.get("applicant_details", {}),
            respondent_details=r.get("respondent_details", {}),
            generated_document=r.get("generated_document"),
            filing_instructions=r.get("filing_instructions", []),
            required_attachments=r.get("required_attachments", []),
            metadata=r.get("metadata", {}),
            created_at=r["created_at"],
            updated_at=r["updated_at"],
        )
