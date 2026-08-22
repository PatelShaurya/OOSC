from typing import Any, Dict, List, Optional
from app.database.repositories.complaint_repo import ComplaintRepository
from app.database.repositories.form_session_repo import FormSessionRepository
from app.integrations.rag_client import RAGClient
from app.schemas.auth import CurrentUser
from app.schemas.form_session import (
    FormCompleteResponse,
    FormSessionCreate,
    FormSessionResponse,
    FormSessionStatus,
    FormStepGuidance,
    FormStepSubmit,
    FormType,
)
from app.utils.exceptions import NotFoundError, ValidationError

FORM_STEP_DEFINITIONS: Dict[FormType, List[Dict[str, Any]]] = {
    FormType.RTI_APPLICATION: [
        {
            "step_number": 1,
            "step_title": "Public Authority Details",
            "prompt_question": "Which public department, ministry, or municipal body holds the information you need?",
            "required_fields": ["public_authority_name", "department", "jurisdiction_state"],
            "suggested_inputs": ["Municipal Corporation", "Department of Revenue", "State Police Department"],
            "legal_tips": ["Under Sec 6(1) of the RTI Act 2005, specify the Central/State Public Information Officer (CPIO/SPIO)."],
        },
        {
            "step_number": 2,
            "step_title": "Information Requested & Period",
            "prompt_question": "What specific documents, records, or file inspection are you requesting? Specify the relevant date range.",
            "required_fields": ["information_description", "time_period_covered"],
            "suggested_inputs": ["Certified copies of sanction order", "Status of grievance letter dated...", "Measurement book records"],
            "legal_tips": ["Keep questions clear, precise, and objective. Avoid seeking personal opinions or justifications."],
        },
        {
            "step_number": 3,
            "step_title": "Applicant Details & Mode of Delivery",
            "prompt_question": "Please provide your contact name, residential address, and preferred delivery mode (Speed Post or Email).",
            "required_fields": ["applicant_name", "applicant_address", "applicant_email", "delivery_mode"],
            "suggested_inputs": ["Speed Post (Certified Copy)", "Electronic Delivery (PDF Email)"],
            "legal_tips": ["Sec 6(2) provides that an applicant shall not be required to give any reason for requesting the information."],
        },
        {
            "step_number": 4,
            "step_title": "Review & Fee Confirmation",
            "prompt_question": "Please review all details. Confirm if you belong to the Below Poverty Line (BPL) category for fee exemption.",
            "required_fields": ["is_bpl_exempt", "fee_payment_mode"],
            "suggested_inputs": ["General Category (Rs. 10 Application Fee via IPO / Court Fee Stamp / Online Portal)", "BPL Card Holder (Fee Exempt)"],
            "legal_tips": ["BPL card holders are exempt from RTI application fees under RTI Rule 5."],
        },
    ],
    FormType.CONSUMER_COMPLAINT: [
        {
            "step_number": 1,
            "step_title": "Opposite Party (Seller / Service Provider)",
            "prompt_question": "Provide the name, branch, and contact address of the company or merchant.",
            "required_fields": ["seller_name", "product_or_service_name", "purchase_date", "invoice_number"],
            "suggested_inputs": ["E-commerce platform", "Telecom service provider", "Electronics manufacturer"],
            "legal_tips": ["Under Consumer Protection Act 2019, e-commerce entities are directly liable for unfair trade practices."],
        },
        {
            "step_number": 2,
            "step_title": "Defect / Deficiency Description",
            "prompt_question": "Describe what defect was found in the goods or what deficiency occurred in the services provided.",
            "required_fields": ["defect_description", "communication_summary"],
            "suggested_inputs": ["Defective item delivered and refund denied", "Unexplained service cancellation"],
            "legal_tips": ["Maintain copies of invoice, warranty card, customer care ticket numbers, and email exchanges."],
        },
        {
            "step_number": 3,
            "step_title": "Relief & Compensation Claimed",
            "prompt_question": "What relief do you seek? (e.g. Full refund, replacement, damages for mental harassment, litigation costs).",
            "required_fields": ["refund_amount", "compensation_claimed", "relief_summary"],
            "suggested_inputs": ["Full refund of Rs. X with 18% interest", "Compensation for mental agony Rs. Y", "Litigation expenses Rs. Z"],
            "legal_tips": ["District Consumer Commissions entertain claims up to Rs. 50 Lakhs under the revised pecuniary jurisdiction."],
        },
    ],
    FormType.MUNICIPAL_GRIEVANCE: [
        {
            "step_number": 1,
            "step_title": "Location & Hazard Details",
            "prompt_question": "Where is the civic issue located (Ward, Street, Landmark) and what type of civic hazard is it?",
            "required_fields": ["ward_or_zone", "street_landmark", "issue_type"],
            "suggested_inputs": ["Potholes / Broken road", "Garbage overflow", "Defective streetlights", "Water supply contamination"],
            "legal_tips": ["Civic authorities are bound by municipal charter service timelines."],
        },
        {
            "step_number": 2,
            "step_title": "Duration & Risk Assessment",
            "prompt_question": "How long has this issue persisted and what risk does it pose to public health/safety?",
            "required_fields": ["duration_days", "safety_hazard_description"],
            "suggested_inputs": ["Persisting for over 2 weeks", "Causing traffic hazards and accident risk"],
            "legal_tips": ["Photos and prior complaint reference numbers increase escalation speed."],
        },
        {
            "step_number": 3,
            "step_title": "Complainant Details & Verification",
            "prompt_question": "Please provide your contact details for civic field verification.",
            "required_fields": ["complainant_name", "phone_number", "address"],
            "suggested_inputs": ["Resident of ward area"],
            "legal_tips": ["Field inspectors may contact you to verify completion."],
        },
    ],
}


class FormService:
    def __init__(
        self,
        session_repo: Optional[FormSessionRepository] = None,
        complaint_repo: Optional[ComplaintRepository] = None,
        rag_client: Optional[RAGClient] = None,
    ):
        self.repo = session_repo or FormSessionRepository()
        self.complaint_repo = complaint_repo or ComplaintRepository()
        self.rag = rag_client or RAGClient()

    def _get_step_guidance(self, form_type: FormType, step_number: int) -> Optional[FormStepGuidance]:
        steps = FORM_STEP_DEFINITIONS.get(form_type, [])
        for s in steps:
            if s["step_number"] == step_number:
                return FormStepGuidance(**s)
        return None

    def _get_total_steps(self, form_type: FormType) -> int:
        return len(FORM_STEP_DEFINITIONS.get(form_type, [1, 2, 3]))

    async def create_session(
        self,
        user: CurrentUser,
        data: FormSessionCreate,
    ) -> FormSessionResponse:
        total_steps = self._get_total_steps(data.form_type)
        initial_data = {}

        if data.initial_input:
            extraction = await self.rag.extract_form_fields(
                user_input=data.initial_input,
                form_type=data.form_type.value,
                current_fields={},
            )
            initial_data.update(extraction.extracted_fields)

        record = await self.repo.create_form_session(
            user_id=user.id,
            form_type=data.form_type.value,
            title=data.title,
            jurisdiction=data.jurisdiction,
            initial_data=initial_data,
            total_steps=total_steps,
        )

        guidance = self._get_step_guidance(data.form_type, 1)

        return FormSessionResponse(
            id=record["id"],
            user_id=record["user_id"],
            form_type=FormType(record["form_type"]),
            title=record["title"],
            status=FormSessionStatus(record["status"]),
            current_step=record["current_step"],
            total_steps=record["total_steps"],
            collected_data=record["collected_data"],
            missing_fields=record.get("missing_fields", []),
            next_step_guidance=guidance,
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    async def get_session(self, session_id: str, user: CurrentUser) -> FormSessionResponse:
        record = await self.repo.get_form_session(session_id, user.id)
        if not record:
            raise NotFoundError("FormSession", session_id)

        form_type = FormType(record["form_type"])
        guidance = self._get_step_guidance(form_type, record["current_step"])

        return FormSessionResponse(
            id=record["id"],
            user_id=record["user_id"],
            form_type=form_type,
            title=record["title"],
            status=FormSessionStatus(record["status"]),
            current_step=record["current_step"],
            total_steps=record["total_steps"],
            collected_data=record["collected_data"],
            missing_fields=record.get("missing_fields", []),
            next_step_guidance=guidance,
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    async def list_sessions(
        self,
        user: CurrentUser,
        status: Optional[FormSessionStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[FormSessionResponse]:
        status_val = status.value if status else None
        records = await self.repo.list_form_sessions(user.id, status=status_val, limit=limit, offset=offset)

        result = []
        for r in records:
            form_type = FormType(r["form_type"])
            guidance = self._get_step_guidance(form_type, r["current_step"])
            result.append(
                FormSessionResponse(
                    id=r["id"],
                    user_id=r["user_id"],
                    form_type=form_type,
                    title=r["title"],
                    status=FormSessionStatus(r["status"]),
                    current_step=r["current_step"],
                    total_steps=r["total_steps"],
                    collected_data=r["collected_data"],
                    missing_fields=r.get("missing_fields", []),
                    next_step_guidance=guidance,
                    created_at=r["created_at"],
                    updated_at=r["updated_at"],
                )
            )
        return result

    async def submit_step(
        self,
        session_id: str,
        user: CurrentUser,
        data: FormStepSubmit,
    ) -> FormSessionResponse:
        session = await self.repo.get_form_session(session_id, user.id)
        if not session:
            raise NotFoundError("FormSession", session_id)

        form_type = FormType(session["form_type"])
        collected_data = dict(session.get("collected_data", {}))

        # Update with explicit field updates
        collected_data.update(data.field_updates)

        # If natural language response provided, extract fields via RAG
        if data.user_response:
            extraction = await self.rag.extract_form_fields(
                user_input=data.user_response,
                form_type=session["form_type"],
                current_fields=collected_data,
            )
            collected_data.update(extraction.extracted_fields)

        # Advance step
        current_step = session["current_step"]
        total_steps = session["total_steps"]

        next_step = min(current_step + 1, total_steps)
        new_status = "completed" if current_step >= total_steps else "in_progress"

        updates = {
            "collected_data": collected_data,
            "current_step": next_step,
            "status": new_status,
        }

        updated = await self.repo.update_form_session(session_id, user.id, updates)
        guidance = self._get_step_guidance(form_type, next_step) if new_status != "completed" else None

        return FormSessionResponse(
            id=updated["id"],
            user_id=updated["user_id"],
            form_type=form_type,
            title=updated["title"],
            status=FormSessionStatus(updated["status"]),
            current_step=updated["current_step"],
            total_steps=updated["total_steps"],
            collected_data=updated["collected_data"],
            missing_fields=[],
            next_step_guidance=guidance,
            created_at=updated["created_at"],
            updated_at=updated["updated_at"],
        )

    async def complete_session(
        self,
        session_id: str,
        user: CurrentUser,
    ) -> FormCompleteResponse:
        session = await self.repo.get_form_session(session_id, user.id)
        if not session:
            raise NotFoundError("FormSession", session_id)

        await self.repo.update_form_session(session_id, user.id, {"status": "completed"})

        collected = session.get("collected_data", {})
        form_type = FormType(session["form_type"])

        # Auto-create complaint / draft record from collected form session
        complaint_record = await self.complaint_repo.create_complaint(
            user_id=user.id,
            complaint_data={
                "title": session.get("title", f"{form_type.value.title()} Filing Draft"),
                "category": form_type.value,
                "jurisdiction": session.get("jurisdiction") or collected.get("jurisdiction_state"),
                "authority_or_opponent_name": collected.get("public_authority_name") or collected.get("seller_name"),
                "facts_description": str(collected.get("information_description") or collected.get("defect_description") or collected),
                "applicant_details": {
                    "name": collected.get("applicant_name") or collected.get("complainant_name"),
                    "address": collected.get("applicant_address") or collected.get("address"),
                    "email": collected.get("applicant_email"),
                },
                "respondent_details": {
                    "name": collected.get("public_authority_name") or collected.get("seller_name"),
                },
                "relief_sought": [collected.get("relief_summary")] if collected.get("relief_summary") else [],
                "metadata": {"source_form_session_id": session_id},
            },
        )

        return FormCompleteResponse(
            session_id=session_id,
            form_type=form_type,
            status=FormSessionStatus.COMPLETED,
            collected_data=collected,
            ready_for_drafting=True,
            complaint_id=complaint_record["id"],
        )
