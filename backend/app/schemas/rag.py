from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    source_title: str
    section: Optional[str] = None
    act_or_law_name: Optional[str] = None
    url: Optional[str] = None
    confidence_score: Optional[float] = None
    excerpt: Optional[str] = None


class RAGQueryRequest(BaseModel):
    query: str
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    state_jurisdiction: Optional[str] = None
    language: str = "en"
    category: Optional[str] = None
    extra_context: Optional[Dict[str, Any]] = None


class RAGQueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
    detected_legal_domain: Optional[str] = None
    applicable_remedies: List[str] = Field(default_factory=list)


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
