from typing import Any, Dict, List, Optional
import httpx
from pydantic import ValidationError

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
    No RAG logic (vector search, chunking, embeddings, generation) lives in this client.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        raise_on_error: bool = False,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.RAG_SERVICE_URL).rstrip("/")
        self.api_key = api_key or settings.RAG_API_KEY
        self.timeout = timeout or settings.RAG_TIMEOUT_SECONDS
        self.raise_on_error = raise_on_error

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

    async def query(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 10,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None,
    ) -> RAGQueryResponse:
        """
        Sends natural-language query to the external RAG microservice REST endpoint POST /api/v1/query.
        """
        request_model = RAGQueryRequest(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
            document_id=document_id,
            document_type=document_type,
            issuing_authority=issuing_authority,
        )

        url = f"{self.base_url}/api/v1/query"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_model.model_dump(), headers=self._get_headers())

                if response.status_code == 200:
                    try:
                        data = response.json()
                        payload = data.get("data", data)
                        parsed = RAGQueryResponse(**payload)
                        if not parsed.answer or not parsed.answer.strip():
                            logger.warning("RAG service returned empty answer string.")
                        return parsed
                    except (ValueError, ValidationError) as exc:
                        logger.error(f"Failed to parse RAG service response payload: {exc}")
                        if self.raise_on_error:
                            raise RAGServiceError(
                                message="Invalid response format received from RAG service",
                                details={"error": str(exc)},
                            )
                else:
                    msg = f"RAG service returned HTTP {response.status_code}: {response.text}"
                    logger.warning(msg)
                    if self.raise_on_error:
                        raise RAGServiceError(
                            message=f"RAG service returned error status {response.status_code}",
                            details={"status_code": response.status_code, "response": response.text},
                        )

        except httpx.TimeoutException as exc:
            msg = f"RAG service request timed out after {self.timeout}s"
            logger.error(msg)
            if self.raise_on_error:
                raise RAGServiceError(message=msg, details={"timeout": self.timeout})

        except httpx.RequestError as exc:
            msg = f"RAG service connection issue: {exc}"
            logger.error(msg)
            if self.raise_on_error:
                raise RAGServiceError(message="Failed to connect to RAG service", details={"error": str(exc)})

        return self._generate_fallback_query_response(query=query, category=document_type, jurisdiction=issuing_authority)

    async def query_legal_knowledge(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        jurisdiction: Optional[str] = None,
        language: str = "en",
        category: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        candidate_k: int = 10,
    ) -> RAGQueryResponse:
        """
        Adapter method maintaining backward compatibility with ConversationService.
        Forwards query parameters to query().
        """
        return await self.query(
            query=query,
            top_k=top_k,
            candidate_k=candidate_k,
            document_type=category,
            issuing_authority=jurisdiction,
        )

    async def draft_rti_application(
        self,
        request_text: str,
        applicant_name: Optional[str] = None,
        applicant_address: Optional[str] = None,
        public_authority: Optional[str] = None,
    ) -> RAGQueryResponse:
        """
        Sends plain-language RTI request to RAG microservice for structured RTI drafting.
        """
        request_model = RAGQueryRequest(
            query=request_text,
            top_k=5,
            candidate_k=10,
            document_type="law",
            mode="rti_draft",
            applicant_name=applicant_name,
            applicant_address=applicant_address,
            public_authority=public_authority,
        )

        url = f"{self.base_url}/api/v1/query"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=request_model.model_dump(), headers=self._get_headers())

                if response.status_code == 200:
                    data = response.json()
                    payload = data.get("data", data)
                    parsed = RAGQueryResponse(**payload)
                    if parsed.answer and parsed.answer.strip():
                        return parsed
        except Exception as exc:
            logger.warning(f"RAG service error during RTI drafting: {exc}")
            if self.raise_on_error:
                raise RAGServiceError(message="Failed to generate RTI draft from RAG service", details={"error": str(exc)})

        # Fallback offline RTI draft generator
        auth_val = public_authority or "[Public Authority]"
        name_val = applicant_name or "[Applicant Name]"
        addr_val = applicant_address or "[Applicant Address]"

        fallback_draft = f"""RTI APPLICATION

To:
[Public Information Officer]
{auth_val}

Subject: Request for Information under the Right to Information Act, 2005 regarding {request_text}

Respected Sir/Madam,

Under Section 6(1) of the Right to Information Act, 2005, I seek the following information:

1. Certified details and documents regarding: {request_text}
2. Complete copies of sanction orders, expenditure statements, and project completion reports.

Kindly provide the requested information within the statutory period of 30 days as prescribed under Section 7(1) of the RTI Act, 2005.

Applicant Details:
Name: {name_val}
Address: {addr_val}
Contact: [Contact Information]

Date: [Date]
Place: [Place]"""

        return RAGQueryResponse(
            query=request_text,
            answer=fallback_draft,
            limitations="RAG microservice unreachable. Fallback RTI template generated.",
            citations=[
                Citation(
                    source_id="rti_act_2005_section_6_38",
                    document_id="rti_act_2005",
                    document_title="Right to Information Act, 2005",
                    document_type="law",
                    issuing_authority="Government of India",
                    section="Section 6(1)",
                    page_start=10,
                    page_end=11,
                    source_url="https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
                )
            ]
        )

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
                    if self.raise_on_error:
                        raise RAGServiceError(
                            message=f"Document generation returned status {response.status_code}",
                            details={"response": response.text},
                        )
        except httpx.TimeoutException:
            if self.raise_on_error:
                raise RAGServiceError(message="Document generation timed out")
        except httpx.RequestError as exc:
            logger.warning(f"RAG service unreachable for document generation ({exc}).")
            if self.raise_on_error:
                raise RAGServiceError(message="Failed to connect to RAG service for document generation")

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
            query=query,
            answer=(
                f"Regarding your query on '{query}': Under applicable {jur} laws and civic procedures, "
                f"citizens have legal recourse through the relevant administrative and appellate bodies. "
                f"For {cat}, you may seek information via an RTI Application, file a complaint before the designated ombudsman or consumer commission, "
                f"or issue a formal grievance notice."
            ),
            limitations="RAG service operating in offline fallback mode.",
            citations=[
                Citation(
                    source_id="rti_act_2005_section_6_38",
                    document_id="rti_act_2005",
                    document_title="Right to Information Act, 2005",
                    document_type="law",
                    issuing_authority="Government of India",
                    section="Section 6(1)",
                    page_start=10,
                    page_end=11,
                    source_url="https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
                ),
                Citation(
                    source_id="consumer_protection_act_2019_section_35_44",
                    document_id="consumer_protection_act_2019",
                    document_title="Consumer Protection Act, 2019",
                    document_type="law",
                    issuing_authority="Parliament of India",
                    section="Section 35",
                    page_start=18,
                    page_end=19,
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
