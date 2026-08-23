"""
Live End-to-End Integration Test for RTI Drafting Agent.
Communicates through Main FastAPI Backend -> RAG Microservice -> Real LLM API.
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

from app.main import app

from dotenv import load_dotenv
load_dotenv("rag/.env")
load_dotenv(".env")

client = TestClient(app)


def test_e2e_rti_drafting_live_pipeline():
    """
    Executes live RTI Drafting Agent queries through the FastAPI endpoint POST /api/v1/rti/draft.
    """
    api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        pytest.skip("LLM_API_KEY not configured in environment. Skipping live LLM integration test.")

    print("\n" + "=" * 80)
    print("STARTING LIVE END-TO-END RTI DRAFTING AGENT INTEGRATION TESTS")
    print("=" * 80 + "\n")

    test_cases = [
        (
            "TEST 1 (Road Repairs)",
            "I want to know how much money my municipality spent on road repairs in my area.",
            None,
            None,
            "Municipal Corporation",
            "road repairs",
            True  # Expect RTI draft format
        ),
        (
            "TEST 2 (Government Project Expenditure)",
            "I want copies of records showing expenditure on a government project.",
            None,
            None,
            "Public Works Department",
            "expenditure",
            True
        ),
        (
            "TEST 3 (Ward 5 Streetlights)",
            "I want to know how many streetlights were installed in Ward 5.",
            "Sunita Verma",
            "House 42, Ward 5, Delhi",
            "Municipal Corporation of Delhi",
            "Ward 5",
            True
        ),
        (
            "TEST 4 (RTI Appeal Question - Informational)",
            "Can I appeal if my RTI request is rejected?",
            None,
            None,
            None,
            "appeal",
            False  # Expect grounded informational Q&A answer, NOT RTI draft template
        ),
        (
            "TEST 5 (Negative Test - PIO Details Missing)",
            "Write an RTI application and tell me the exact PIO name and address.",
            None,
            None,
            None,
            "Public Information Officer",
            True
        ),
    ]

    for label, user_req, name, addr, authority, expected_keyword, is_draft in test_cases:
        print(f"[{label}] Request: \"{user_req}\"")

        payload = {"request": user_req}
        if name:
            payload["applicant_name"] = name
        if addr:
            payload["applicant_address"] = addr
        if authority:
            payload["public_authority"] = authority

        response = client.post("/api/v1/rti/draft", json=payload)
        assert response.status_code == 200, f"Failed HTTP {response.status_code}: {response.text}"

        res_json = response.json()
        assert res_json["success"] is True
        data = res_json["data"]

        draft_text = data["draft"]
        limitations = data.get("limitations")
        citations = data.get("citations", [])

        print("-" * 80)
        print("GENERATED RESPONSE:")
        print(draft_text[:400] + ("..." if len(draft_text) > 400 else ""))
        if limitations:
            print(f"\nLIMITATIONS:\n{limitations}")
        print(f"\nVERIFIED CITATIONS ({len(citations)}):")
        for c in citations:
            print(f"  • [{c.get('source_id')}] {c.get('document_title')} | Section: {c.get('section')} | Pages: {c.get('page_start')}-{c.get('page_end')}")

        if is_draft:
            assert "[Public Information Officer]" in draft_text or "Public Information Officer" in draft_text
            assert expected_keyword.lower() in draft_text.lower()
        else:
            # Informational query should NOT force an RTI Application template header
            assert "RTI APPLICATION" not in draft_text or "appeal" in draft_text.lower()
            assert expected_keyword.lower() in draft_text.lower()

        if "PIO name" in user_req or "exact PIO" in user_req:
            assert limitations is not None, "Negative test expected limitations statement regarding missing PIO details"

        print("=" * 80 + "\n")
