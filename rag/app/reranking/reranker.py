"""
Cross-Encoder Reranker using BAAI/bge-reranker-v2-m3 and integrated RerankedRetriever pipeline.
"""
from typing import List, Optional
import torch
from sentence_transformers import CrossEncoder

from rag.app.reranking.models import RerankedResponse
from rag.app.retrieval.models import RetrievalResult
from rag.app.retrieval.retriever import SemanticRetriever


import os

class CrossEncoderReranker:
    """
    Reranks candidate legal document chunks using a CrossEncoder model.
    Receives (query, candidate_chunk) pairs and computes fine-grained cross-attention relevance scores.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "auto",
        max_length: int = 1024
    ):
        self.model = None
        disable_reranker = os.getenv("DISABLE_RERANKER", "false").lower() in ("true", "1", "yes")

        if disable_reranker:
            print("CrossEncoder reranker disabled via DISABLE_RERANKER environment variable.")
            return

        effective_model = model_name or os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-small")

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        try:
            print(f"Loading cross-encoder reranker model '{effective_model}' on device '{self.device}'...")
            self.model = CrossEncoder(
                effective_model,
                max_length=max_length,
                device=self.device
            )
            print("Cross-encoder reranker model loaded successfully.")
        except Exception as exc:
            print(f"Warning: Could not load CrossEncoder model '{effective_model}' ({exc}). Reranker will operate in bypass mode.")
            self.model = None

    def rerank(
        self,
        query: str,
        results: List[RetrievalResult],
        top_k: int = 5
    ) -> List[RetrievalResult]:
        """
        Reranks a list of candidate RetrievalResult objects based on cross-encoder scoring.

        Args:
            query: User's natural-language question.
            results: Candidate chunks retrieved from stage 4A/4B vector search.
            top_k: Number of final reranked results to return.

        Returns:
            List of RetrievalResult objects updated with `rerank_score` and sorted descending.
        """
        top_k = max(1, top_k)
        clean_query = query.strip() if query else ""

        if not clean_query or not results:
            return []

        if self.model is None:
            return results[:top_k]

        # Create query-document pairs
        pairs = [[clean_query, r.text] for r in results]

        try:
            # Predict reranker scores
            scores = self.model.predict(pairs, show_progress_bar=False)

            # Copy results and attach rerank scores
            reranked_results: List[RetrievalResult] = []
            for r, score in zip(results, scores):
                res_dict = r.model_dump()
                res_dict["rerank_score"] = float(round(float(score), 4))
                reranked_results.append(RetrievalResult(**res_dict))

            # Sort descending by rerank_score
            reranked_results.sort(key=lambda x: (x.rerank_score if x.rerank_score is not None else -999.0), reverse=True)
            return reranked_results[:top_k]

        except Exception as exc:
            print(f"Warning: CrossEncoder reranker failed ({exc}). Falling back to semantic similarity order.")
            fallback_results: List[RetrievalResult] = []
            for r in results[:top_k]:
                res_dict = r.model_dump()
                fallback_results.append(RetrievalResult(**res_dict))
            return fallback_results


class RerankedRetriever:
    """
    Two-stage retrieval pipeline:
    1. Candidate retrieval using SemanticRetriever (BGE-M3 + pgvector) to get candidate_k items.
    2. Candidate reranking using CrossEncoderReranker (BAAI/bge-reranker-v2-m3) to return top_k items.
    """

    def __init__(
        self,
        semantic_retriever: Optional[SemanticRetriever] = None,
        reranker: Optional[CrossEncoderReranker] = None
    ):
        self.semantic_retriever = semantic_retriever or SemanticRetriever()
        self.reranker = reranker or CrossEncoderReranker()

    def retrieve(
        self,
        query: str,
        candidate_k: int = 10,
        top_k: int = 5,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None
    ) -> RerankedResponse:
        """
        Executes two-stage retrieval: vector candidate search + cross-encoder reranking.

        Args:
            query: User's natural-language question.
            candidate_k: Number of candidate chunks retrieved in stage 1 (default: 10).
            top_k: Number of final top-ranked chunks returned in stage 2 (default: 5).
            document_id: Optional metadata filter for document ID.
            document_type: Optional metadata filter for document type.
            issuing_authority: Optional metadata filter for issuing authority.

        Returns:
            RerankedResponse object containing query, candidate_k, top_k, and reranked results.
        """
        candidate_k = max(1, candidate_k)
        top_k = max(1, top_k)
        clean_query = query.strip() if query else ""

        if not clean_query:
            return RerankedResponse(
                query=query,
                candidate_k=candidate_k,
                top_k=top_k,
                results=[]
            )

        # Stage 1: Candidate retrieval via vector similarity search
        candidate_response = self.semantic_retriever.retrieve(
            query=clean_query,
            top_k=candidate_k,
            document_id=document_id,
            document_type=document_type,
            issuing_authority=issuing_authority
        )

        candidates = candidate_response.results

        if not candidates:
            return RerankedResponse(
                query=clean_query,
                candidate_k=candidate_k,
                top_k=top_k,
                results=[]
            )

        # Stage 2: Cross-Encoder Reranking
        reranked_results = self.reranker.rerank(
            query=clean_query,
            results=candidates,
            top_k=top_k
        )

        return RerankedResponse(
            query=clean_query,
            candidate_k=candidate_k,
            top_k=top_k,
            results=reranked_results
        )
