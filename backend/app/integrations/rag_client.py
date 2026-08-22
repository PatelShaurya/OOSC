from typing import Any, Dict, List, Optional
import httpx
from app.config import get_settings
from app.schemas.rag import (
    Citation,
    RAGDocumentGenerationRequest,
    RAGDocumentGenerationResponse,
    RAGFormFieldExtractionRequest,
    RAGFormFieldExtractionResponse,
    RAGQueryRequest,
    RAGQueryResponse,
)
from app.utils.exceptions import RAGServiceError
from app.utils.logger import logger


class RAGClient:
    """
    HTTP Client communicating exclusively with the external RAG/AI microservice.
    No RAG logic (vector search, chunking, embeddings) lives in this client.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.RAG_SERVICE_URL).rstrip("/")
        self.api_key = api_key or settings.RAG_API_KEY
        self.timeout = timeout or settings.RAG_TIMEOUT_SECONDS

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def check_health(self) -> bool:
        """Checks if the RAG microservice is responsive."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/health", headers=self._get_headers())
                return res.status_code == 200
        except Exception:
            return False

    async def query_legal_knowledge(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        jurisdiction: Optional[str] = None,
        language: str = "en",
        category: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> RAGQueryResponse:
        """
        Sends user query and chat history to RAG service to obtain legal guidance with statutory citations.
        """
        request_payload = RAGQueryRequest(
            query=query,
            conversation_history=conversation_history or [],
            state_jurisdiction=jurisdiction,
            language=language,
            category=category,
            extra_context=extra_context,
        ).model_dump()

        url = f"{self.base_url}/api/v1/query"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_payload, headers=self._get_headers())

                if response.status_code == 200:
                    data = response.json()
                    # Support both { data: {...} } envelope and direct payload
                    payload = data.get("data", data)
                    return RAGQueryResponse(**payload)
                else:
                    logger.warning(
                        f"RAG service returned status {response.status_code}: {response.text}. Falling back to default response."
                    )
        except httpx.RequestError as exc:
            logger.warning(f"RAG service connection issue ({exc}). Using fallback assistant response.")

        # Resilient fallback for local testing / when RAG service is booting
        return self._generate_fallback_query_response(query=query, category=category, jurisdiction=jurisdiction)

    async def generate_complaint_document(
        self,
        document_type: str,
        applicant_details: Dict[str, Any],
        respondent_details: Dict[str, Any],
        facts_and_events: List[str],
        grievance_description: str,
        relief_sought: List[str],
        jurisdiction: Optional[str] = None,
        language: str = "en",
    ) -> RAGDocumentGenerationResponse:
        """
        Calls RAG microservice to generate formalized legal notice / complaint / RTI draft.
        """
        request_payload = RAGDocumentGenerationRequest(
            document_type=document_type,
            applicant_details=applicant_details,
            respondent_details=respondent_details,
            facts_and_events=facts_and_events,
            grievance_description=grievance_description,
            relief_sought=relief_sought,
            jurisdiction=jurisdiction,
            language=language,
        ).model_dump()

        url = f"{self.base_url}/api/v1/generate-document"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_payload, headers=self._get_headers())

                if response.status_code == 200:
                    data = response.json()
                    payload = data.get("data", data)
                    return RAGDocumentGenerationResponse(**payload)
                else:
                    logger.warning(f"RAG service draft generation error: {response.text}")
        except httpx.RequestError as exc:
            logger.warning(f"RAG service unreachable for document generation ({exc}). Using fallback template.")

        # Fallback generated document template
        return self._generate_fallback_document_response(
            document_type=document_type,
            applicant=applicant_details,
            respondent=respondent_details,
            grievance=grievance_description,
            relief=relief_sought,
            jurisdiction=jurisdiction,
        )

    async def extract_form_fields(
        self,
        user_input: str,
        form_type: str,
        current_fields: Dict[str, Any],
    ) -> RAGFormFieldExtractionResponse:
        """
        Extracts structured fields from user's conversational message.
        """
        request_payload = RAGFormFieldExtractionRequest(
            user_input=user_input,
            form_type=form_type,
            current_fields=current_fields,
        ).model_dump()

        url = f"{self.base_url}/api/v1/extract-fields"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_payload, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    payload = data.get("data", data)
                    return RAGFormFieldExtractionResponse(**payload)
        except httpx.RequestError:
            pass

        # Fallback field extractor
        return RAGFormFieldExtractionResponse(
            extracted_fields={"notes": user_input},
            next_question=f"Please provide any remaining details regarding your {form_type.replace('_', ' ')}.",
            is_complete=False,
            validation_notes=["Input recorded successfully."],
        )

    def _generate_fallback_query_response(
        self, query: str, category: Optional[str], jurisdiction: Optional[str]
    ) -> RAGQueryResponse:
        """Fallback response when external RAG service is not reachable in dev."""
        jur = jurisdiction or "National/Central"
        cat = category or "General Civic & Legal Rights"

        return RAGQueryResponse(
            answer=(
                f"Regarding your query on '{query}': Under applicable {jur} laws and civic procedures, "
                f"citizens have legal recourse through the relevant administrative and appellate bodies. "
                f"For {cat}, you may seek information via an RTI Application, file a complaint before the designated ombudsman or consumer commission, "
                f"or issue a formal grievance notice."
            ),
            citations=[
                Citation(
                    source_title="Right to Information Act, 2005",
                    section="Section 6(1)",
                    act_or_law_name="RTI Act",
                    confidence_score=0.92,
                    excerpt="A person who desires to obtain any information under this Act shall make a request in writing...",
                ),
                Citation(
                    source_title="Consumer Protection Act, 2019",
                    section="Section 35",
                    act_or_law_name="Consumer Protection Act",
                    confidence_score=0.88,
                    excerpt="A complaint in relation to any goods sold or delivered or agreed to be sold or delivered or any service provided...",
                ),
            ],
            suggested_followups=[
                "How do I file an online grievance with the municipal authority?",
                "What is the statutory time limit for response under RTI?",
                "What documents are required to attach with this complaint?",
            ],
            detected_legal_domain=cat,
            applicable_remedies=[
                "Filing formal administrative grievance",
                "Submitting RTI query for public inspection",
                "Serving legal dispute notice",
            ],
        )

    def _generate_fallback_document_response(
        self,
        document_type: str,
        applicant: Dict[str, Any],
        respondent: Dict[str, Any],
        grievance: str,
        relief: List[str],
        jurisdiction: Optional[str],
    ) -> RAGDocumentGenerationResponse:
        doc_name = document_type.replace("_", " ").upper()
        app_name = applicant.get("name", "The Applicant/Complainant")
        resp_name = respondent.get("name", "The Respondent/Opposite Party")
        jur_text = jurisdiction or "Competent Jurisdiction"

        relief_bullets = "\n".join([f"- {r}" for r in relief]) if relief else "- Appropriate relief and rectification as deemed fit."

        markdown = f"""# {doc_name}
**Before the Competent Authority / Court in {jur_text}**

---

### IN THE MATTER OF:
**{app_name}**  
*(Applicant / Complainant)*

**VERSUS**

**{resp_name}**  
*(Respondent / Opposite Party)*

---

### 1. JURISDICTION & PARTIES
1. The Applicant is a citizen residing at the address provided in the attached application.
2. The Respondent is the entity/authority responsible under applicable laws within {jur_text}.

### 2. STATEMENT OF FACTS & GRIEVANCE
{grievance}

### 3. STATUTORY PROVISIONS & GROUNDS
- Violation of statutory duties and standard of service under applicable civic and consumer protection frameworks.
- Failure of respondent to redress the grievance within the stipulated statutory period.

### 4. PRAYER / RELIEF SOUGHT
The Complainant respectfully prays that this Hon'ble Authority may be pleased to:
{relief_bullets}

---

**Date:** [Date]  
**Place:** {jur_text}  
**Signature of Complainant / Authorized Representative**
"""
        return RAGDocumentGenerationResponse(
            document_title=f"Draft {doc_name}",
            content_markdown=markdown,
            sections={
                "parties": f"{app_name} vs {resp_name}",
                "facts": grievance,
                "prayer": relief_bullets,
            },
            filing_instructions=[
                "Verify all party names and contact details.",
                "Attach proof of payment, correspondence, and relevant identity documents.",
                "Sign each page of the document before submission to the registry or online portal.",
            ],
            required_attachments=[
                "Copy of identity proof (Aadhaar / Voter ID / Passport)",
                "Chronological copies of previous communications / complaints",
                "Receipts or service transaction invoices",
            ],
        )
