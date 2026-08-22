from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ComplaintCategory(str, Enum):
    CONSUMER = "consumer"
    CIVIC_INFRASTRUCTURE = "civic_infrastructure"
    GOVERNMENT_SERVICE = "government_service"
    TENANCY = "tenancy"
    LEGAL_NOTICE = "legal_notice"
    CYBERCRIME = "cybercrime"
    RTI = "rti"
    OTHER = "other"


class ComplaintStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    READY_TO_FILE = "ready_to_file"
    FILED = "filed"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    category: ComplaintCategory
    jurisdiction: Optional[str] = Field(None, max_length=100)
    authority_or_opponent_name: Optional[str] = Field(None, max_length=200)
    incident_date: Optional[str] = Field(None, max_length=50)
    facts_description: str = Field(..., min_length=10, max_length=20000)
    relief_sought: Optional[List[str]] = Field(default_factory=list)
    applicant_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    respondent_details: Optional[Dict[str, Any]] = Field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ComplaintUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=200)
    category: Optional[ComplaintCategory] = None
    status: Optional[ComplaintStatus] = None
    jurisdiction: Optional[str] = Field(None, max_length=100)
    authority_or_opponent_name: Optional[str] = Field(None, max_length=200)
    incident_date: Optional[str] = Field(None, max_length=50)
    facts_description: Optional[str] = Field(None, min_length=10, max_length=20000)
    relief_sought: Optional[List[str]] = None
    generated_document: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class GenerateDocumentRequest(BaseModel):
    language: str = Field("en", description="Target document language (en, hi, etc.)")
    tone: str = Field("formal_legal", description="formal_legal, assertive, or polite_civic")
    custom_instructions: Optional[str] = Field(None, max_length=2000)
    include_statutory_references: bool = Field(True, description="Whether to include legal section numbers")


class DocumentDraftResponse(BaseModel):
    complaint_id: str
    document_title: str
    content_markdown: str
    filing_instructions: List[str] = Field(default_factory=list)
    required_attachments: List[str] = Field(default_factory=list)
    sections: Dict[str, str] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExportDocumentResponse(BaseModel):
    complaint_id: str
    document_title: str
    format: str = "markdown"
    content: str
    filename: str


class ComplaintResponse(BaseModel):
    id: str
    user_id: str
    title: str
    category: ComplaintCategory
    status: ComplaintStatus
    jurisdiction: Optional[str] = None
    authority_or_opponent_name: Optional[str] = None
    incident_date: Optional[str] = None
    facts_description: str
    relief_sought: List[str] = Field(default_factory=list)
    applicant_details: Dict[str, Any] = Field(default_factory=dict)
    respondent_details: Dict[str, Any] = Field(default_factory=dict)
    generated_document: Optional[str] = None
    filing_instructions: List[str] = Field(default_factory=list)
    required_attachments: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
