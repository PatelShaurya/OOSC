"""
RAG Pipeline Orchestrator connecting Retrieval, Reranking, LLM Generation, and Verified Citation Mapping.
"""
from typing import Optional, List
from rag.app.api.models import RAGQueryResponse, RetrievalDebugInfo
from rag.app.citations.mapper import CitationMapper
from rag.app.generation.generator import Generator
from rag.app.reranking.reranker import RerankedRetriever


class RAGPipeline:
    """
    Orchestrates the end-to-end CivicAI RAG pipeline:
    User Query -> RerankedRetriever (4C) -> Generator (5A) -> CitationMapper (5B) -> RAGQueryResponse
    """

    def __init__(
        self,
        retriever: Optional[RerankedRetriever] = None,
        generator: Optional[Generator] = None,
        citation_mapper: Optional[CitationMapper] = None
    ):
        self.retriever = retriever or RerankedRetriever()
        self.generator = generator or Generator()
        self.citation_mapper = citation_mapper or CitationMapper()

    def query(
        self,
        query: str,
        top_k: int = 5,
        candidate_k: int = 10,
        document_id: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        include_debug: bool = True
    ) -> RAGQueryResponse:
        """
        Executes end-to-end RAG pipeline for a given user query.

        Args:
            query: User's natural-language question.
            top_k: Final top reranked results passed to LLM (default: 5).
            candidate_k: Initial vector search candidate pool size (default: 10).
            document_id: Optional metadata filter for document ID.
            document_type: Optional metadata filter for document type.
            issuing_authority: Optional metadata filter for issuing authority.
            include_debug: Whether to include retrieval debug details in output.

        Returns:
            RAGQueryResponse containing answer, limitations, verified citations, and debug retrieval info.
        """
        clean_query = query.strip()

        # 1. Two-stage candidate retrieval and cross-encoder reranking
        reranked_resp = self.retriever.retrieve(
            query=clean_query,
            candidate_k=candidate_k,
            top_k=top_k,
            document_id=document_id,
            document_type=document_type,
            issuing_authority=issuing_authority
        )

        # 2. Grounded LLM generation
        gen_resp = self.generator.generate(
            question=clean_query,
            retrieved_results=reranked_resp.results
        )

        # 3. Verified citation mapping
        cited_resp = self.citation_mapper.create_cited_response(
            generation_response=gen_resp,
            retrieval_results=reranked_resp.results
        )

        # 4. Construct response model
        debug_info = None
        if include_debug:
            debug_info = RetrievalDebugInfo(
                candidate_k=candidate_k,
                top_k=top_k,
                results=reranked_resp.results
            )

        return RAGQueryResponse(
            query=clean_query,
            answer=cited_resp.answer,
            limitations=cited_resp.limitations,
            citations=cited_resp.citations,
            retrieval=debug_info
        )
