"""
Unit and grounding tests for Stage 5A Grounded Answer Generation.
Mocks the LLM API calls to run 100% offline and fast.
"""
import json
from unittest.mock import MagicMock, patch
import pytest

from rag.app.generation.context_builder import ContextBuilder
from rag.app.generation.generator import Generator
from rag.app.generation.llm_client import LLMClient
from rag.app.generation.models import GenerationResponse
from rag.app.generation.prompts import GROUNDED_SYSTEM_PROMPT, build_user_prompt
from rag.app.retrieval.models import RetrievalResult


@pytest.fixture
def sample_retrieved_results():
    return [
        RetrievalResult(
            chunk_id="doc1_chunk_39",
            document_id="consumer_protection_act_2019",
            document_title="Consumer Protection Act, 2019",
            document_type="law",
            issuing_authority="Government of India",
            section="Section 39",
            page_start=21,
            page_end=22,
            text="Section 39 provides that the District Commission may order removal of defects in goods or replacement with new goods.",
            similarity_score=0.85,
            rerank_score=0.92
        ),
        RetrievalResult(
            chunk_id="doc1_chunk_83",
            document_id="consumer_protection_act_2019",
            document_title="Consumer Protection Act, 2019",
            document_type="law",
            issuing_authority="Government of India",
            section="Section 83",
            page_start=31,
            page_end=32,
            text="Section 83 states that a product liability action may be brought by a complainant for harm caused by a defective product.",
            similarity_score=0.80,
            rerank_score=0.88
        )
    ]


def test_context_builder_formatting_and_metadata_preservation(sample_retrieved_results):
    """Test 1 & 2: Context builder formats blocks cleanly and preserves metadata."""
    builder = ContextBuilder()
    context_text, valid_chunk_ids = builder.build_context(sample_retrieved_results)

    assert "Consumer Protection Act, 2019" in context_text
    assert "Section 39" in context_text
    assert "Section 83" in context_text
    assert "Pages: 21-22" in context_text
    assert valid_chunk_ids == ["doc1_chunk_39", "doc1_chunk_83"]


def test_prompt_structure():
    """Test 3 & 4: Grounded user prompt contains question and context."""
    question = "What can I do if I receive a defective product?"
    context = "Section 39 text..."
    prompt = build_user_prompt(question, context)

    assert "USER QUESTION:\nWhat can I do if I receive a defective product?" in prompt
    assert "RETRIEVED SOURCES:\nSection 39 text..." in prompt


def test_generator_sends_correct_prompt_and_returns_response(sample_retrieved_results):
    """Test 5 & 6: Generator sends system/user prompts and parses valid LLM JSON output."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.return_value = json.dumps({
        "answer": "Under Section 39, a consumer can get defective goods replaced or repaired. Under Section 83, they can file a product liability action.",
        "limitations": None,
        "source_ids": ["doc1_chunk_39", "doc1_chunk_83"]
    })

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("What remedies exist for defective products?", sample_retrieved_results)

    assert isinstance(resp, GenerationResponse)
    assert "Section 39" in resp.answer
    assert resp.source_ids == ["doc1_chunk_39", "doc1_chunk_83"]
    assert resp.limitations is None

    mock_client.generate.assert_called_once()
    call_args = mock_client.generate.call_args[1]
    assert call_args["system_prompt"] == GROUNDED_SYSTEM_PROMPT
    assert "Section 39" in call_args["user_prompt"]


def test_hallucinated_source_ids_rejection(sample_retrieved_results):
    """Test 7: Generator rejects/removes hallucinated source IDs not present in context."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.return_value = json.dumps({
        "answer": "Referred to Section 39.",
        "limitations": None,
        "source_ids": ["doc1_chunk_39", "fake_chunk_id_999", "invented_source_abc"]
    })

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("Query?", sample_retrieved_results)

    # Only doc1_chunk_39 is valid; fake_chunk_id_999 and invented_source_abc must be stripped!
    assert resp.source_ids == ["doc1_chunk_39"]


def test_empty_retrieved_context_handling():
    """Test 8: Generator handles empty context list without calling LLM."""
    mock_client = MagicMock(spec=LLMClient)
    generator = Generator(llm_client=mock_client)

    resp = generator.generate("What is Section 100?", [])

    assert "do not provide enough information" in resp.answer
    assert resp.source_ids == []
    mock_client.generate.assert_not_called()


def test_llm_api_error_handling(sample_retrieved_results):
    """Test 9: Generator handles network/API exceptions gracefully."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.side_effect = Exception("API connection error test")

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("Question?", sample_retrieved_results)

    assert "error occurred" in resp.answer.lower()
    assert "API connection error test" in resp.limitations
    assert resp.source_ids == []


def test_grounding_case_directly_supported(sample_retrieved_results):
    """Grounding Test 1: Question directly supported by context produces clear answer."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.return_value = json.dumps({
        "answer": "According to Section 39, the District Commission can order the removal of defects or replacement of goods.",
        "limitations": None,
        "source_ids": ["doc1_chunk_39"]
    })

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("What can the District Commission order?", sample_retrieved_results)

    assert "Section 39" in resp.answer
    assert resp.source_ids == ["doc1_chunk_39"]


def test_grounding_case_unsupported_question(sample_retrieved_results):
    """Grounding Test 2: Question asks for info NOT in retrieved context -> explicit limitation."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.return_value = json.dumps({
        "answer": "The available retrieved legal sources do not state the exact tax rate on imported goods.",
        "limitations": "The retrieved chunks only cover consumer defect remedies and product liability, not customs tax rates.",
        "source_ids": []
    })

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("What is the customs import tax rate for laptops?", sample_retrieved_results)

    assert "do not state" in resp.answer.lower() or "do not provide" in resp.answer.lower()
    assert resp.limitations is not None
    assert resp.source_ids == []


def test_grounding_case_no_invented_sections(sample_retrieved_results):
    """Grounding Test 3: Context contains Section 39 and Section 83 -> answer does not invent Section 50."""
    mock_client = MagicMock(spec=LLMClient)
    mock_client.generate.return_value = json.dumps({
        "answer": "Based on Section 39 and Section 83, defective products give rise to replacement remedies or product liability claims.",
        "limitations": None,
        "source_ids": ["doc1_chunk_39", "doc1_chunk_83"]
    })

    generator = Generator(llm_client=mock_client)
    resp = generator.generate("How to handle defective goods?", sample_retrieved_results)

    assert "Section 39" in resp.answer
    assert "Section 83" in resp.answer
    assert "Section 50" not in resp.answer
