"""
Pydantic schemas and dataclasses for Stage 2 structure-aware chunking.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Unique document identifier")
    document_title: str = Field(..., description="Document title")
    document_type: Optional[str] = Field(None, description="Document type e.g. law, rule")
    issuing_authority: Optional[str] = Field(None, description="Issuing authority e.g. Government of India")
    source_url: Optional[str] = Field(None, description="Original source URL")
    page_start: int = Field(..., description="1-indexed starting page number")
    page_end: int = Field(..., description="1-indexed ending page number")
    chapter: Optional[str] = Field(None, description="Chapter title or header if detected")
    section: Optional[str] = Field(None, description="Section number or header if detected")
    parent_section: Optional[str] = Field(None, description="Parent section context if chunk is a subsection/clause")
    subsection: Optional[str] = Field(None, description="Subsection label or header if detected")
    chunk_index: int = Field(..., description="0-indexed sequence position of the chunk in document")
    text: str = Field(..., description="Cleaned chunk text")


class DocumentChunksOutput(BaseModel):
    document_id: str
    document_title: str
    total_pages: int
    total_chunks: int
    chunks: List[ChunkMetadata]
