"""
Pydantic schemas for Stage 4C Cross-Encoder Reranking.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from rag.app.retrieval.models import RetrievalResult


class RerankedResponse(BaseModel):
    """
    Represents the complete response from a candidate retrieval + cross-encoder reranking pipeline.
    """
    query: str
    candidate_k: int = Field(..., description="Number of initial semantic retrieval candidate chunks")
    top_k: int = Field(..., description="Number of final top reranked chunks returned")
    results: List[RetrievalResult] = Field(default_factory=list, description="Reranked chunk results sorted by rerank_score descending")
