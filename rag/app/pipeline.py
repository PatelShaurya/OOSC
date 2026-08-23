"""
RAG Pipeline Orchestrator connecting Retrieval, Reranking, LLM Generation, and Verified Citation Mapping.
"""
from typing import Optional, List, TYPE_CHECKING
from rag.app.citations.mapper import CitationMapper
from rag.app.generation.generator import Generator
from rag.app.reranking.reranker import RerankedRetriever

if TYPE_CHECKING:
    from rag.app.api.models import RAGQueryResponse


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
        mode: Optional[str] = None,
        applicant_name: Optional[str] = None,
        applicant_address: Optional[str] = None,
        public_authority: Optional[str] = None,
        include_debug: bool = True
    ) -> "RAGQueryResponse":
        """
        Executes end-to-end RAG pipeline for a given user query or RTI draft request.
        """
        clean_query = query.strip()

        # If RTI drafting mode, default document_type filter to 'law' if unset
        effective_doc_type = document_type
        if mode == "rti_draft" and not effective_doc_type:
            effective_doc_type = "law"

        # 1. Two-stage candidate retrieval and cross-encoder reranking
        reranked_resp = self.retriever.retrieve(
            query=clean_query,
            candidate_k=candidate_k,
            top_k=top_k,
            document_id=document_id,
            document_type=effective_doc_type,
            issuing_authority=issuing_authority
        )

        # 2. Grounded LLM generation
        gen_resp = self.generator.generate(
            question=clean_query,
            retrieved_results=reranked_resp.results,
            mode=mode,
            applicant_name=applicant_name,
            applicant_address=applicant_address,
            public_authority=public_authority,
        )

        # 3. Verified citation mapping
        cited_resp = self.citation_mapper.create_cited_response(
            generation_response=gen_resp,
            retrieval_results=reranked_resp.results
        )

        # 4. Construct response model
        from rag.app.api.models import RAGQueryResponse, RetrievalDebugInfo

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
