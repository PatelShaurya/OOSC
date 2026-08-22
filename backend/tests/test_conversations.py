from fastapi.testclient import TestClient


def test_conversation_lifecycle_and_messaging(client: TestClient, auth_headers: dict):
    # 1. Create a conversation
    create_payload = {
        "title": "Property Dispute Query",
        "category": "tenancy",
        "jurisdiction": "Delhi",
        "initial_message": "My landlord is withholding my security deposit without reason. What legal notice can I send?",
    }
    response = client.post("/api/v1/conversations", json=create_payload, headers=auth_headers)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    conv_id = res_data["data"]["id"]
    assert conv_id is not None

    # 2. Get conversation detail (should contain user message and assistant reply with citations)
    detail_res = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["success"] is True
    assert len(detail_data["data"]["messages"]) >= 2

    # Check that assistant response has citations
    assistant_msg = detail_data["data"]["messages"][1]
    assert assistant_msg["role"] == "assistant"
    assert len(assistant_msg["citations"]) > 0

    # 3. Send a follow-up message
    msg_payload = {
        "content": "What is the time period under the Rent Control Act or Consumer Forum to reply?",
        "language": "en",
    }
    msg_res = client.post(f"/api/v1/conversations/{conv_id}/messages", json=msg_payload, headers=auth_headers)
    assert msg_res.status_code == 200
    msg_data = msg_res.json()
    assert msg_data["success"] is True
    assert msg_data["data"]["role"] == "assistant"
    assert len(msg_data["data"]["citations"]) > 0
    new_msg_id = msg_data["data"]["id"]

    # 4. Submit feedback on message
    feedback_payload = {
        "feedback": "thumbs_up",
        "feedback_notes": "Very helpful citation!",
    }
    fb_res = client.post(
        f"/api/v1/conversations/{conv_id}/messages/{new_msg_id}/feedback",
        json=feedback_payload,
        headers=auth_headers,
    )
    assert fb_res.status_code == 200
    assert fb_res.json()["success"] is True

    # 5. List conversations
    list_res = client.get("/api/v1/conversations", headers=auth_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 6. Update conversation
    update_res = client.patch(
        f"/api/v1/conversations/{conv_id}",
        json={"title": "Updated Tenancy Dispute"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["title"] == "Updated Tenancy Dispute"

    # 7. Delete conversation
    del_res = client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert del_res.status_code == 200
    assert del_res.json()["data"]["deleted"] is True
