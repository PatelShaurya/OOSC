"""
End-to-End Live Integration Test for CivicAI Main Backend <-> RAG Service.
Tests live service-to-service communication across all ingested document domains:
1. Consumer Protection Act, 2019
2. PM Kisan Scheme FAQ
3. Right to Information Act, 2005
"""
import sys
import time
from pathlib import Path

# Ensure root workspace is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import get_settings


def get_e2e_settings():
    return Settings(
        PROJECT_NAME="CivicAI Backend [E2E Test]",
        ENVIRONMENT="test",
        DEBUG=True,
        SUPABASE_URL="",
        SUPABASE_KEY="",
        SUPABASE_JWT_SECRET="test-secret-key-12345",
        RAG_SERVICE_URL="http://localhost:8000",
        RAG_TIMEOUT_SECONDS=60.0,
    )


def test_e2e_live_rag_integration():
    app.dependency_overrides[get_settings] = get_e2e_settings
    client = TestClient(app)

    auth_headers = {
        "Authorization": "Bearer test-user123",
        "Content-Type": "application/json",
    }

    test_queries = [
        ("Query 1 (Consumer Rights)", "What rights does a consumer have?", "Consumer Protection"),
        ("Query 2 (PM Kisan Scheme)", "Who is eligible for PM Kisan?", "PM Kis"),
        ("Query 3 (RTI Application)", "How can I file an RTI application?", "Right to Information"),
    ]

    print("\n" + "=" * 80)
    print("STARTING LIVE END-TO-END BACKEND <-> RAG SERVICE INTEGRATION TESTS")
    print("=" * 80 + "\n")

    try:
        for tag, query_text, expected_doc_keyword in test_queries:
            print(f"[{tag}] Sending query to Main Backend: \"{query_text}\"")

            # 1. Create conversation with query
            create_payload = {
                "title": f"E2E Test: {tag}",
                "category": None,
                "jurisdiction": None,
                "initial_message": query_text,
            }

            res = client.post("/api/v1/conversations", json=create_payload, headers=auth_headers)
            assert res.status_code == 201, f"Failed to create conversation: {res.text}"
            res_data = res.json()
            assert res_data["success"] is True

            conv_id = res_data["data"]["id"]

            # 2. Retrieve conversation detail
            detail_res = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
            assert detail_res.status_code == 200
            detail_data = detail_res.json()
            messages = detail_data["data"]["messages"]

            assert len(messages) >= 2, "Expected at least user query and assistant response"

            assistant_msg = messages[1]
            assert assistant_msg["role"] == "assistant"

            answer = assistant_msg["content"]
            citations = assistant_msg["citations"]

            print("-" * 80)
            print("BACKEND RESPONSE RECEIVED:")
            print(f"Answer snippet: {answer[:250]}...")
            print(f"Total Citations Attached: {len(citations)}")
            for c in citations:
                doc_title = c.get("document_title") or c.get("document_id") or ""
                sec = c.get("section") or ""
                page_start = c.get("page_start") or ""
                page_end = c.get("page_end") or ""
                print(f"  - [{c.get('source_id')}] {doc_title} | {sec} | Pages {page_start}-{page_end}")

            assert len(answer) > 20, "Answer string must not be empty"
            assert len(citations) > 0, f"Expected verified citations for query '{query_text}'"

            # Check primary expected document presence
            matched = any(expected_doc_keyword.lower() in (c.get("document_title") or c.get("document_id") or "").lower() for c in citations)
            print(f"Primary Document Match ('{expected_doc_keyword}'): {matched}")
            assert matched, f"Expected citation matching '{expected_doc_keyword}', got: {citations}"

            print("=" * 80 + "\n")
            time.sleep(2.0)  # Inter-query pacing for LLM API limits

    finally:
        app.dependency_overrides.clear()


if __name__ == "__main__":
    test_e2e_live_rag_integration()
