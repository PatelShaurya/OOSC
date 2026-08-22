"""
Context Builder for converting RetrievalResult chunks into formatted, grounded context for LLM generation.
"""
from typing import List, Tuple
from rag.app.retrieval.models import RetrievalResult


class ContextBuilder:
    """
    Formats top reranked RetrievalResult chunks into clearly separated, immutable context blocks for LLM consumption.
    """

    def build_context(self, results: List[RetrievalResult]) -> Tuple[str, List[str]]:
        """
        Converts a list of RetrievalResult objects into a formatted context string and extracts valid chunk IDs.

        Args:
            results: List of top reranked RetrievalResult objects.

        Returns:
            Tuple of (formatted_context_text, valid_chunk_ids_list)
        """
        if not results:
            return "No relevant legal sources available.", []

        context_blocks = []
        valid_chunk_ids = []

        for idx, item in enumerate(results, 1):
            valid_chunk_ids.append(item.chunk_id)

            pages_str = f"{item.page_start}-{item.page_end}" if item.page_start and item.page_end else "N/A"
            doc_title = item.document_title or item.document_id
            doc_type = item.document_type or "N/A"
            authority = item.issuing_authority or "N/A"
            chapter = item.chapter or "N/A"
            section = item.section or "N/A"
            subsection = item.subsection or "N/A"
            url = item.source_url or "N/A"

            block = (
                f"[SOURCE {idx}]\n"
                f"Chunk ID: {item.chunk_id}\n"
                f"Document: {doc_title} (ID: {item.document_id})\n"
                f"Document Type: {doc_type}\n"
                f"Issuing Authority: {authority}\n"
                f"Chapter: {chapter}\n"
                f"Section: {section}\n"
                f"Subsection: {subsection}\n"
                f"Pages: {pages_str}\n"
                f"Source URL: {url}\n\n"
                f"Text:\n"
                f"{item.text.strip()}\n"
            )
            context_blocks.append(block)

        context_text = "\n" + ("=" * 50) + "\n\n".join([""] + context_blocks) + "\n" + ("=" * 50)
        return context_text, valid_chunk_ids
