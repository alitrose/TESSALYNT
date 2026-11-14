"""
Tessalynt - Generation Endpoint and Service Tests
Verifies prompt handling, JSON response extraction, and endpoint schemas.
"""
import pytest
from unittest.mock import patch
from app import app
from services.gemini_service import clean_json_response


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_clean_json_response_markdown_block():
    raw = '```json\n[{"id": 1, "front": "Q1", "back": "A1", "tag": "Concept"}]\n```'
    parsed = clean_json_response(raw)
    assert isinstance(parsed, list)
    assert len(parsed) == 1
    assert parsed[0]["front"] == "Q1"


def test_clean_json_response_raw_array():
    raw = '[{"id": 1, "front": "Q1", "back": "A1"}]'
    parsed = clean_json_response(raw)
    assert isinstance(parsed, list)
    assert parsed[0]["id"] == 1


def test_clean_json_response_with_surrounding_prose():
    raw = 'Here is your quiz:\n[{"id": 1, "question": "What is DNA?", "options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_answer": "A", "explanation": "test"}]\nHope this helps!'
    parsed = clean_json_response(raw)
    assert isinstance(parsed, list)
    assert parsed[0]["question"] == "What is DNA?"


def test_generate_notes_mocked(client):
    with patch("services.gemini_service._generate_with_fallback", return_value="# Photosynthesis\n## 1. Introduction\nPlant biology."):
        with client.session_transaction() as sess:
            sess["gemini_api_key"] = "test-fake-key"
        res = client.post("/api/generate-notes", json={
            "stream": "B.Sc",
            "department": "Botany",
            "year": "1st Year",
            "semester": "Semester 1",
            "subject": "Botany",
            "topic": "Photosynthesis"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "Photosynthesis" in data["content"]
        assert "material_id" in data


def test_generate_revision_mocked(client):
    with patch("services.gemini_service._generate_with_fallback", return_value="# Quick Revision Sheet: Newton's Laws\n## 1. Executive Summary\nThree laws."):
        with client.session_transaction() as sess:
            sess["gemini_api_key"] = "test-fake-key"
        res = client.post("/api/generate-revision", json={
            "subject": "Physics",
            "topic": "Newton's Laws",
            "level": "Undergraduate",
            "focus": "Core formulas"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert "Newton's Laws" in data["content"]


def test_generate_mcq_mocked(client):
    mock_mcq_json = (
        '[\n'
        '  {\n'
        '    "id": 1,\n'
        '    "question": "Which organelle performs photosynthesis?",\n'
        '    "options": {"A": "Chloroplast", "B": "Mitochondria", "C": "Ribosome", "D": "Nucleus"},\n'
        '    "correct_answer": "A",\n'
        '    "explanation": "Chloroplasts contain chlorophyll."\n'
        '  }\n'
        ']'
    )
    with patch("services.gemini_service._generate_with_fallback", return_value=mock_mcq_json):
        with client.session_transaction() as sess:
            sess["gemini_api_key"] = "test-fake-key"
        res = client.post("/api/generate-mcq", json={
            "subject": "Biology",
            "topic": "Chloroplast",
            "count": 1,
            "difficulty": "Easy"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert len(data["questions"]) == 1
        assert data["questions"][0]["correct_answer"] == "A"


def test_generate_flashcards_mocked(client):
    mock_cards_json = (
        '[\n'
        '  {\n'
        '    "id": 1,\n'
        '    "tag": "Definition",\n'
        '    "front": "What is Mitochondria?",\n'
        '    "back": "The powerhouse of the cell."\n'
        '  }\n'
        ']'
    )
    with patch("services.gemini_service._generate_with_fallback", return_value=mock_cards_json):
        with client.session_transaction() as sess:
            sess["gemini_api_key"] = "test-fake-key"
        res = client.post("/api/generate-flashcards", json={
            "subject": "Biology",
            "topic": "Cell Organelles",
            "count": 1,
            "difficulty": "Easy"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["status"] == "success"
        assert len(data["flashcards"]) == 1
        assert data["flashcards"][0]["front"] == "What is Mitochondria?"
