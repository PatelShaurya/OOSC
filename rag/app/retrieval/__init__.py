"""
Stage 4A Retrieval module providing semantic vector search.
"""
from rag.app.retrieval.models import RetrievalResult, RetrievalResponse
from rag.app.retrieval.retriever import SemanticRetriever

__all__ = ["RetrievalResult", "RetrievalResponse", "SemanticRetriever"]
