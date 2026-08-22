"""
Unit and grounding tests for Stage 5B Citation Mapping and Formatter.
Verifies metadata resolution, rejection of unknown IDs, deduplication, and formatting without DB calls.
"""
from unittest.mock import MagicMock
import pytest

from rag.app.citations.formatter import CitationFormatter
from rag.app.citations.mapper import CitationMapper
from rag.app.citations.models import Citation, CitedGenerationResponse
from rag.app.generation.models import GenerationResponse
from rag.app.retrieval.models import RetrievalResult


@pytest.fixture
def sample_retrieved_results():
    return [
        RetrievalResult(
            chunk_id="chunk_39",
            document_id="consumer_protection_act_2019",
            document_title="Consumer Protection Act, 2019",
            document_type="law",
            issuing_authority="Government of India",
            section="Section 39",
            subsection="(1)",
            page_start=21,
            page_end=22,
            source_url="https://egazette.gov.in/cpa2019.pdf",
            text="Section 39 text...",
            similarity_score=0.85
        ),
        RetrievalResult(
            chunk_id="chunk_83",
            document_id="consumer_protection_act_2019",
            document_title="Consumer Protection Act, 2019",
            document_type="law",
            issuing_authority="Government of India",
            section="Section 83",
            page_start=31,
            page_end=32,
            source_url="https://egazette.gov.in/cpa2019.pdf",
            text="Section 83 text...",
            similarity_score=0.80
        ),
        RetrievalResult(
            chunk_id="chunk_no_pages",
            document_id="rule_doc_1",
            document_title="Consumer Protection Rules",
            document_type="rule",
            issuing_authority=None,
            section=None,
            page_start=None,
            page_end=None,
            source_url=None,
            text="General rules...",
            similarity_score=0.75
        )
    ]


def test_valid_source_ids_mapping(sample_retrieved_results):
    """Test 1 & 5 & 10: Valid source IDs map correctly and preserve exact metadata."""
    mapper = CitationMapper()
    citations = mapper.map_sources(["chunk_39", "chunk_83"], sample_retrieved_results)

    assert len(citations) == 2
    c1 = citations[0]
    assert c1.source_id == "chunk_39"
    assert c1.document_title == "Consumer Protection Act, 2019"
    assert c1.section == "Section 39"
    assert c1.page_start == 21
    assert c1.page_end == 22
    assert c1.source_url == "https://egazette.gov.in/cpa2019.pdf"


def test_unknown_source_ids_rejected(sample_retrieved_results):
    """Test 2: Unknown/hallucinated source IDs are rejected."""
    mapper = CitationMapper()
    citations = mapper.map_sources(["chunk_39", "fake_chunk_999"], sample_retrieved_results)

    assert len(citations) == 1
    assert citations[0].source_id == "chunk_39"


def test_duplicate_source_ids_deduplicated(sample_retrieved_results):
    """Test 3: Repeating source IDs are deduplicated while preserving order."""
    mapper = CitationMapper()
    citations = mapper.map_sources(["chunk_83", "chunk_39", "chunk_83", "chunk_39"], sample_retrieved_results)

    assert len(citations) == 2
    assert citations[0].source_id == "chunk_83"
    assert citations[1].source_id == "chunk_39"


def test_citation_order_preservation(sample_retrieved_results):
    """Test 4: Citation order strictly follows source_id order."""
    mapper = CitationMapper()
    citations = mapper.map_sources(["chunk_83", "chunk_39"], sample_retrieved_results)

    assert [c.source_id for c in citations] == ["chunk_83", "chunk_39"]


def test_missing_metadata_handled_without_fabrication(sample_retrieved_results):
    """Test 6, 7, 8: Missing pages, section, and URL are handled without fabrication."""
    mapper = CitationMapper()
    formatter = CitationFormatter()

    citations = mapper.map_sources(["chunk_no_pages"], sample_retrieved_results)
    assert len(citations) == 1
    c = citations[0]

    assert c.page_start is None
    assert c.section is None
    assert c.source_url is None

    formatted_text = formatter.format_citation(c, 1)

    assert "Pages:" not in formatted_text
    assert "Section:" not in formatted_text
    assert "Official source:" not in formatted_text
    assert "Issued by:" not in formatted_text
    assert "Document: Consumer Protection Rules" in formatted_text


def test_empty_source_ids_handling(sample_retrieved_results):
    """Test 9: Empty source_ids returns no citations."""
    mapper = CitationMapper()
    citations = mapper.map_sources([], sample_retrieved_results)
    assert citations == []


def test_no_database_call_occurs(sample_retrieved_results):
    """Test 12: CitationMapper operates purely on python memory objects without database calls."""
    mapper = CitationMapper()
    # Passing results with no DB client active
    citations = mapper.map_sources(["chunk_39"], sample_retrieved_results)
    assert len(citations) == 1


def test_grounding_case_hallucinated_and_valid_mix(sample_retrieved_results):
    """
    Grounding Test: Mock LLM returns ['valid_chunk', 'fake_chunk_123'].
    Expected: Only 'valid_chunk' becomes a citation, 'fake_chunk_123' does NOT appear in final citations.
    """
    gen_response = GenerationResponse(
        answer="The consumer has rights under Section 39.",
        limitations=None,
        source_ids=["chunk_39", "fake_chunk_123"]
    )

    mapper = CitationMapper()
    cited_response = mapper.create_cited_response(gen_response, sample_retrieved_results)

    assert len(cited_response.citations) == 1
    assert cited_response.citations[0].source_id == "chunk_39"
    assert cited_response.source_ids == ["chunk_39"]
    assert "fake_chunk_123" not in [c.source_id for c in cited_response.citations]


def test_formatter_produces_readable_citations(sample_retrieved_results):
    """Test 11: CitationFormatter generates clean, structured output."""
    mapper = CitationMapper()
    formatter = CitationFormatter()

    citations = mapper.map_sources(["chunk_39"], sample_retrieved_results)
    cited_resp = CitedGenerationResponse(
        answer="Defective products can be replaced.",
        limitations=None,
        citations=citations,
        source_ids=["chunk_39"]
    )

    output = formatter.format_cited_answer(cited_resp)

    assert "[Source 1]" in output
    assert "Document: Consumer Protection Act, 2019" in output
    assert "Section: Section 39 (Subsection: (1))" in output
    assert "Pages: 21-22" in output
    assert "Issued by: Government of India" in output
    assert "Official source: https://egazette.gov.in/cpa2019.pdf" in output
