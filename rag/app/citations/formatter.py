"""
Citation Formatter module for producing clean, human-readable verified citation blocks.
"""
from typing import List
from rag.app.citations.models import Citation, CitedGenerationResponse


class CitationFormatter:
    """
    Formats verified Citation objects into human-readable citation strings without inventing missing fields.
    """

    def format_citation(self, citation: Citation, index: int = 1) -> str:
        """
        Formats a single Citation object into a structured human-readable string.

        Args:
            citation: Verified Citation object.
            index: 1-based index marker (e.g. 1 for [Source 1]).

        Returns:
            Formatted citation string.
        """
        lines = [f"[Source {index}]"]

        doc_title = citation.document_title or citation.document_id
        lines.append(f"Document: {doc_title}")

        if citation.section:
            sec_str = citation.section
            if citation.subsection:
                sec_str += f" (Subsection: {citation.subsection})"
            lines.append(f"Section: {sec_str}")
        elif citation.chapter:
            lines.append(f"Chapter: {citation.chapter}")

        if citation.page_start is not None and citation.page_end is not None:
            if citation.page_start == citation.page_end:
                lines.append(f"Pages: {citation.page_start}")
            else:
                lines.append(f"Pages: {citation.page_start}-{citation.page_end}")

        if citation.issuing_authority:
            lines.append(f"Issued by: {citation.issuing_authority}")

        if citation.source_url:
            lines.append(f"Official source: {citation.source_url}")

        return "\n".join(lines)

    def format_citations_list(self, citations: List[Citation]) -> str:
        """
        Formats a list of Citation objects into a combined, numbered citations block.

        Args:
            citations: List of verified Citation objects.

        Returns:
            Formatted multi-line citations block string.
        """
        if not citations:
            return "No citations available."

        formatted_blocks = [
            self.format_citation(c, idx)
            for idx, c in enumerate(citations, 1)
        ]
        return "\n\n".join(formatted_blocks)

    def format_cited_answer(self, response: CitedGenerationResponse) -> str:
        """
        Formats the complete grounded answer along with its verified citations and limitations.

        Args:
            response: CitedGenerationResponse object.

        Returns:
            Complete human-readable output string.
        """
        out_lines = [
            "============================================================",
            "Grounded Answer:",
            "============================================================",
            response.answer.strip(),
            ""
        ]

        if response.limitations:
            out_lines.extend([
                "------------------------------------------------------------",
                "Limitations & Scope:",
                "------------------------------------------------------------",
                response.limitations.strip(),
                ""
            ])

        out_lines.extend([
            "------------------------------------------------------------",
            "Verified Citations:",
            "------------------------------------------------------------"
        ])

        if response.citations:
            out_lines.append(self.format_citations_list(response.citations))
        else:
            out_lines.append("No verified citations attached.")

        out_lines.append("============================================================")

        return "\n".join(out_lines)
