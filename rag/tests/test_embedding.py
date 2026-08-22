"""
Unit tests for Stage 3 embedding generation and vector store integration.
Uses mock SentenceTransformer model for fast, offline unit testing.
"""
from unittest.mock import MagicMock, patch
import numpy as np
import pytest
from rag.app.embeddings.embedder import BGEEmbedder
from rag.app.vector_store.supabase_vector import SupabaseVectorStore


@pytest.fixture
def mock_embedder():
    """Returns a BGEEmbedder with mocked SentenceTransformer model producing 1024-dim vectors."""
    with patch("rag.app.embeddings.embedder.SentenceTransformer") as mock_st_cls:
        mock_model = MagicMock()

        def dummy_encode(sentences, batch_size=16, show_progress_bar=False, normalize_embeddings=True):
            # Return array of normalized 1024-dim vectors
            results = []
            for s in sentences:
                vec = np.ones(1024, dtype=np.float32)
                if normalize_embeddings:
                    vec = vec / np.linalg.norm(vec)
                results.append(vec)
            return np.array(results)

        mock_model.encode.side_effect = dummy_encode
        mock_st_cls.return_value = mock_model

        embedder = BGEEmbedder(model_name="BAAI/bge-m3", device="cpu", batch_size=4)
        yield embedder


def test_model_loads_successfully(mock_embedder):
    """Test 1: Verify model loads successfully."""
    assert mock_embedder.model is not None
    assert mock_embedder.EMBEDDING_DIM == 1024


def test_single_text_embedding_dimension(mock_embedder):
    """Test 2: Verify one text produces a 1024-dimensional embedding."""
    text = "The District Commission shall have jurisdiction to entertain complaints."
    embedding = mock_embedder.encode_single(text)
    assert len(embedding) == 1024
    assert isinstance(embedding[0], float)


def test_multiple_texts_embedding_count(mock_embedder):
    """Test 3: Verify multiple texts produce the correct number of embeddings."""
    texts = [
        "First legal chunk text.",
        "Second legal chunk text.",
        "Third legal chunk text."
    ]
    embeddings = mock_embedder.encode(texts)
    assert len(embeddings) == 3
    for emb in embeddings:
        assert len(emb) == 1024


def test_embeddings_are_normalized(mock_embedder):
    """Test 4: Verify generated embeddings are L2 normalized (norm ~ 1.0)."""
    text = "Consumer protection provisions under Section 2."
    embedding = mock_embedder.encode_single(text)
    norm = np.linalg.norm(np.array(embedding))
    assert pytest.approx(norm, abs=1e-4) == 1.0


def test_empty_text_handled_safely(mock_embedder):
    """Test 5: Verify empty and whitespace text handled safely without error."""
    embeddings = mock_embedder.encode(["", "   ", "Valid text"])
    assert len(embeddings) == 3
    assert len(embeddings[0]) == 1024
    assert len(embeddings[1]) == 1024
    assert sum(embeddings[0]) == 0.0  # Zero vector for empty text


def test_chunk_metadata_preservation():
    """Test 6 & 7: Verify chunk metadata is preserved and schema format matches database fields."""
    store = SupabaseVectorStore(supabase_url="https://fake.supabase.co", supabase_key="fakekey")
    
    chunk = {
        "chunk_id": "cpa_sec_2_1",
        "document_id": "cpa_2019",
        "document_title": "Consumer Protection Act 2019",
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
        "text": "Definitions under Section 2."
    }
    dummy_embedding = [0.1] * 1024

    record = store.prepare_chunk_record(chunk, dummy_embedding)

    assert record["chunk_id"] == "cpa_sec_2_1"
    assert record["document_id"] == "cpa_2019"
    assert record["content"] == "Definitions under Section 2."
    assert record["embedding"] == dummy_embedding
    assert record["document_title"] == "Consumer Protection Act 2019"
    assert record["page_start"] == 2
    assert record["page_end"] == 4
    assert record["section"] == "Section 2"
    assert record["parent_section"] == "Section 2"


def test_no_duplicate_records_on_reprocessing():
    """Test 8: Verify upsert uses (document_id, chunk_id) conflict handling to prevent duplicate records."""
    store = SupabaseVectorStore(supabase_url="https://fake.supabase.co", supabase_key="fakekey")
    
    # Mock supabase client
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_upsert = MagicMock()
    mock_execute = MagicMock()

    mock_client.table.return_value = mock_table
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute.return_value = mock_execute
    mock_execute.data = [{"id": 1}, {"id": 2}]

    store.client = mock_client

    records = [
        {"chunk_id": "chunk_1", "document_id": "doc_1", "content": "Text 1", "embedding": [0.0] * 1024},
        {"chunk_id": "chunk_2", "document_id": "doc_1", "content": "Text 2", "embedding": [0.0] * 1024}
    ]

    count = store.upsert_chunks(records)

    assert count == 2
    mock_table.upsert.assert_called_once_with(records, on_conflict="document_id,chunk_id")
