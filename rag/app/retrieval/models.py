"""
Pydantic schemas for Stage 4A Semantic Retrieval.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievalResult(BaseModel):
    """
    Represents a single retrieved chunk with its metadata and similarity score.
    """
    chunk_id: str
    document_id: str
    document_title: Optional[str] = None
    document_type: Optional[str] = None
    issuing_authority: Optional[str] = None
    source_url: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    parent_section: Optional[str] = None
    subsection: Optional[str] = None
    chunk_index: Optional[int] = None
    text: str
    similarity_score: float = Field(..., description="Cosine similarity score between 0.0 and 1.0 (higher is better)")


class RetrievalResponse(BaseModel):
    """
    Represents the complete response from a semantic retrieval query.
    """
    query: str
    top_k: int
    results: List[RetrievalResult] = Field(default_factory=list)
