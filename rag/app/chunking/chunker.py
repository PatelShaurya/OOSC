"""
Structure-aware legal document chunker implementing the hierarchy:
Chapter -> Section -> Subsection -> Paragraph -> Sentence fallback.
"""
import re
from typing import List, Dict, Any, Optional
from rag.app.chunking.config import ChunkingConfig, DEFAULT_CHUNKING_CONFIG
from rag.app.chunking.models import ChunkMetadata, DocumentChunksOutput
from rag.app.chunking.parser import LegalDocumentParser, SectionNode, SubsectionNode, TextBlock


class StructureAwareChunker:
    """Orchestrates legal chunking following strict hierarchical boundaries without splitting at PDF pages."""

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or DEFAULT_CHUNKING_CONFIG

    def chunk_document(self, processed_doc: Dict[str, Any]) -> DocumentChunksOutput:
        metadata = processed_doc.get("metadata", {})
        doc_id = metadata.get("document_id", "unknown_doc")
        title = metadata.get("title", "Untitled Document")
        doc_type = metadata.get("document_type")
        authority = metadata.get("issuing_authority")
        source_url = metadata.get("source_url")
        pages = processed_doc.get("pages", [])

        total_pages = len(pages)
        if not pages:
            return DocumentChunksOutput(
                document_id=doc_id,
                document_title=title,
                total_pages=0,
                total_chunks=0,
                chunks=[]
            )

        # Step 1: Parse structural section nodes across pages
        sections = LegalDocumentParser.parse_pages(pages)

        raw_chunks: List[Dict[str, Any]] = []

        # Step 2: Apply legal chunking hierarchy
        for section in sections:
            section_chunks = self._chunk_section_node(section)
            raw_chunks.extend(section_chunks)

        # Step 3: Build ChunkMetadata objects
        chunks: List[ChunkMetadata] = []
        for idx, item in enumerate(raw_chunks):
            sec_label = item.get("section") or "Section"
            chunk_id = f"{doc_id}_{sec_label.lower().replace(' ', '_')}_{idx + 1}"

            chunk_meta = ChunkMetadata(
                chunk_id=chunk_id,
                document_id=doc_id,
                document_title=title,
                document_type=doc_type,
                issuing_authority=authority,
                source_url=source_url,
                page_start=item["page_start"],
                page_end=item["page_end"],
                chapter=item.get("chapter"),
                section=item.get("section"),
                parent_section=item.get("parent_section"),
                subsection=item.get("subsection"),
                chunk_index=idx,
                text=item["text"],
            )
            chunks.append(chunk_meta)

        return DocumentChunksOutput(
            document_id=doc_id,
            document_title=title,
            total_pages=total_pages,
            total_chunks=len(chunks),
            chunks=chunks
        )

    def _chunk_section_node(self, section: SectionNode) -> List[Dict[str, Any]]:
        """Applies chunking hierarchy to a SectionNode."""
        sec_text = section.full_text
        
        # 1. Entire Section fits in maximum character limit
        if len(sec_text) <= self.config.max_chars and sec_text.strip():
            return [{
                "chapter": section.chapter,
                "section": section.section,
                "parent_section": section.parent_section,
                "subsection": None,
                "page_start": section.page_start,
                "page_end": section.page_end,
                "text": sec_text
            }]

        # 2. Section exceeds max size -> Split by Subsections
        if section.subsections:
            return self._chunk_by_subsections(section)

        # 3. Section exceeds max size with no subsections -> Split by Paragraphs
        return self._chunk_blocks_by_paragraphs(
            blocks=section.all_blocks,
            chapter=section.chapter,
            section=section.section,
            parent_section=section.parent_section,
            subsection=None
        )

    def _chunk_by_subsections(self, section: SectionNode) -> List[Dict[str, Any]]:
        """Groups subsections into chunks up to target size, splitting oversized subsections as needed."""
        chunks: List[Dict[str, Any]] = []

        curr_blocks: List[TextBlock] = []
        curr_sub_tags: List[str] = []
        curr_len = 0

        # Include header blocks if any exist before first subsection
        if section.blocks:
            curr_blocks.extend(section.blocks)
            curr_len += sum(len(b.text) for b in section.blocks)

        for sub in section.subsections:
            sub_len = sum(len(b.text) for b in sub.blocks)

            # Case A: An individual subsection is larger than max_chars -> Split subsection by Paragraphs
            if sub_len > self.config.max_chars:
                # Flush current accumulated subsections first
                if curr_blocks:
                    chunks.append(self._make_chunk_dict(
                        blocks=curr_blocks,
                        chapter=section.chapter,
                        section=section.section,
                        parent_section=section.parent_section,
                        subsection=", ".join(curr_sub_tags) if curr_sub_tags else None
                    ))
                    curr_blocks = []
                    curr_sub_tags = []
                    curr_len = 0

                sub_chunks = self._chunk_blocks_by_paragraphs(
                    blocks=sub.blocks,
                    chapter=section.chapter,
                    section=section.section,
                    parent_section=section.parent_section,
                    subsection=sub.subsection_tag
                )
                chunks.extend(sub_chunks)
                continue

            # Case B: Adding subsection exceeds target_chars -> Flush accumulated chunk
            if curr_len > 0 and (curr_len + sub_len) > self.config.target_chars:
                chunks.append(self._make_chunk_dict(
                    blocks=curr_blocks,
                    chapter=section.chapter,
                    section=section.section,
                    parent_section=section.parent_section,
                    subsection=", ".join(curr_sub_tags) if curr_sub_tags else None
                ))
                curr_blocks = []
                curr_sub_tags = []
                curr_len = 0

            curr_blocks.extend(sub.blocks)
            if sub.subsection_tag:
                curr_sub_tags.append(sub.subsection_tag)
            curr_len += sub_len

        if curr_blocks:
            chunks.append(self._make_chunk_dict(
                blocks=curr_blocks,
                chapter=section.chapter,
                section=section.section,
                parent_section=section.parent_section,
                subsection=", ".join(curr_sub_tags) if curr_sub_tags else None
            ))

        return chunks

    def _chunk_blocks_by_paragraphs(
        self,
        blocks: List[TextBlock],
        chapter: Optional[str],
        section: Optional[str],
        parent_section: Optional[str],
        subsection: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Splits a block of text by paragraph boundaries (\n\n). Fallback to sentence boundaries if needed."""
        full_text = "\n".join(b.text for b in blocks).strip()
        if not full_text:
            return []

        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        chunks: List[Dict[str, Any]] = []

        curr_paras: List[str] = []
        curr_len = 0

        for p in paragraphs:
            p_len = len(p)
            # If paragraph itself is too large -> split by sentences
            if p_len > self.config.max_chars:
                if curr_paras:
                    chunks.append(self._build_text_chunk(
                        text="\n\n".join(curr_paras),
                        blocks=blocks,
                        chapter=chapter,
                        section=section,
                        parent_section=parent_section,
                        subsection=subsection
                    ))
                    curr_paras = []
                    curr_len = 0

                sentence_chunks = self._split_paragraph_by_sentences(
                    para=p,
                    blocks=blocks,
                    chapter=chapter,
                    section=section,
                    parent_section=parent_section,
                    subsection=subsection
                )
                chunks.extend(sentence_chunks)
                continue

            if curr_len > 0 and (curr_len + p_len) > self.config.target_chars:
                chunks.append(self._build_text_chunk(
                    text="\n\n".join(curr_paras),
                    blocks=blocks,
                    chapter=chapter,
                    section=section,
                    parent_section=parent_section,
                    subsection=subsection
                ))
                curr_paras = []
                curr_len = 0

            curr_paras.append(p)
            curr_len += p_len

        if curr_paras:
            chunks.append(self._build_text_chunk(
                text="\n\n".join(curr_paras),
                blocks=blocks,
                chapter=chapter,
                section=section,
                parent_section=parent_section,
                subsection=subsection
            ))

        return chunks

    def _split_paragraph_by_sentences(
        self,
        para: str,
        blocks: List[TextBlock],
        chapter: Optional[str],
        section: Optional[str],
        parent_section: Optional[str],
        subsection: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Splits an oversized paragraph into sentence-aware chunks with limited overlap."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", para) if s.strip()]
        chunks: List[Dict[str, Any]] = []

        curr_sents: List[str] = []
        curr_len = 0

        for sent in sentences:
            sent_len = len(sent)
            if curr_len > 0 and (curr_len + sent_len) > self.config.target_chars:
                chunk_text = " ".join(curr_sents)
                chunks.append(self._build_text_chunk(
                    text=chunk_text,
                    blocks=blocks,
                    chapter=chapter,
                    section=section,
                    parent_section=parent_section,
                    subsection=subsection
                ))

                # Retain overlap sentences
                overlap_sents: List[str] = []
                overlap_len = 0
                for s in reversed(curr_sents):
                    if overlap_len + len(s) <= self.config.overlap_chars:
                        overlap_sents.insert(0, s)
                        overlap_len += len(s)
                    else:
                        break
                curr_sents = overlap_sents
                curr_len = overlap_len

            curr_sents.append(sent)
            curr_len += sent_len

        if curr_sents:
            chunks.append(self._build_text_chunk(
                text=" ".join(curr_sents),
                blocks=blocks,
                chapter=chapter,
                section=section,
                parent_section=parent_section,
                subsection=subsection
            ))

        return chunks

    def _make_chunk_dict(
        self,
        blocks: List[TextBlock],
        chapter: Optional[str],
        section: Optional[str],
        parent_section: Optional[str],
        subsection: Optional[str]
    ) -> Dict[str, Any]:
        """Creates chunk dict computing page_start and page_end from block metadata."""
        non_empty_blocks = [b for b in blocks if b.text.strip()]
        if not non_empty_blocks:
            non_empty_blocks = blocks

        page_start = min((b.page_num for b in non_empty_blocks), default=1)
        page_end = max((b.page_num for b in non_empty_blocks), default=1)
        text = "\n".join(b.text for b in blocks if b.text.strip()).strip()

        return {
            "chapter": chapter,
            "section": section,
            "parent_section": parent_section,
            "subsection": subsection,
            "page_start": page_start,
            "page_end": page_end,
            "text": text
        }

    def _build_text_chunk(
        self,
        text: str,
        blocks: List[TextBlock],
        chapter: Optional[str],
        section: Optional[str],
        parent_section: Optional[str],
        subsection: Optional[str]
    ) -> Dict[str, Any]:
        """Maps specific text slice back to pages using matching blocks."""
        non_empty_blocks = [b for b in blocks if b.text.strip()]
        if not non_empty_blocks:
            non_empty_blocks = blocks

        page_start = min((b.page_num for b in non_empty_blocks), default=1)
        page_end = max((b.page_num for b in non_empty_blocks), default=1)

        return {
            "chapter": chapter,
            "section": section,
            "parent_section": parent_section,
            "subsection": subsection,
            "page_start": page_start,
            "page_end": page_end,
            "text": text
        }
