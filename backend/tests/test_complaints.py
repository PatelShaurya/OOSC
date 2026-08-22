from fastapi.testclient import TestClient


def test_complaint_and_document_generation_flow(client: TestClient, auth_headers: dict):
    # 1. Create a complaint
    create_payload = {
        "title": "Defective Washing Machine - Refund Refusal",
        "category": "consumer",
        "jurisdiction": "New Delhi District Consumer Forum",
        "authority_or_opponent_name": "ElectroTech Retail Ltd",
        "incident_date": "2026-01-15",
        "facts_description": "Purchased front-load washing machine on 15 Jan 2026 for Rs. 42,000. Developed severe motor fault on Day 3. Technician confirmed manufacturing defect but company refused refund/replacement.",
        "relief_sought": [
            "Full refund of Rs. 42,000 with 12% interest",
            "Compensation of Rs. 20,000 for mental harassment",
            "Litigation expenses of Rs. 5,000",
        ],
        "applicant_details": {
            "name": "Amit Kumar",
            "address": "B-42, Vasant Kunj, New Delhi",
            "phone": "9876543210",
        },
        "respondent_details": {
            "name": "ElectroTech Retail Ltd",
            "address": "Connaught Place Branch, New Delhi",
        },
    }

    res = client.post("/api/v1/complaints", json=create_payload, headers=auth_headers)
    assert res.status_code == 201
    comp_id = res.json()["data"]["id"]
    assert comp_id is not None

    # 2. Get complaint details
    get_res = client.get(f"/api/v1/complaints/{comp_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "draft"

    # 3. Generate legal document draft via RAG orchestration
    gen_payload = {
        "language": "en",
        "tone": "formal_legal",
        "include_statutory_references": True,
    }
    gen_res = client.post(f"/api/v1/complaints/{comp_id}/generate-document", json=gen_payload, headers=auth_headers)
    assert gen_res.status_code == 200
    draft_data = gen_res.json()["data"]
    assert draft_data["document_title"] is not None
    assert "content_markdown" in draft_data
    assert len(draft_data["filing_instructions"]) > 0

    # 4. Verify complaint status updated to 'generated'
    chk_res = client.get(f"/api/v1/complaints/{comp_id}", headers=auth_headers)
    assert chk_res.json()["data"]["status"] == "generated"

    # 5. Export document
    export_res = client.post(f"/api/v1/complaints/{comp_id}/export?format=markdown", headers=auth_headers)
    assert export_res.status_code == 200
    export_data = export_res.json()["data"]
    assert export_data["format"] == "markdown"
    assert export_data["filename"].endswith(".md")
    assert len(export_data["content"]) > 50

    # 6. List complaints
    list_res = client.get("/api/v1/complaints?category=consumer", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 7. Update status
    update_res = client.patch(
        f"/api/v1/complaints/{comp_id}",
        json={"status": "ready_to_file"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == "ready_to_file"

    # 8. Delete complaint
    del_res = client.delete(f"/api/v1/complaints/{comp_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True
