import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.integrations.rag_client import RAGClient
from app.schemas.rag import RAGQueryResponse
from app.utils.exceptions import RAGServiceError


@pytest.mark.asyncio
async def test_successful_rag_request_and_forwarding():
    """1, 2, 3, 4: Successful request, correct payload forwarding, parsing, & citation parsing."""
    client = RAGClient(base_url="http://mock-rag:8000", timeout=5.0)

    mock_response_data = {
        "query": "What rights does a consumer have?",
        "answer": "Consumers have the right to protection against unfair trade practices.",
        "limitations": None,
        "citations": [
            {
                "source_id": "consumer_protection_act_2019_section_2_10",
                "document_id": "consumer_protection_act_2019",
                "document_title": "Consumer Protection Act, 2019",
                "document_type": "law",
                "issuing_authority": "Parliament of India",
                "chapter": "Chapter I",
                "section": "Section 2",
                "page_start": 5,
                "page_end": 6,
                "source_url": "https://example.gov.in/cpa.pdf",
            }
        ],
        "retrieval": {
            "candidate_k": 10,
            "top_k": 5,
            "results": []
        }
    }

    async def mock_post(url, json, headers):
        # Verify correct payload forwarding
        assert json["query"] == "What rights does a consumer have?"
        assert json["top_k"] == 5
        assert json["candidate_k"] == 10
        assert json["document_type"] == "law"

        return httpx.Response(200, json=mock_response_data)

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        res = await client.query(
            query="What rights does a consumer have?",
            top_k=5,
            candidate_k=10,
            document_type="law",
        )

        assert res.query == "What rights does a consumer have?"
        assert "Consumers have the right" in res.answer
        assert len(res.citations) == 1
        assert res.citations[0].source_id == "consumer_protection_act_2019_section_2_10"
        assert res.citations[0].document_title == "Consumer Protection Act, 2019"
        assert res.citations[0].section == "Section 2"
        assert res.citations[0].page_start == 5


@pytest.mark.asyncio
async def test_rag_timeout_raises_error_when_configured():
    """5: RAG request timeout behavior."""
    client = RAGClient(base_url="http://mock-rag:8000", timeout=0.1, raise_on_error=True)

    async def mock_post_timeout(url, json, headers):
        raise httpx.TimeoutException("Connection timed out")

    with patch("httpx.AsyncClient.post", side_effect=mock_post_timeout):
        with pytest.raises(RAGServiceError) as exc_info:
            await client.query("Sample query")
        assert exc_info.value.status_code == 502
        assert "timed out" in exc_info.value.message


@pytest.mark.asyncio
async def test_rag_service_unavailable_handling():
    """6: RAG service unavailable handling."""
    client = RAGClient(base_url="http://mock-rag:8000", raise_on_error=True)

    async def mock_post_conn_refused(url, json, headers):
        raise httpx.ConnectError("Connection refused")

    with patch("httpx.AsyncClient.post", side_effect=mock_post_conn_refused):
        with pytest.raises(RAGServiceError) as exc_info:
            await client.query("Sample query")
        assert exc_info.value.status_code == 502
        assert "Failed to connect" in exc_info.value.message


@pytest.mark.asyncio
async def test_rag_returns_500_error():
    """7: RAG returns HTTP 500 status."""
    client = RAGClient(base_url="http://mock-rag:8000", raise_on_error=True)

    async def mock_post_500(url, json, headers):
        return httpx.Response(500, text="Internal Server Error in RAG Pipeline")

    with patch("httpx.AsyncClient.post", side_effect=mock_post_500):
        with pytest.raises(RAGServiceError) as exc_info:
            await client.query("Sample query")
        assert exc_info.value.status_code == 502
        assert "error status 500" in exc_info.value.message


@pytest.mark.asyncio
async def test_rag_returns_invalid_response_json():
    """8: Invalid response JSON structure handling."""
    client = RAGClient(base_url="http://mock-rag:8000", raise_on_error=True)

    async def mock_post_invalid(url, json, headers):
        return httpx.Response(200, text="Not a JSON payload")

    with patch("httpx.AsyncClient.post", side_effect=mock_post_invalid):
        with pytest.raises(RAGServiceError) as exc_info:
            await client.query("Sample query")
        assert exc_info.value.status_code == 502


@pytest.mark.asyncio
async def test_rag_empty_answer_handling():
    """9: Empty answer handling."""
    client = RAGClient(base_url="http://mock-rag:8000", raise_on_error=False)

    async def mock_post_empty(url, json, headers):
        return httpx.Response(200, json={"query": "Sample", "answer": "", "citations": []})

    with patch("httpx.AsyncClient.post", side_effect=mock_post_empty):
        res = await client.query("Sample")
        assert res.answer == ""


@pytest.mark.asyncio
async def test_authentication_bearer_token_forwarding():
    """10: RAG Client API key header inclusion."""
    client = RAGClient(base_url="http://mock-rag:8000", api_key="secret-rag-key")

    async def mock_post_headers(url, json, headers):
        assert headers["Authorization"] == "Bearer secret-rag-key"
        return httpx.Response(200, json={"query": "Sample", "answer": "Authenticated response", "citations": []})

    with patch("httpx.AsyncClient.post", side_effect=mock_post_headers):
        res = await client.query("Sample")
        assert res.answer == "Authenticated response"


@pytest.mark.asyncio
async def test_rag_client_query_fallback():
    client = RAGClient(base_url="http://non-existent-rag-url:9999", timeout=1.0)
    res = await client.query_legal_knowledge(
        query="How to file RTI for road repair in Bangalore?",
        jurisdiction="Karnataka",
        category="RTI",
    )
    assert res is not None
    assert len(res.answer) > 20
    assert len(res.citations) > 0


@pytest.mark.asyncio
async def test_rag_client_generate_document_fallback():
    client = RAGClient(base_url="http://non-existent-rag-url:9999", timeout=1.0)
    res = await client.generate_complaint_document(
        document_type="consumer_complaint",
        applicant_details={"name": "Priya Sen"},
        respondent_details={"name": "ABC Airlines"},
        facts_and_events=["Flight cancelled without refund"],
        grievance_description="Ticket amount of Rs 8,000 not refunded after flight cancellation.",
        relief_sought=["Full refund", "Compensation Rs 5,000"],
        jurisdiction="West Bengal",
    )
    assert res is not None
    assert "Draft" in res.document_title
    assert "Priya Sen" in res.content_markdown
    assert len(res.filing_instructions) > 0
