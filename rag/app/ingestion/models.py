"""
Pydantic schemas for document ingestion.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    document_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source_url: Optional[str] = Field(None, description="Original source URL")
    document_type: Optional[str] = Field(None, description="Type of document e.g. law, rule, form")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority e.g. Government, Court")


class PageContent(BaseModel):
    page_number: int = Field(..., description="1-indexed page number")
    text: str = Field(..., description="Cleaned extracted text of the page")


class ProcessedDocument(BaseModel):
    metadata: DocumentMetadata
    pages: List[PageContent]
