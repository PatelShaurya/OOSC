from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class Citation(BaseModel):
    """
    Verified citation schema returned by the RAG Service.
    Supports all required legal document metadata fields and legacy aliases.
    """
    source_id: str = Field(default="", description="Unique chunk/source identifier")
    document_id: str = Field(default="", description="Document identifier")
    document_title: Optional[str] = Field(default=None, description="Title of the legal document")
    document_type: Optional[str] = Field(default=None, description="Category of document (law, scheme, rule)")
    issuing_authority: Optional[str] = Field(default=None, description="Issuing government body or authority")
    chapter: Optional[str] = Field(default=None, description="Chapter within document")
    section: Optional[str] = Field(default=None, description="Section provision number")
    subsection: Optional[str] = Field(default=None, description="Subsection clause details")
    page_start: Optional[int] = Field(default=None, description="Starting page number")
    page_end: Optional[int] = Field(default=None, description="Ending page number")
    source_url: Optional[str] = Field(default=None, description="Official public source URL")

    # Legacy compatibility fields
    source_title: Optional[str] = Field(default=None, description="Legacy document title alias")
    act_or_law_name: Optional[str] = Field(default=None, description="Legacy law name alias")
    url: Optional[str] = Field(default=None, description="Legacy URL alias")
    confidence_score: Optional[float] = Field(default=None, description="Confidence score")
    excerpt: Optional[str] = Field(default=None, description="Excerpt snippet")

    @model_validator(mode="before")
    @classmethod
    def populate_aliases(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Map legacy source_title to document_title if document_title is missing
            if not data.get("document_title") and data.get("source_title"):
                data["document_title"] = data["source_title"]
            if not data.get("source_title") and data.get("document_title"):
                data["source_title"] = data["document_title"]
            if not data.get("source_url") and data.get("url"):
                data["source_url"] = data["url"]
            if not data.get("url") and data.get("source_url"):
                data["url"] = data["source_url"]
        return data


class RAGQueryRequest(BaseModel):
    """
    HTTP request payload sent from Main Backend to RAG Service (/api/v1/query).
    """
    query: str = Field(..., description="User's natural language question")
    top_k: int = Field(default=5, ge=1, le=20, description="Top reranked chunks")
    candidate_k: int = Field(default=10, ge=1, le=50, description="Initial candidate pool size")
    document_id: Optional[str] = Field(default=None, description="Optional document ID filter")
    document_type: Optional[str] = Field(default=None, description="Optional document category filter")
    issuing_authority: Optional[str] = Field(default=None, description="Optional issuing authority filter")
    mode: Optional[str] = Field(default=None, description="Optional execution mode e.g. 'rti_draft'")
    applicant_name: Optional[str] = Field(default=None, description="Optional applicant name for drafting")
    applicant_address: Optional[str] = Field(default=None, description="Optional applicant address for drafting")
    public_authority: Optional[str] = Field(default=None, description="Optional target public authority name")


class RAGQueryResponse(BaseModel):
    """
    Typed response model received from the RAG Service.
    Omits internal retrieval debug data for public backend consumption.
    """
    query: Optional[str] = Field(default=None, description="Original query string")
    answer: str = Field(..., description="Grounded plain-language answer")
    what_we_understood: Optional[str] = Field(default=None, description="Brief summary of user situation")
    what_you_can_do: List[str] = Field(default_factory=list, description="Action steps supported by retrieved sources")
    what_you_need: List[str] = Field(default_factory=list, description="Required information/documents supported by retrieved sources")
    next_step: Optional[str] = Field(default=None, description="Concrete next step supported by retrieved sources")
    limitations: Optional[str] = Field(default=None, description="Explicit limitations or missing info statement")
    citations: List[Citation] = Field(default_factory=list, description="Verified legal citations")
    suggested_followups: List[str] = Field(default_factory=list, description="Suggested followup questions")
    detected_legal_domain: Optional[str] = Field(default=None, description="Detected legal domain/category")
    applicable_remedies: List[str] = Field(default_factory=list, description="Applicable legal remedies")


class RAGDocumentGenerationRequest(BaseModel):
    document_type: str
    applicant_details: Dict[str, Any]
    respondent_details: Dict[str, Any]
    facts_and_events: List[str]
    grievance_description: str
    relief_sought: List[str]
    jurisdiction: Optional[str] = None
    language: str = "en"


class RAGDocumentGenerationResponse(BaseModel):
    document_title: str
    content_markdown: str
    sections: Dict[str, str] = Field(default_factory=dict)
    filing_instructions: List[str] = Field(default_factory=list)
    required_attachments: List[str] = Field(default_factory=list)


class RAGFormFieldExtractionRequest(BaseModel):
    user_input: str
    form_type: str
    current_fields: Dict[str, Any] = Field(default_factory=dict)


class RAGFormFieldExtractionResponse(BaseModel):
    extracted_fields: Dict[str, Any] = Field(default_factory=dict)
    next_question: Optional[str] = None
    is_complete: bool = False
    validation_notes: List[str] = Field(default_factory=list)
