"""
Pydantic API Request and Response Schemas for CivicAI RAG REST Service.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from rag.app.citations.models import Citation
from rag.app.retrieval.models import RetrievalResult


class RAGQueryRequest(BaseModel):
    """
    Request payload for end-to-end RAG query execution.
    """
    query: str = Field(..., min_length=1, description="Natural-language legal or civic query")
    top_k: int = Field(default=5, ge=1, le=20, description="Top reranked context chunks passed to generator")
    candidate_k: int = Field(default=10, ge=1, le=50, description="Initial vector candidate search pool size")
    document_id: Optional[str] = Field(default=None, description="Optional filter for specific document ID")
    document_type: Optional[str] = Field(default=None, description="Optional filter for document category (law, scheme, rule)")
    issuing_authority: Optional[str] = Field(default=None, description="Optional filter for issuing authority")

    @model_validator(mode="after")
    def validate_candidate_k_ge_top_k(self) -> "RAGQueryRequest":
        if self.candidate_k < self.top_k:
            raise ValueError(f"candidate_k ({self.candidate_k}) must be greater than or equal to top_k ({self.top_k}).")
        # Trim query whitespace
        self.query = self.query.strip()
        if not self.query:
            raise ValueError("Query string must not be empty or whitespace only.")
        return self


class RetrievalDebugInfo(BaseModel):
    """
    Debug information containing retrieval and reranking candidate details.
    """
    candidate_k: int = Field(..., description="Initial vector candidate pool count")
    top_k: int = Field(..., description="Final top reranked result count")
    results: List[RetrievalResult] = Field(default_factory=list, description="Top reranked RetrievalResult objects")


class RAGQueryResponse(BaseModel):
    """
    Response payload returned by the RAG query endpoint.
    """
    query: str = Field(..., description="Original normalized user question")
    answer: str = Field(..., description="Grounded, plain-language legal answer")
    limitations: Optional[str] = Field(default=None, description="Explicit statement of any missing information")
    citations: List[Citation] = Field(default_factory=list, description="List of verified legal citations")
    retrieval: Optional[RetrievalDebugInfo] = Field(default=None, description="Optional retrieval debug details")
