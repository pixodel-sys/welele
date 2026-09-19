import pytest
from fastapi.testclient import TestClient
from main import app
from story_forge.repository import InMemoryStoryForgeRepository
from story_forge.api.routes import get_repository

client = TestClient(app)

def test_start_session_timing_headers_and_document_context():
    # 1. Create a story
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Amaphupho Treatment Test",
        "owner_id": "creator_doc_test",
        "logline": "A story seeded with treatment notes",
        "primary_language": "isiZulu"
    })
    assert create_res.status_code == 200
    story_data = create_res.json()
    story_id = story_data["story_id"]

    # 2. Start session with story_document_context ("Context Before Interrogation")
    doc_context = (
        "CHARACTERS:\n"
        "- Sabelo (32): Disillusioned private investigator in Durban.\n"
        "- Nomvula (28): Fierce heir to a taxi fleet contesting her uncle's will.\n\n"
        "TREATMENT / EPISODIC OUTLINE:\n"
        "Episode 1 opens at a contested funeral. Sabelo is hired to photograph attendees "
        "when Nomvula recognizes him from an old police inquiry."
    )

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_doc_test",
        "initial_premise": "Contested family funeral and taxi empire dispute",
        "story_document_context": doc_context,
        "creative_objective": "Tense urban vertical drama",
        "production_objective": "Single funeral location, 2-3 actors per scene"
    })

    assert session_res.status_code == 200
    sess = session_res.json()
    assert sess["id"] is not None
    assert sess["story_id"] == story_id

    # 3. Verify HTTP timing headers exist and are non-empty
    headers = session_res.headers
    assert "X-Forge-Ingestion-Ms" in headers
    assert "X-Forge-LLM-Ms" in headers
    assert "X-Forge-Reconciliation-Ms" in headers
    assert "X-Forge-Backend-Total-Ms" in headers
    assert "Access-Control-Expose-Headers" in headers

    ingestion_ms = float(headers["X-Forge-Ingestion-Ms"])
    llm_ms = float(headers["X-Forge-LLM-Ms"])
    reconciliation_ms = float(headers["X-Forge-Reconciliation-Ms"])
    backend_total_ms = float(headers["X-Forge-Backend-Total-Ms"])

    assert ingestion_ms >= 0.0
    assert llm_ms >= 0.0
    assert reconciliation_ms >= 0.0
    assert backend_total_ms >= 0.0


def test_start_session_backward_compatibility_without_doc_context():
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Minimal Seed Story",
        "owner_id": "creator_compat_test",
        "logline": "Minimal logline"
    })
    assert create_res.status_code == 200
    story_id = create_res.json()["story_id"]

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_compat_test",
        "initial_premise": "A man arrives at the wrong funeral"
    })
    assert session_res.status_code == 200
    assert "X-Forge-Backend-Total-Ms" in session_res.headers


# =============================================================================
# INPUT INTEGRITY GUARD REGRESSION SUITE
# Proves: "No unvalidated external material crosses the Document Context boundary into Story Reasoning."
# =============================================================================

def test_document_submission_rejects_docx_pk_zip_signature():
    """
    Specifically tests that a .docx/binary ZIP signature beginning with 'PK'
    is rejected at the API boundary before entering Story Reasoning.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Binary Injection Attempt",
        "owner_id": "creator_security_test"
    })
    story_id = create_res.json()["story_id"]

    # Typical PK\x03\x04 ZIP container header used by DOCX / OpenXML
    docx_binary_simulated = "PK\x03\x04\x14\x00\x06\x00\x08\x00[Content_Types].xml\x00\x01\x02garbled_binary_data"

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_security_test",
        "initial_premise": "Valid premise",
        "story_document_context": docx_binary_simulated
    })

    # Must be rejected with HTTP 400 or HTTP 422
    assert session_res.status_code in (400, 422)
    err_detail = str(session_res.json())
    assert "DOCX/ZIP" in err_detail or "Unsupported binary document format" in err_detail


def test_document_submission_rejects_pdf_signature():
    """
    Tests that PDF documents (%PDF-) are rejected at the ingestion boundary.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "PDF Ingestion Attempt",
        "owner_id": "creator_security_test"
    })
    story_id = create_res.json()["story_id"]

    pdf_binary_simulated = "%PDF-1.7\n%\xe2\xe3\xcf\xd3\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj"

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_security_test",
        "initial_premise": "Valid premise",
        "story_document_context": pdf_binary_simulated
    })

    assert session_res.status_code in (400, 422)
    err_detail = str(session_res.json())
    assert "PDF" in err_detail


def test_document_submission_rejects_rtf_signature():
    """
    Tests that RTF documents (^{\\rtf) are rejected at the ingestion boundary.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "RTF Ingestion Attempt",
        "owner_id": "creator_security_test"
    })
    story_id = create_res.json()["story_id"]

    rtf_content = "{\\rtf1\\ansi\\deff0{\\fonttbl{\\f0 Courier;}}\\viewkind4\\uc1\\pard\\f0\\fs20 Hello\\par}"

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_security_test",
        "initial_premise": "Valid premise",
        "story_document_context": rtf_content
    })

    assert session_res.status_code in (400, 422)
    err_detail = str(session_res.json())
    assert "RTF" in err_detail


def test_document_submission_rejects_malformed_null_bytes():
    """
    Tests that malformed text files containing null bytes are rejected.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Null Byte Test",
        "owner_id": "creator_security_test"
    })
    story_id = create_res.json()["story_id"]

    corrupted_text = "Good text until here\x00\x00corrupted binary payload"

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_security_test",
        "initial_premise": "Valid premise",
        "story_document_context": corrupted_text
    })

    assert session_res.status_code in (400, 422)
    err_detail = str(session_res.json())
    assert "null bytes" in err_detail


def test_document_submission_rejects_binary_control_characters():
    """
    Tests that text with non-printable binary control characters is rejected.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Control Char Test",
        "owner_id": "creator_security_test"
    })
    story_id = create_res.json()["story_id"]

    corrupted_text = "Some text \x01\x02\x03\x04\x05 disguised as notes"

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_security_test",
        "initial_premise": "Valid premise",
        "story_document_context": corrupted_text
    })

    assert session_res.status_code in (400, 422)
    err_detail = str(session_res.json())
    assert "Non-printable" in err_detail or "control characters" in err_detail


def test_document_submission_accepts_clean_markdown():
    """
    Tests that valid markdown notes are accepted and ingested as context cleanly.
    """
    create_res = client.post("/api/v1/forge/stories", json={
        "title": "Clean Markdown Story",
        "owner_id": "creator_markdown_test",
        "logline": "Logline for clean MD"
    })
    story_id = create_res.json()["story_id"]

    markdown_notes = (
        "# Story Treatment: The Lost Heir\n\n"
        "## Core Characters\n"
        "- **Bongani**: A retired detective\n"
        "- **Lindiwe**: A young journalist uncovering corruption\n\n"
        "## Scene 1\n"
        "In a rainy Durban harbor, a sealed container is opened..."
    )

    session_res = client.post(f"/api/v1/forge/stories/{story_id}/sessions", json={
        "creator_id": "creator_markdown_test",
        "initial_premise": "A retired detective and young journalist uncover harbor corruption",
        "story_document_context": markdown_notes
    })

    assert session_res.status_code == 200
    sess = session_res.json()
    assert sess["id"] is not None
    assert sess["story_id"] == story_id
