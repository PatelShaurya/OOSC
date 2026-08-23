"""
Citation Mapper module for resolving LLM-generated source_ids into verified Citation objects.
"""
from typing import List, Dict, Optional
from rag.app.citations.models import Citation, CitedGenerationResponse
from rag.app.generation.models import GenerationResponse
from rag.app.retrieval.models import RetrievalResult


class CitationMapper:
    """
    Maps LLM-referenced source_ids to verified metadata contained in RetrievalResult objects.
    Rejects unknown, fake, empty, or un-retrieved source IDs and deduplicates repeating IDs while preserving order.
    """

    def map_sources(
        self,
        source_ids: List[str],
        retrieval_results: List[RetrievalResult]
    ) -> List[Citation]:
        """
        Resolves a list of source_id strings into verified Citation objects using RetrievalResult metadata.

        Args:
            source_ids: List of chunk ID strings returned by the LLM.
            retrieval_results: List of candidate RetrievalResult objects used during generation.

        Returns:
            List of verified Citation objects in the exact order of first appearance.
        """
        if not source_ids or not retrieval_results:
            return []

        # Create chunk_id -> RetrievalResult mapping
        results_map: Dict[str, RetrievalResult] = {
            r.chunk_id: r for r in retrieval_results if r.chunk_id
        }

        citations: List[Citation] = []
        seen_ids = set()

        for sid in source_ids:
            if not sid or not isinstance(sid, str):
                continue

            clean_sid = sid.strip()
            # Deduplicate while preserving order
            if clean_sid in seen_ids:
                continue

            if clean_sid in results_map:
                res = results_map[clean_sid]
                citation = Citation(
                    source_id=res.chunk_id,
                    document_id=res.document_id,
                    document_title=res.document_title,
                    document_type=res.document_type,
                    issuing_authority=res.issuing_authority,
                    chapter=res.chapter,
                    section=res.section,
                    subsection=res.subsection,
                    page_start=res.page_start,
                    page_end=res.page_end,
                    source_url=res.source_url
                )
                citations.append(citation)
                seen_ids.add(clean_sid)
            else:
                # Reject unknown/hallucinated source ID
                print(f"Warning [CitationMapper]: Rejected unknown source_id '{clean_sid}' not present in retrieved context.")

        return citations

    def create_cited_response(
        self,
        generation_response: GenerationResponse,
        retrieval_results: List[RetrievalResult]
    ) -> CitedGenerationResponse:
        """
        Combines a GenerationResponse with verified Citation objects.

        Args:
            generation_response: Grounded answer response from Stage 5A.
            retrieval_results: Candidate chunks passed to generator.

        Returns:
            CitedGenerationResponse instance containing verified citations.
        """
        verified_citations = self.map_sources(
            source_ids=generation_response.source_ids,
            retrieval_results=retrieval_results
        )

        # Update source_ids list to match only verified citations
        verified_source_ids = [c.source_id for c in verified_citations]

        return CitedGenerationResponse(
            answer=generation_response.answer,
            what_we_understood=generation_response.what_we_understood,
            what_you_can_do=generation_response.what_you_can_do,
            what_you_need=generation_response.what_you_need,
            next_step=generation_response.next_step,
            limitations=generation_response.limitations,
            citations=verified_citations,
            source_ids=verified_source_ids
        )
