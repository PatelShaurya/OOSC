"""
Unit tests for Stage 4B metadata filtering.
"""
from unittest.mock import MagicMock, patch, ANY
import numpy as np
import pytest

from rag.app.embeddings.embedder import BGEEmbedder
from rag.app.retrieval.models import RetrievalResponse
from rag.app.retrieval.retriever import SemanticRetriever
from rag.app.vector_store.supabase_vector import SupabaseVectorStore


@pytest.fixture
def mock_embedder():
    with patch("rag.app.embeddings.embedder.SentenceTransformer") as mock_st_cls:
        mock_model = MagicMock()
        mock_model.encode.return_value = np.ones((1, 1024), dtype=np.float32) / np.sqrt(1024)
        mock_st_cls.return_value = mock_model
        embedder = BGEEmbedder(model_name="BAAI/bge-m3", device="cpu")
        yield embedder


@pytest.fixture
def sample_chunks():
    return [
        {
            "chunk_id": "c1",
            "document_id": "doc_law_1",
            "document_type": "law",
            "issuing_authority": "Government of India",
            "content": "Content of law 1",
            "similarity_score": 0.90
        },
        {
            "chunk_id": "c2",
            "document_id": "doc_scheme_1",
            "document_type": "scheme",
            "issuing_authority": "Ministry of Consumer Affairs",
            "content": "Content of scheme 1",
            "similarity_score": 0.85
        },
        {
            "chunk_id": "c3",
            "document_id": "doc_law_2",
            "document_type": "law",
            "issuing_authority": "Government of India",
            "content": "Content of law 2",
            "similarity_score": 0.80
        }
    ]


def test_no_filter_returns_all_document_types(mock_embedder, sample_chunks):
    """Test 1: Unfiltered query returns results across all document types."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    with patch.object(retriever, "_local_search_fallback", return_value=sample_chunks):
        resp = retriever.retrieve("consumer rights", top_k=5)
        assert len(resp.results) == 3


def test_filter_by_document_type(mock_embedder, sample_chunks):
    """Test 2: document_type filter returns only matching document types."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    law_chunks = [c for c in sample_chunks if c["document_type"] == "law"]
    with patch.object(retriever, "_local_search_fallback", return_value=law_chunks) as mock_fallback:
        resp = retriever.retrieve("consumer rights", top_k=5, document_type="law")
        assert len(resp.results) == 2
        assert all(r.document_type == "law" for r in resp.results)
        mock_fallback.assert_called_with(ANY, 5, None, "law", None)


def test_filter_by_document_id(mock_embedder, sample_chunks):
    """Test 3: document_id filter returns only chunks matching document_id."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    doc_chunks = [c for c in sample_chunks if c["document_id"] == "doc_law_1"]
    with patch.object(retriever, "_local_search_fallback", return_value=doc_chunks):
        resp = retriever.retrieve("consumer rights", top_k=5, document_id="doc_law_1")
        assert len(resp.results) == 1
        assert resp.results[0].document_id == "doc_law_1"


def test_filter_by_issuing_authority(mock_embedder, sample_chunks):
    """Test 4: issuing_authority filter returns only matching issuing authority."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    auth_chunks = [c for c in sample_chunks if c["issuing_authority"] == "Ministry of Consumer Affairs"]
    with patch.object(retriever, "_local_search_fallback", return_value=auth_chunks):
        resp = retriever.retrieve("scheme query", top_k=5, issuing_authority="Ministry of Consumer Affairs")
        assert len(resp.results) == 1
        assert resp.results[0].issuing_authority == "Ministry of Consumer Affairs"


def test_multiple_combined_filters(mock_embedder, sample_chunks):
    """Test 5: Combining document_id, document_type, and issuing_authority filters."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    filtered_chunks = [
        c for c in sample_chunks
        if c["document_id"] == "doc_law_1" and c["document_type"] == "law" and c["issuing_authority"] == "Government of India"
    ]
    with patch.object(retriever, "_local_search_fallback", return_value=filtered_chunks):
        resp = retriever.retrieve(
            "rights",
            top_k=5,
            document_id="doc_law_1",
            document_type="law",
            issuing_authority="Government of India"
        )
        assert len(resp.results) == 1
        assert resp.results[0].chunk_id == "c1"


def test_filter_no_matching_documents(mock_embedder):
    """Test 6: Filter matching zero documents returns empty RetrievalResponse safely."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    with patch.object(retriever, "_local_search_fallback", return_value=[]):
        resp = retriever.retrieve("query", top_k=5, document_id="non_existent_doc")
        assert resp.results == []


def test_top_k_and_sorting_preserved_with_filters(mock_embedder, sample_chunks):
    """Test 7 & 8: top_k limit and descending score sorting are preserved under filtering."""
    mock_store = MagicMock(spec=SupabaseVectorStore)
    mock_store.is_connected.return_value = False
    retriever = SemanticRetriever(embedder=mock_embedder, vector_store=mock_store)

    with patch.object(retriever, "_local_search_fallback", return_value=sample_chunks[:2]):
        resp = retriever.retrieve("query", top_k=2, document_type="law")
        assert len(resp.results) == 2
        scores = [r.similarity_score for r in resp.results]
        assert scores == sorted(scores, reverse=True)
