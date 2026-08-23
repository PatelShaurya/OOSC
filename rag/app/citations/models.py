"""
Pydantic schemas for Stage 5B Citation Mapping and Verified Formatting.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Citation(BaseModel):
    """
    Represents a verified legal citation resolved strictly from RetrievalResult metadata.
    """
    source_id: str = Field(..., description="Unique chunk_id representing the source")
    document_id: str = Field(..., description="Document identifier")
    document_title: Optional[str] = Field(default=None, description="Title of the legal document")
    document_type: Optional[str] = Field(default=None, description="Category of the document (law, scheme, rule)")
    issuing_authority: Optional[str] = Field(default=None, description="Issuing government body or authority")
    chapter: Optional[str] = Field(default=None, description="Chapter within the document")
    section: Optional[str] = Field(default=None, description="Section provision number")
    subsection: Optional[str] = Field(default=None, description="Subsection clause details")
    page_start: Optional[int] = Field(default=None, description="Starting page number in original document")
    page_end: Optional[int] = Field(default=None, description="Ending page number in original document")
    source_url: Optional[str] = Field(default=None, description="Official public source URL")


class CitedGenerationResponse(BaseModel):
    """
    Extended response model combining grounded answer generation with verified citations.
    """
    answer: str = Field(..., description="Grounded, plain-language answer")
    what_we_understood: Optional[str] = Field(default=None, description="Brief summary of user situation")
    what_you_can_do: List[str] = Field(default_factory=list, description="Action steps supported by retrieved sources")
    what_you_need: List[str] = Field(default_factory=list, description="Required information/documents supported by retrieved sources")
    next_step: Optional[str] = Field(default=None, description="Concrete next step supported by retrieved sources")
    limitations: Optional[str] = Field(default=None, description="Explicit statement of missing or absent information")
    citations: List[Citation] = Field(default_factory=list, description="List of verified citations resolved from metadata")
    source_ids: List[str] = Field(default_factory=list, description="Original source chunk IDs relied upon (for debugging)")
