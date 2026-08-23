"""
Unit and API contract tests for Stage 5C FastAPI REST Service.
Uses FastAPI TestClient and mocked RAGPipeline dependencies.
"""
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from rag.app.api.dependencies import set_pipeline_override, reset_pipeline_dependency
from rag.app.api.main import app
from rag.app.api.models import RAGQueryResponse, RetrievalDebugInfo
from rag.app.citations.models import Citation
from rag.app.pipeline import RAGPipeline
from rag.app.retrieval.models import RetrievalResult


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_pipeline():
    pipeline = MagicMock(spec=RAGPipeline)
    
    sample_citation = Citation(
        source_id="chunk_39",
        document_id="consumer_protection_act_2019",
        document_title="Consumer Protection Act, 2019",
        document_type="law",
        issuing_authority="Government of India",
        section="Section 39",
        page_start=21,
        page_end=22,
        source_url="https://ncdrc.nic.in/bare_acts/CPA2019.pdf"
    )

    sample_result = RetrievalResult(
        chunk_id="chunk_39",
        document_id="consumer_protection_act_2019",
        document_title="Consumer Protection Act, 2019",
        section="Section 39",
        text="Sample text...",
        similarity_score=0.85,
        rerank_score=0.92
    )

    mock_response = RAGQueryResponse(
        query="What rights does a consumer have?",
        answer="Under Section 39, a consumer has various remedies.",
        limitations="Scope limited to retrieved provisions.",
        citations=[sample_citation],
        retrieval=RetrievalDebugInfo(
            candidate_k=10,
            top_k=5,
            results=[sample_result]
        )
    )

    pipeline.query.return_value = mock_response
    set_pipeline_override(pipeline)
    yield pipeline
    reset_pipeline_dependency()


def test_root_health_endpoint(client):
    """Test GET /health returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "civicai-rag"


def test_v1_readiness_health_endpoint(client):
    """Test GET /api/v1/health returns 200 OK."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_valid_query_contract(client, mock_pipeline):
    """Test POST /api/v1/query returns 200 OK and valid RAGQueryResponse schema."""
    payload = {
        "query": "What rights does a consumer have?",
        "top_k": 5,
        "candidate_k": 10
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "What rights does a consumer have?"
    assert "Under Section 39" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["section"] == "Section 39"
    assert data["retrieval"]["top_k"] == 5

    mock_pipeline.query.assert_called_once_with(
        query="What rights does a consumer have?",
        top_k=5,
        candidate_k=10,
        document_id=None,
        document_type=None,
        issuing_authority=None,
        mode=None,
        applicant_name=None,
        applicant_address=None,
        public_authority=None
    )


def test_metadata_filters_passed_to_pipeline(client, mock_pipeline):
    """Test metadata filter parameters are correctly forwarded to pipeline."""
    payload = {
        "query": "What are consumer rights?",
        "top_k": 3,
        "candidate_k": 15,
        "document_type": "law",
        "issuing_authority": "Government of India"
    }
    response = client.post("/api/v1/query", json=payload)
    assert response.status_code == 200

    mock_pipeline.query.assert_called_once_with(
        query="What are consumer rights?",
        top_k=3,
        candidate_k=15,
        document_id=None,
        document_type="law",
        issuing_authority="Government of India",
        mode=None,
        applicant_name=None,
        applicant_address=None,
        public_authority=None
    )


def test_empty_query_validation(client):
    """Test empty or whitespace query returns 422 Unprocessable Entity."""
    response = client.post("/api/v1/query", json={"query": "   ", "top_k": 5, "candidate_k": 10})
    assert response.status_code == 422


def test_invalid_top_k_validation(client):
    """Test top_k out of range (<1 or >20) returns 422 Unprocessable Entity."""
    response1 = client.post("/api/v1/query", json={"query": "Valid", "top_k": 0, "candidate_k": 10})
    assert response1.status_code == 422

    response2 = client.post("/api/v1/query", json={"query": "Valid", "top_k": 25, "candidate_k": 30})
    assert response2.status_code == 422


def test_candidate_k_less_than_top_k_validation(client):
    """Test candidate_k < top_k returns 422 Unprocessable Entity."""
    response = client.post("/api/v1/query", json={"query": "Valid", "top_k": 10, "candidate_k": 5})
    assert response.status_code == 422


def test_pipeline_failure_error_handling(client, mock_pipeline):
    """Test pipeline exception returns 503 Service Unavailable."""
    mock_pipeline.query.side_effect = Exception("Model service timeout error")

    response = client.post("/api/v1/query", json={"query": "What is Section 2?", "top_k": 5, "candidate_k": 10})
    assert response.status_code == 503
    assert "failed or dependency service unavailable" in response.json()["detail"]
