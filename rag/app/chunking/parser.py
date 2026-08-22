"""
Legal document structure parser for extracting Chapters, Sections, Subsections, and Paragraphs
across page boundaries.
"""
import re
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TextBlock:
    text: str
    page_num: int


@dataclass
class SubsectionNode:
    subsection_tag: Optional[str]
    blocks: List[TextBlock] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(b.text for b in self.blocks).strip()

    @property
    def page_start(self) -> int:
        return min((b.page_num for b in self.blocks), default=1)

    @property
    def page_end(self) -> int:
        return max((b.page_num for b in self.blocks), default=1)


@dataclass
class SectionNode:
    chapter: Optional[str]
    section: Optional[str]
    parent_section: Optional[str]
    header_text: str
    subsections: List[SubsectionNode] = field(default_factory=list)
    blocks: List[TextBlock] = field(default_factory=list)

    @property
    def all_blocks(self) -> List[TextBlock]:
        res = list(self.blocks)
        for sub in self.subsections:
            res.extend(sub.blocks)
        return res

    @property
    def full_text(self) -> str:
        if self.subsections:
            parts = [b.text for b in self.blocks if b.text.strip()]
            for sub in self.subsections:
                if sub.text:
                    parts.append(sub.text)
            return "\n".join(parts).strip()
        return "\n".join(b.text for b in self.blocks).strip()

    @property
    def page_start(self) -> int:
        blocks = self.all_blocks
        return min((b.page_num for b in blocks), default=1)

    @property
    def page_end(self) -> int:
        blocks = self.all_blocks
        return max((b.page_num for b in blocks), default=1)


class LegalDocumentParser:
    """Parses continuous page text into structural Section and Subsection nodes without page boundary splitting."""

    CHAPTER_PATTERN = re.compile(
        r"^\s*(CHAPTER\s+[I|V|X|L|C|D|M\d]+[^\n]*)$",
        re.IGNORECASE
    )

    SECTION_PATTERN = re.compile(
        r"^\s*(?:SECTION\s+)?(\d+)\.\s*(.*)$",
        re.IGNORECASE
    )

    SUBSECTION_PATTERN = re.compile(
        r"^\s*\(([0-9]+|[a-z]|[ivxlcdm]+)\)\s+(.*)$",
        re.IGNORECASE
    )

    @classmethod
    def parse_pages(cls, pages: List[dict]) -> List[SectionNode]:
        """
        Parses page-level JSON into structural Section nodes.
        Preserves section/subsection hierarchy while letting content span across PDF pages.
        """
        sections: List[SectionNode] = []
        current_chapter: Optional[str] = None
        
        current_section_node: Optional[SectionNode] = None
        current_subsection_node: Optional[SubsectionNode] = None

        for page_data in pages:
            page_num = page_data["page_number"]
            text = page_data["text"]
            lines = text.split("\n")

            line_idx = 0
            while line_idx < len(lines):
                line = lines[line_idx].strip()
                if not line:
                    if current_subsection_node:
                        current_subsection_node.blocks.append(TextBlock(text="", page_num=page_num))
                    elif current_section_node:
                        current_section_node.blocks.append(TextBlock(text="", page_num=page_num))
                    line_idx += 1
                    continue

                # 1. Check Chapter Heading
                chap_match = cls.CHAPTER_PATTERN.match(line)
                if chap_match:
                    current_chapter = line
                    # Look ahead 1 line if chapter title is split across lines (e.g. CHAPTER V \n MEDIATION)
                    if line_idx + 1 < len(lines) and lines[line_idx + 1].strip().isupper():
                        current_chapter += " — " + lines[line_idx + 1].strip()
                        line_idx += 1

                    line_idx += 1
                    continue

                # 2. Check Section Heading (e.g. "40. The District Commission...", "1. (1)...")
                sec_match = cls.SECTION_PATTERN.match(line)
                if sec_match:
                    sec_num = sec_match.group(1)
                    sec_title = f"Section {sec_num}"

                    # Finalize previous section node
                    if current_section_node:
                        if current_subsection_node:
                            current_section_node.subsections.append(current_subsection_node)
                            current_subsection_node = None
                        sections.append(current_section_node)

                    current_section_node = SectionNode(
                        chapter=current_chapter,
                        section=sec_title,
                        parent_section=sec_title,
                        header_text=line,
                        subsections=[],
                        blocks=[TextBlock(text=line, page_num=page_num)]
                    )

                    # Check if line contains inline subsection e.g., "1. (1) This Act..."
                    inline_sub = cls.SUBSECTION_PATTERN.search(sec_match.group(2))
                    if inline_sub:
                        sub_tag = f"({inline_sub.group(1)})"
                        current_subsection_node = SubsectionNode(
                            subsection_tag=sub_tag,
                            blocks=[TextBlock(text=line, page_num=page_num)]
                        )
                    else:
                        current_subsection_node = None

                    line_idx += 1
                    continue

                # 3. Check Subsection Heading inside an active section (e.g. "(1) Any person...", "(a) to issue...")
                sub_match = cls.SUBSECTION_PATTERN.match(line)
                if sub_match and current_section_node:
                    sub_tag = f"({sub_match.group(1)})"
                    
                    if current_subsection_node:
                        current_section_node.subsections.append(current_subsection_node)

                    current_subsection_node = SubsectionNode(
                        subsection_tag=sub_tag,
                        blocks=[TextBlock(text=line, page_num=page_num)]
                    )
                    line_idx += 1
                    continue

                # 4. Append general line to current subsection or section
                block = TextBlock(text=line, page_num=page_num)
                if current_subsection_node:
                    current_subsection_node.blocks.append(block)
                elif current_section_node:
                    current_section_node.blocks.append(block)
                else:
                    # Fallback section if text occurs before first section header
                    current_section_node = SectionNode(
                        chapter=current_chapter,
                        section=None,
                        parent_section=None,
                        header_text="General Content",
                        subsections=[],
                        blocks=[block]
                    )

                line_idx += 1

        # Finalize trailing section
        if current_section_node:
            if current_subsection_node:
                current_section_node.subsections.append(current_subsection_node)
            sections.append(current_section_node)

        # Fallback if no sections were detected at all
        if not sections:
            return cls._fallback_document_sections(pages)

        return sections

    @classmethod
    def _fallback_document_sections(cls, pages: List[dict]) -> List[SectionNode]:
        """Creates fallback sections when no legal structure is found."""
        all_blocks = []
        for p in pages:
            page_num = p["page_number"]
            for line in p["text"].split("\n"):
                if line.strip():
                    all_blocks.append(TextBlock(text=line.strip(), page_num=page_num))

        return [
            SectionNode(
                chapter=None,
                section=None,
                parent_section=None,
                header_text="Document Content",
                subsections=[],
                blocks=all_blocks
            )
        ]
