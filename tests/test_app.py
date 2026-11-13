"""
Tessalynt - Comprehensive Application Test Suite
Verifies Flask routing, database persistence, PDF exports, validation, and security boundaries.
"""
import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from services.db_service import (
    init_db, save_material, get_materials, get_material_by_id,
    delete_material, get_stats
)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        with app.app_context():
            init_db()
        yield client


def test_landing_page(client):
    """Verifies that the landing page renders successfully with Tessalynt branding."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Tessalynt" in html
    assert "Learn beyond limits." in html
    assert "Start Generating Notes" in html


def test_dashboard_page(client):
    """Verifies the Student Dashboard loads."""
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "Learning Studios" in html
    assert "Saved Notes" in html


def test_learning_pages(client):
    """Verifies all main learning studio pages render without errors."""
    pages = ["/notes", "/revision", "/mcq", "/flashcards", "/library", "/pdf-centre", "/about"]
    for path in pages:
        res = client.get(path)
        assert res.status_code == 200, f"Page {path} failed with status {res.status_code}"


def test_api_status(client):
    """Verifies the /api/status endpoint response structure."""
    res = client.get("/api/status")
    assert res.status_code in [200, 400]
    data = res.get_json()
    assert "configured" in data


def test_input_validation(client):
    """Verifies that missing parameters return 400 validation error."""
    # Empty subject and topic
    res = client.post("/api/generate-notes", json={"subject": "", "topic": ""})
    assert res.status_code == 400
    data = res.get_json()
    assert data["error"] == "VALIDATION_ERROR"


def test_missing_key_security(client):
    """Verifies that attempts to generate content without a valid key fail securely."""
    # Send request with invalid placeholder key
    res = client.post(
        "/api/generate-notes",
        headers={"X-Gemini-Key": ""},
        json={"subject": "Calculus", "topic": "Integrals"}
    )
    # Either 403 KEY_MISSING or 400 depending on env
    assert res.status_code in [400, 403]


def test_database_persistence(client):
    """Verifies SQLite save, retrieval, filtering, and deletion."""
    test_session = "test-session-uuid-123"
    
    # Save a note
    item_id = save_material(
        session_id=test_session,
        material_type="notes",
        title="Test Operating Systems Note",
        subject="Operating Systems",
        topic="Deadlocks",
        content_text="Detailed notes about deadlock prevention and Banker's Algorithm."
    )
    assert item_id is not None
    assert item_id > 0

    # Retrieve by ID
    item = get_material_by_id(item_id, session_id=test_session)
    assert item is not None
    assert item["topic"] == "Deadlocks"

    # Filter by type
    materials = get_materials(session_id=test_session, material_type="notes")
    assert any(m["id"] == item_id for m in materials)

    # Check stats
    stats = get_stats(session_id=test_session)
    assert stats["notes"] >= 1

    # Delete
    deleted = delete_material(item_id, session_id=test_session)
    assert deleted is True

    # Confirm deletion
    deleted_item = get_material_by_id(item_id, session_id=test_session)
    assert deleted_item is None


def test_pdf_export_endpoint(client):
    """Verifies PDF generation endpoint for notes and MCQs."""
    # 1. Notes PDF
    payload = {
        "export_type": "notes",
        "title": "Quantum Mechanics Intro",
        "subject": "Physics",
        "topic": "Wave-Particle Duality",
        "stream": "B.Sc Physics",
        "content": "# Wave-Particle Duality\nLight behaves as both a wave and a particle.\n\n## 1. De Broglie Hypothesis\nLambda = h / p"
    }
    res = client.post("/api/export-pdf", json=payload)
    assert res.status_code == 200
    assert res.mimetype == "application/pdf"
    assert len(res.data) > 1000

    # 2. MCQ Paper PDF
    mcq_payload = {
        "export_type": "mcq_paper",
        "title": "Data Structures Quiz",
        "subject": "CS",
        "topic": "Binary Heaps",
        "difficulty": "Medium",
        "questions": [
            {
                "id": 1,
                "question": "What is the worst-case time complexity of inserting into a binary min-heap?",
                "options": {"A": "O(1)", "B": "O(log n)", "C": "O(n)", "D": "O(n log n)"},
                "correct_answer": "B",
                "explanation": "Heap insertion requires bubble-up along the tree height which is log n."
            }
        ]
    }
    res_mcq = client.post("/api/export-pdf", json=mcq_payload)
    assert res_mcq.status_code == 200
    assert res_mcq.mimetype == "application/pdf"


def test_txt_export_endpoint(client):
    """Verifies plain text study download endpoint."""
    payload = {
        "title": "Algorithms Summary",
        "subject": "Computer Science",
        "topic": "Sorting",
        "content": "Quicksort is divide-and-conquer."
    }
    res = client.post("/api/export-txt", json=payload)
    assert res.status_code == 200
    assert "text/plain" in res.mimetype
    assert "Quicksort" in res.data.decode("utf-8")
