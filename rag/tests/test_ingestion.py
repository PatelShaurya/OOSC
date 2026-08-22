"""
Tests for Stage 1 Document Ingestion pipeline.
"""
import json
from pathlib import Path
import pymupdf as fitz
import pytest

from rag.app.ingestion.cleaner import TextCleaner
from rag.app.ingestion.loader import DocumentLoader, DocumentLoaderError
from rag.app.ingestion.models import DocumentMetadata, PageContent, ProcessedDocument
from rag.app.ingestion.pipeline import IngestionPipeline


@pytest.fixture
def sample_pdf(tmp_path) -> Path:
    """Fixture to generate a temporary multi-page PDF."""
    pdf_path = tmp_path / "test_document.pdf"
    doc = fitz.open()

    page1 = doc.new_page()
    page1.insert_text((50, 50), "Page 1: Section 1.\n  Legal text line 1  \n\n  Line 2.  ")

    page2 = doc.new_page()
    page2.insert_text((50, 50), "Page 2: Section 2.\n  Further legal wording here.  ")

    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_pdf_extraction_and_page_preservation(sample_pdf):
    """Test PDF loading extracts pages with correct 1-indexed numbers."""
    pages = DocumentLoader.load_pdf(sample_pdf)
    assert len(pages) == 2
    assert pages[0][0] == 1
    assert "Page 1: Section 1." in pages[0][1]
    assert pages[1][0] == 2
    assert "Page 2: Section 2." in pages[1][1]


def test_missing_pdf_handling():
    """Test that missing PDF raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        DocumentLoader.load_pdf("non_existent_file.pdf")


def test_invalid_file_handling(tmp_path):
    """Test that non-PDF file raises DocumentLoaderError."""
    not_a_pdf = tmp_path / "test.txt"
    not_a_pdf.write_text("Hello world")

    with pytest.raises(DocumentLoaderError):
        DocumentLoader.load_pdf(not_a_pdf)


def test_text_cleaning():
    """Test text cleaner normalizes whitespace while keeping content meaning intact."""
    raw_text = "   Section 1.   \r\n\r\n   Line 1\t\twith spaces.   \n\n\n\nLine 2   "
    cleaned = TextCleaner.clean_text(raw_text)

    assert "Section 1." in cleaned
    assert "Line 1 with spaces." in cleaned
    # Ensure line endings normalized and max 2 newlines
    assert "\r" not in cleaned
    assert "\n\n\n" not in cleaned


def test_full_pipeline_and_json_structure(sample_pdf, tmp_path):
    """Test end-to-end pipeline execution and verify output JSON structure."""
    output_dir = tmp_path / "processed"
    pipeline = IngestionPipeline(output_dir=output_dir)

    doc = pipeline.process_document(
        pdf_path=sample_pdf,
        document_id="doc_test_001",
        title="Test Legal Act 2024",
        source_url="https://example.gov.in/act.pdf",
        document_type="law",
        issuing_authority="Ministry of Justice",
        save=True,
    )

    # Check Pydantic model
    assert isinstance(doc, ProcessedDocument)
    assert doc.metadata.document_id == "doc_test_001"
    assert len(doc.pages) == 2

    # Check JSON file written to disk
    json_path = output_dir / "doc_test_001.json"
    assert json_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "pages" in data
    assert data["metadata"]["document_id"] == "doc_test_001"
    assert data["metadata"]["title"] == "Test Legal Act 2024"
    assert data["metadata"]["source_url"] == "https://example.gov.in/act.pdf"
    assert data["metadata"]["document_type"] == "law"
    assert data["metadata"]["issuing_authority"] == "Ministry of Justice"
    assert len(data["pages"]) == 2
    assert data["pages"][0]["page_number"] == 1
    assert "Page 1: Section 1." in data["pages"][0]["text"]
