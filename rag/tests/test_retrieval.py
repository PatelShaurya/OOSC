"""
Unit tests for Stage 4A basic semantic retrieval.
Uses mocking to test query embedding, sorting, top_k, metadata, and error handling offline.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from rag.app.embeddings.embedder import BGEEmbedder
from rag.app.retrieval.models import RetrievalResult, RetrievalResponse
from rag.app.retrieval.retriever import SemanticRetriever
from rag.app.vector_store.supabase_vector import SupabaseVectorStore


@pytest.fixture
def mock_embedder():
    """Mock embedder producing 1024-dim L2-normalized query vectors."""
    with patch("rag.app.embeddings.embedder.SentenceTransformer") as mock_st_cls:
        mock_model = MagicMock()
        def dummy_encode(sentences, batch_size=16, show_progress_bar=False, normalize_embeddings=True):
            res = []
            for s in sentences:
                v = np.ones(1024, dtype=np.float32)
                if normalize_embeddings:
                    v = v / np.linalg.norm(v)
                res.append(v)
            return np.array(res)
        mock_model.encode.side_effect = dummy_encode
        mock_st_cls.return_value = mock_model

        embedder = BGEEmbedder(model_name="BAAI/bge-m3", device="cpu", batch_size=4)
        yield embedder


def test_query_embedding_dimension_and_normalization(mock_embedder):
    """Test 1 & 2: Verify query embedding has 1024 dimensions and is L2 normalized."""
    query = "What are consumer rights?"
    vec = mock_embedder.encode_single(query)
    assert len(vec) == 1024
    norm = np.linalg.norm(np.array(vec))
    assert pytest.approx(norm, abs=1e-4) == 1.0


def test_retriever_top_k_respected(mock_embedder):
    """Test 3: Verify top_k parameter is respected in retrieval output."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False  # Triggers local search fallback

    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)
    
    # Mock local search fallback to return 10 items
    dummy_records = [
        {"chunk_id": f"chunk_{i}", "document_id": "doc_1", "text": f"Content {i}", "similarity_score": 0.9 - (i * 0.05)}
        for i in range(10)
    ]
    with patch.object(retriever, "_local_search_fallback", return_value=dummy_records[:3]):
        resp = retriever.retrieve("defective product", top_k=3)
        assert resp.top_k == 3
        assert len(resp.results) == 3


def test_results_sorted_by_similarity_descending(mock_embedder):
    """Test 4: Verify results are sorted from highest similarity score to lowest."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False

    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    unsorted_records = [
        {"chunk_id": "c1", "document_id": "d1", "text": "Text 1", "similarity_score": 0.65},
        {"chunk_id": "c2", "document_id": "d1", "text": "Text 2", "similarity_score": 0.92},
        {"chunk_id": "c3", "document_id": "d1", "text": "Text 3", "similarity_score": 0.78},
    ]

    with patch.object(retriever, "_local_search_fallback", return_value=unsorted_records):
        resp = retriever.retrieve("unfair trade practice", top_k=5)
        scores = [r.similarity_score for r in resp.results]
        assert scores == sorted(scores, reverse=True)
        assert scores[0] == 0.92
        assert scores[-1] == 0.65


def test_metadata_preservation_in_results(mock_embedder):
    """Test 5 & 6: Verify all metadata fields and similarity scores are preserved."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False

    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    detailed_record = [{
        "chunk_id": "cpa_sec_2_1",
        "document_id": "consumer_protection_act_2019",
        "document_title": "Consumer Protection Act, 2019",
        "document_type": "law",
        "issuing_authority": "Government of India",
        "source_url": "https://example.com/act.pdf",
        "page_start": 2,
        "page_end": 4,
        "chapter": "CHAPTER I",
        "section": "Section 2",
        "parent_section": "Section 2",
        "subsection": "(1)",
        "chunk_index": 1,
        "content": "Definitions under Section 2.",
        "similarity_score": 0.885
    }]

    with patch.object(retriever, "_local_search_fallback", return_value=detailed_record):
        resp = retriever.retrieve("definitions", top_k=5)
        assert len(resp.results) == 1
        res = resp.results[0]
        assert res.chunk_id == "cpa_sec_2_1"
        assert res.document_title == "Consumer Protection Act, 2019"
        assert res.section == "Section 2"
        assert res.subsection == "(1)"
        assert res.page_start == 2
        assert res.page_end == 4
        assert res.similarity_score == 0.885
        assert res.text == "Definitions under Section 2."


def test_empty_query_handling(mock_embedder):
    """Test 7: Verify empty or whitespace query returns empty RetrievalResponse safely."""
    retriever = SemanticRetriever(embedder=mock_embedder)
    resp1 = retriever.retrieve("")
    assert resp1.results == []
    resp2 = retriever.retrieve("   ")
    assert resp2.results == []


def test_supabase_rpc_error_handling(mock_embedder):
    """Test 8: Verify Supabase RPC errors are caught cleanly and fall back gracefully."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = True

    mock_client = MagicMock()
    mock_client.rpc.side_effect = Exception("Database RPC exception test")
    mock_store.client = mock_client

    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    with patch.object(retriever, "_local_search_fallback", return_value=[]) as mock_fallback:
        resp = retriever.retrieve("complaint filing procedure", top_k=5)
        assert isinstance(resp, RetrievalResponse)
        mock_fallback.assert_called_once()
