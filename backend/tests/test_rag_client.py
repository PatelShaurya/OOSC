import pytest
from app.integrations.rag_client import RAGClient


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
    assert res.citations[0].act_or_law_name is not None


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
