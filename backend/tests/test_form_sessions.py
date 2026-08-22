from fastapi.testclient import TestClient


def test_form_session_flow_and_completion(client: TestClient, auth_headers: dict):
    # 1. Create a new RTI form session
    create_payload = {
        "form_type": "rti_application",
        "title": "RTI for Road Repair Sanction Orders",
        "jurisdiction": "Karnataka",
        "initial_input": "I need copies of road repair contracts sanctioned in Ward 150 Bangalore.",
    }
    res = client.post("/api/v1/form-sessions", json=create_payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["success"] is True
    session_id = data["data"]["id"]
    assert data["data"]["form_type"] == "rti_application"
    assert data["data"]["current_step"] == 1

    # 2. Get form session details and step 1 guidance
    get_res = client.get(f"/api/v1/form-sessions/{session_id}", headers=auth_headers)
    assert get_res.status_code == 200
    session_data = get_res.json()["data"]
    assert session_data["next_step_guidance"] is not None
    assert session_data["next_step_guidance"]["step_number"] == 1

    # 3. Submit Step 1 data
    step1_payload = {
        "field_updates": {
            "public_authority_name": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
            "department": "Road Infrastructure Division",
            "jurisdiction_state": "Karnataka",
        },
        "user_response": "I want information from the BBMP Road Infrastructure Division.",
    }
    step1_res = client.post(f"/api/v1/form-sessions/{session_id}/steps", json=step1_payload, headers=auth_headers)
    assert step1_res.status_code == 200
    s1_data = step1_res.json()["data"]
    assert s1_data["current_step"] == 2
    assert s1_data["collected_data"]["public_authority_name"] == "Bruhat Bengaluru Mahanagara Palike (BBMP)"

    # 4. Submit Step 2 data
    step2_payload = {
        "field_updates": {
            "information_description": "Certified copies of sanction order and contractor payment logs for Bellandur main road repair.",
            "time_period_covered": "April 2024 to December 2024",
        }
    }
    step2_res = client.post(f"/api/v1/form-sessions/{session_id}/steps", json=step2_payload, headers=auth_headers)
    assert step2_res.status_code == 200
    assert step2_res.json()["data"]["current_step"] == 3

    # 5. Complete session (auto creates complaint/draft record)
    comp_res = client.post(f"/api/v1/form-sessions/{session_id}/complete", headers=auth_headers)
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert comp_data["status"] == "completed"
    assert comp_data["complaint_id"] is not None
