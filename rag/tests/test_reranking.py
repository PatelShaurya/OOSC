"""
Unit tests for Stage 4C Cross-Encoder Reranking and RerankedRetriever pipeline.
Uses mocking so tests run quickly offline without downloading heavy model weights.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from rag.app.reranking.models import RerankedResponse
from rag.app.reranking.reranker import CrossEncoderReranker, RerankedRetriever
from rag.app.retrieval.models import RetrievalResult, RetrievalResponse
from rag.app.retrieval.retriever import SemanticRetriever


@pytest.fixture
def sample_candidates():
    return [
        RetrievalResult(
            chunk_id="c1",
            document_id="doc_1",
            document_title="Consumer Protection Act, 2019",
            section="Section 2",
            page_start=3,
            page_end=4,
            text="Definitions under Section 2",
            similarity_score=0.75
        ),
        RetrievalResult(
            chunk_id="c2",
            document_id="doc_1",
            document_title="Consumer Protection Act, 2019",
            section="Section 39",
            page_start=21,
            page_end=22,
            text="Remedies for defective goods under Section 39",
            similarity_score=0.85
        ),
        RetrievalResult(
            chunk_id="c3",
            document_id="doc_1",
            document_title="Consumer Protection Act, 2019",
            section="Section 83",
            page_start=31,
            page_end=31,
            text="Product liability action for defective product under Section 83",
            similarity_score=0.80
        )
    ]


@pytest.fixture
def mock_cross_encoder():
    with patch("rag.app.reranking.reranker.CrossEncoder") as mock_ce_cls:
        mock_instance = MagicMock()
        # Mock predict method returning custom rerank scores
        mock_instance.predict.side_effect = lambda pairs, show_progress_bar=False: np.array([
            2.5 if "Section 39" in p[1] else (3.8 if "Section 83" in p[1] else 0.2)
            for p in pairs
        ])
        mock_ce_cls.return_value = mock_instance
        reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3", device="cpu")
        yield reranker


def test_reranker_initialization(mock_cross_encoder):
    """Test 1: Verify reranker model initializes with specified device and model name."""
    assert mock_cross_encoder.device == "cpu"
    assert mock_cross_encoder.model is not None


def test_query_candidate_pair_creation_and_scoring(mock_cross_encoder, sample_candidates):
    """Test 2 & 3: Verify pair creation [query, text] and reranker score calculation."""
    query = "defective product remedies"
    reranked = mock_cross_encoder.rerank(query=query, results=sample_candidates, top_k=5)
    
    assert len(reranked) == 3
    for r in reranked:
        assert r.rerank_score is not None
        assert isinstance(r.rerank_score, float)


def test_results_sorted_by_reranker_score_descending(mock_cross_encoder, sample_candidates):
    """Test 4: Verify results are re-sorted strictly by rerank_score in descending order."""
    query = "defective product remedies"
    reranked = mock_cross_encoder.rerank(query=query, results=sample_candidates, top_k=5)

    scores = [r.rerank_score for r in reranked]
    assert scores == sorted(scores, reverse=True)
    # Based on mock: Section 83 gets 3.8, Section 39 gets 2.5, Section 2 gets 0.2
    assert reranked[0].section == "Section 83"
    assert reranked[1].section == "Section 39"
    assert reranked[2].section == "Section 2"


def test_top_k_respected_in_reranker(mock_cross_encoder, sample_candidates):
    """Test 5: Verify top_k parameter truncates output count correctly."""
    query = "defective product"
    reranked = mock_cross_encoder.rerank(query=query, results=sample_candidates, top_k=2)
    assert len(reranked) == 2


def test_candidate_k_and_top_k_pipeline_flow(mock_cross_encoder, sample_candidates):
    """Test 6: Verify candidate_k retrieval and top_k reranking flow in RerankedRetriever."""
    mock_semantic = MagicMock(spec=SemanticRetriever)
    mock_semantic.retrieve.return_value = RetrievalResponse(
        query="defective product",
        top_k=10,
        results=sample_candidates
    )

    pipeline = RerankedRetriever(semantic_retriever=mock_semantic, reranker=mock_cross_encoder)
    response = pipeline.retrieve(query="defective product", candidate_k=10, top_k=2)

    assert isinstance(response, RerankedResponse)
    assert response.candidate_k == 10
    assert response.top_k == 2
    assert len(response.results) == 2
    mock_semantic.retrieve.assert_called_once_with(
        query="defective product",
        top_k=10,
        document_id=None,
        document_type=None,
        issuing_authority=None
    )


def test_metadata_preservation(mock_cross_encoder, sample_candidates):
    """Test 7: Verify all metadata fields (document_title, section, page_start, page_end) are preserved."""
    reranked = mock_cross_encoder.rerank(query="defective product", results=sample_candidates, top_k=3)
    item = next(r for r in reranked if r.chunk_id == "c2")

    assert item.document_title == "Consumer Protection Act, 2019"
    assert item.section == "Section 39"
    assert item.page_start == 21
    assert item.page_end == 22


def test_similarity_score_preservation(mock_cross_encoder, sample_candidates):
    """Test 8: Verify original semantic similarity_score is preserved alongside rerank_score."""
    reranked = mock_cross_encoder.rerank(query="defective product", results=sample_candidates, top_k=3)
    item = next(r for r in reranked if r.chunk_id == "c2")

    assert item.similarity_score == 0.85
    assert item.rerank_score == 2.5


def test_empty_query_handling(mock_cross_encoder, sample_candidates):
    """Test 9: Verify empty query returns empty list without error."""
    resp1 = mock_cross_encoder.rerank(query="", results=sample_candidates)
    assert resp1 == []

    pipeline = RerankedRetriever(reranker=mock_cross_encoder)
    resp2 = pipeline.retrieve(query="   ", candidate_k=10, top_k=5)
    assert resp2.results == []


def test_reranker_failure_fallback(sample_candidates):
    """Test 10: Verify graceful fallback to semantic similarity order if reranker fails."""
    with patch("rag.app.reranking.reranker.CrossEncoder") as mock_ce_cls:
        mock_instance = MagicMock()
        mock_instance.predict.side_effect = Exception("Model prediction failure test")
        mock_ce_cls.return_value = mock_instance

        reranker = CrossEncoderReranker(model_name="BAAI/bge-reranker-v2-m3", device="cpu")
        reranked = reranker.rerank(query="defective product", results=sample_candidates, top_k=2)

        assert len(reranked) == 2
        # Should fallback to top 2 candidates in original order
        assert reranked[0].chunk_id == "c1"
        assert reranked[1].chunk_id == "c2"
