"""
Unit tests for RAGPipeline RTI Drafting mode and prompt formatting.
"""
from unittest.mock import MagicMock
import pytest

from rag.app.api.models import RAGQueryRequest
from rag.app.generation.prompts import RTI_DRAFT_SYSTEM_PROMPT, build_rti_user_prompt
from rag.app.pipeline import RAGPipeline
from rag.app.retrieval.models import RetrievalResponse, RetrievalResult


def test_build_rti_user_prompt():
    """Verify prompt formatting incorporates request and placeholders."""
    prompt = build_rti_user_prompt(
        question="I want to know how much money was spent on road repairs in Ward 12.",
        context_text="[Section 6(1)] Information request procedure...",
        applicant_name=None,
        applicant_address=None,
        public_authority="Municipal Corporation",
    )

    assert "I want to know how much money was spent on road repairs in Ward 12." in prompt
    assert "Municipal Corporation" in prompt
    assert "[Applicant Name]" in prompt
    assert "[Applicant Address]" in prompt
    assert "Section 6(1)" in prompt


def test_rag_pipeline_rti_drafting_mode():
    """Verify RAGPipeline passes mode and applicant details to generator."""
    mock_retriever = MagicMock()
    mock_generator = MagicMock()
    mock_mapper = MagicMock()

    mock_retriever.retrieve.return_value = RetrievalResponse(
        query="I want to know expenditure on road repairs",
        top_k=5,
        results=[
            RetrievalResult(
                chunk_id="rti_act_2005_section_6_38",
                document_id="RTI_Act_2005",
                document_title="Right to Information Act, 2005",
                text="Section 6(1)...",
                page_start=10,
                page_end=11,
                similarity_score=0.9,
                rerank_score=0.95,
            )
        ]
    )

    mock_generator.generate.return_value = MagicMock(
        answer="RTI APPLICATION\n\nTo:\n[PIO]\n[Public Authority]\n\nSubject: Road repairs...",
        limitations="None",
        source_ids=["rti_act_2005_section_6_38"],
    )

    mock_mapper.create_cited_response.return_value = MagicMock(
        answer="RTI APPLICATION\n\nTo:\n[PIO]\n[Public Authority]\n\nSubject: Road repairs...",
        what_we_understood="Expenditure request",
        what_you_can_do=[],
        what_you_need=[],
        next_step="Submit RTI application",
        limitations="None",
        citations=[],
    )

    pipeline = RAGPipeline(
        retriever=mock_retriever,
        generator=mock_generator,
        citation_mapper=mock_mapper,
    )

    resp = pipeline.query(
        query="I want to know expenditure on road repairs",
        mode="rti_draft",
        applicant_name="Anita Sharma",
        public_authority="PWD Delhi",
    )

    # Verify document_type was defaulted to 'law'
    mock_retriever.retrieve.assert_called_once_with(
        query="I want to know expenditure on road repairs",
        candidate_k=10,
        top_k=5,
        document_id=None,
        document_type="law",
        issuing_authority=None,
    )

    # Verify generator received RTI mode and details
    mock_generator.generate.assert_called_once()
    _, kwargs = mock_generator.generate.call_args
    assert kwargs["mode"] == "rti_draft"
    assert kwargs["applicant_name"] == "Anita Sharma"
    assert kwargs["public_authority"] == "PWD Delhi"
