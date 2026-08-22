"""
Unit tests for Stage 2 structure-aware legal chunking pipeline.
"""
from rag.app.chunking.chunker import StructureAwareChunker
from rag.app.chunking.config import ChunkingConfig
from rag.app.chunking.models import DocumentChunksOutput, ChunkMetadata


def test_section_spanning_multiple_pages():
    """Test that a section spanning multiple pages is kept in a single chunk with page_start and page_end."""
    sample_doc = {
        "metadata": {
            "document_id": "test_act",
            "title": "Test Legal Act",
            "document_type": "law"
        },
        "pages": [
            {
                "page_number": 1,
                "text": "CHAPTER I\n1. (1) This Act may be called the Test Legal Act.\n(2) It extends to all states."
            },
            {
                "page_number": 2,
                "text": "(3) It shall come into force immediately upon publication in the gazette."
            }
        ]
    }

    chunker = StructureAwareChunker(config=ChunkingConfig(target_tokens=1000, max_tokens=1500))
    result: DocumentChunksOutput = chunker.chunk_document(sample_doc)

    assert result.total_chunks == 1
    chunk = result.chunks[0]
    assert chunk.section == "Section 1"
    assert chunk.page_start == 1
    assert chunk.page_end == 2
    assert "This Act may be called" in chunk.text
    assert "upon publication in the gazette" in chunk.text


def test_large_section_split_by_subsections():
    """Test that a section larger than max_tokens splits cleanly at subsection boundaries."""
    # Create text with subsections (1) and (2)
    sub1_text = "Sub 1 text " * 100  # ~1100 chars
    sub2_text = "Sub 2 text " * 100  # ~1100 chars

    sample_doc = {
        "metadata": {"document_id": "large_sec_doc", "title": "Large Section Act"},
        "pages": [
            {
                "page_number": 1,
                "text": f"CHAPTER I\n1. {sub1_text}"
            },
            {
                "page_number": 2,
                "text": f"(2) {sub2_text}"
            }
        ]
    }

    # Set very small max_tokens to force subsection split
    config = ChunkingConfig(target_tokens=100, max_tokens=200)
    chunker = StructureAwareChunker(config=config)
    result = chunker.chunk_document(sample_doc)

    assert result.total_chunks == 2
    c1, c2 = result.chunks
    assert c1.section == "Section 1"
    assert c2.section == "Section 1"
    assert c1.parent_section == "Section 1"
    assert c2.parent_section == "Section 1"
    assert c1.page_start == 1
    assert c2.page_start == 2


def test_fallback_unstructured_document():
    """Test fallback paragraph chunking for documents without legal structure."""
    sample_doc = {
        "metadata": {"document_id": "notice_123", "title": "Public Notice"},
        "pages": [
            {
                "page_number": 1,
                "text": "This is a public notice paragraph 1.\n\nThis is paragraph 2 of the notice."
            },
            {
                "page_number": 2,
                "text": "This is paragraph 3 on page 2."
            }
        ]
    }

    chunker = StructureAwareChunker(config=ChunkingConfig(target_tokens=1000, max_tokens=1500))
    result = chunker.chunk_document(sample_doc)

    assert result.total_chunks == 1
    chunk = result.chunks[0]
    assert chunk.page_start == 1
    assert chunk.page_end == 2
    assert "public notice paragraph 1" in chunk.text
    assert "paragraph 3 on page 2" in chunk.text
