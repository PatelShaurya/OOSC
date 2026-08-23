"""
Unit and integration tests for RTI Drafting Agent endpoint and service layer.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_rag_client, get_rti_service
from app.main import app
from app.schemas.rag import Citation, RAGQueryResponse
from app.services.rti_service import RTIDraftingService

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mock_rag_client():
    mock_client = MagicMock()

    async def mock_draft_rti(request_text, applicant_name=None, applicant_address=None, public_authority=None):
        if "appeal" in request_text.lower():
            # Informational question (TEST 4)
            return RAGQueryResponse(
                query=request_text,
                answer="Under Section 19 of the RTI Act 2005, if your RTI request is rejected or ignored, you can file a First Appeal within 30 days to the First Appellate Authority.",
                limitations=None,
                citations=[
                    Citation(
                        source_id="rti_act_2005_section_19",
                        document_id="RTI_Act_2005",
                        document_title="Right to Information Act, 2005",
                        document_type="law",
                        section="Section 19",
                        page_start=15,
                        page_end=16,
                    )
                ]
            )

        auth_str = public_authority or "[Public Authority]"
        name_str = applicant_name or "[Applicant Name]"
        addr_str = applicant_address or "[Applicant Address]"

        limitation_text = None
        if "pio name" in request_text.lower():
            limitation_text = "The retrieved sources do not contain specific PIO officer names or local postal addresses for municipal offices."

        draft_content = f"""RTI APPLICATION

To:
[Public Information Officer]
{auth_str}

Subject: Request for information under the Right to Information Act, 2005 regarding {request_text}

Respected Sir/Madam,

Under Section 6(1) of the Right to Information Act, 2005, I seek the following information:

1. Information regarding: {request_text}

Kindly provide the requested information within 30 days under Section 7(1).

Applicant Details:
Name: {name_str}
Address: {addr_str}
Contact: [Contact Information]

Date: [Date]
Place: [Place]"""

        return RAGQueryResponse(
            query=request_text,
            answer=draft_content,
            limitations=limitation_text,
            citations=[
                Citation(
                    source_id="rti_act_2005_section_6",
                    document_id="RTI_Act_2005",
                    document_title="Right to Information Act, 2005",
                    document_type="law",
                    section="Section 6(1)",
                    page_start=10,
                    page_end=11,
                    source_url="https://cic.gov.in/sites/default/files/RTI-Act_English.pdf",
                )
            ]
        )

    mock_client.draft_rti_application = AsyncMock(side_effect=mock_draft_rti)

    def override_get_rti_service():
        return RTIDraftingService(rag_client=mock_client)

    app.dependency_overrides[get_rti_service] = override_get_rti_service
    app.dependency_overrides[get_rag_client] = lambda: mock_client

    yield mock_client

    app.dependency_overrides.clear()


def test_rti_draft_road_repairs(setup_mock_rag_client):
    """TEST 1: Request for road repairs expenditure."""
    response = client.post(
        "/api/v1/rti/draft",
        json={"request": "I want to know how much money my municipality spent on road repairs in my area."}
    )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["success"] is True
    data = res_json["data"]

    assert "RTI APPLICATION" in data["draft"]
    assert "road repairs" in data["draft"]
    assert len(data["citations"]) > 0
    assert data["citations"][0]["document_title"] == "Right to Information Act, 2005"


def test_rti_draft_government_project(setup_mock_rag_client):
    """TEST 2: Request for government project expenditure records."""
    response = client.post(
        "/api/v1/rti/draft",
        json={"request": "I want copies of records showing expenditure on a government project."}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "expenditure on a government project" in data["draft"]


def test_rti_draft_streetlights(setup_mock_rag_client):
    """TEST 3: Request for streetlights in Ward 5."""
    response = client.post(
        "/api/v1/rti/draft",
        json={
            "request": "I want to know how many streetlights were installed in Ward 5.",
            "applicant_name": "Ramesh Kumar",
            "public_authority": "Municipal Corporation of Delhi",
        }
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "streetlights" in data["draft"]
    assert "Ramesh Kumar" in data["draft"]
    assert "Municipal Corporation of Delhi" in data["draft"]


def test_rti_appeal_question_not_application(setup_mock_rag_client):
    """TEST 4: Informational query about appeals should return grounded answer instead of draft template."""
    response = client.post(
        "/api/v1/rti/draft",
        json={"request": "Can I appeal if my RTI request is rejected?"}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "First Appeal" in data["draft"]
    assert "RTI APPLICATION" not in data["draft"]


def test_rti_negative_test_no_invented_pio(setup_mock_rag_client):
    """TEST 5 (Negative Test): Request for exact PIO name/address should use placeholders and state limitation."""
    response = client.post(
        "/api/v1/rti/draft",
        json={"request": "Write an RTI application and tell me the exact PIO name and address."}
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert "[Public Information Officer]" in data["draft"]
    assert data["limitations"] is not None
    assert "sources do not contain specific PIO officer names" in data["limitations"]
