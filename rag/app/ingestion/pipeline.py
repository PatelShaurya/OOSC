"""
Ingestion pipeline orchestrator.
Loads PDF, cleans page texts, applies metadata, and saves JSON output.
"""
import json
from pathlib import Path
from typing import List, Optional, Union

from rag.app.ingestion.cleaner import TextCleaner
from rag.app.ingestion.loader import DocumentLoader
from rag.app.ingestion.models import DocumentMetadata, PageContent, ProcessedDocument


class IngestionPipeline:
    """Orchestrates document loading, cleaning, metadata attachment, and export."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path("rag/data/processed")

    def process_document(
        self,
        pdf_path: Union[str, Path],
        document_id: str,
        title: str,
        source_url: Optional[str] = None,
        document_type: Optional[str] = None,
        issuing_authority: Optional[str] = None,
        save: bool = True,
    ) -> ProcessedDocument:
        """
        Runs full ingestion process for a PDF file.

        Args:
            pdf_path: Path to the input PDF file.
            document_id: Unique string ID for document.
            title: Document title.
            source_url: Optional origin URL.
            document_type: Optional document classification.
            issuing_authority: Optional issuing authority.
            save: If True, writes JSON output to output_dir/<document_id>.json.

        Returns:
            ProcessedDocument Pydantic instance.
        """
        # 1. Load PDF pages
        raw_pages = DocumentLoader.load_pdf(pdf_path)

        # 2. Clean each page text
        pages: List[PageContent] = []
        for page_num, raw_text in raw_pages:
            cleaned_text = TextCleaner.clean_text(raw_text)
            pages.append(PageContent(page_number=page_num, text=cleaned_text))

        # 3. Construct Metadata & ProcessedDocument
        metadata = DocumentMetadata(
            document_id=document_id,
            title=title,
            source_url=source_url,
            document_type=document_type,
            issuing_authority=issuing_authority,
        )

        doc = ProcessedDocument(metadata=metadata, pages=pages)

        # 4. Save to JSON if requested
        if save:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_file = self.output_dir / f"{document_id}.json"

            doc_dict = doc.model_dump()

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(doc_dict, f, indent=2, ensure_ascii=False)

        return doc
