"""
Tessalynt - Learning Levels Test Suite
Verifies the 3 selectable learning levels: Beginner Friendly, University Academic, and Exam Preparation.
Tests prompt generation, API endpoint behavior, database storage, and PDF rendering with tables/math.
"""
import pytest
from unittest.mock import patch, MagicMock
from app import app
from services.gemini_service import generate_academic_notes
from services.pdf_service import generate_notes_pdf, _clean_markdown_to_xml, markdown_to_flowables, get_tessalynt_styles
from services.db_service import get_material_by_id


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_level_prompts_are_meaningfully_different():
    """Verifies that each learning level produces distinct pedagogical prompts."""
    prompts_captured = {}

    def mock_gen(prompt, api_key=None, temperature=0.5, response_mime_type=None, max_output_tokens=4096):
        level_tag = "unknown"
        if "Level 1: Beginner Friendly" in prompt:
            level_tag = "beginner"
        elif "Level 2: University Academic" in prompt:
            level_tag = "academic"
        elif "Level 3: University Exam Preparation" in prompt:
            level_tag = "exam"
        prompts_captured[level_tag] = prompt
        return f"# {level_tag.upper()} NOTES CONTENT"

    with patch("services.gemini_service._generate_with_fallback", side_effect=mock_gen):
        res_beg = generate_academic_notes(
            stream="B.Tech", department="CSE", year="3rd Year", semester="Semester 5",
            subject="Theory of Computation", topic="Variants of Turing Machines",
            learning_level="beginner", api_key="fake-key"
        )
        res_acad = generate_academic_notes(
            stream="B.Tech", department="CSE", year="3rd Year", semester="Semester 5",
            subject="Theory of Computation", topic="Variants of Turing Machines",
            learning_level="academic", api_key="fake-key"
        )
        res_exam = generate_academic_notes(
            stream="B.Tech", department="CSE", year="3rd Year", semester="Semester 5",
            subject="Theory of Computation", topic="Variants of Turing Machines",
            learning_level="exam", api_key="fake-key"
        )

    # 1. All 3 levels must be captured
    assert "beginner" in prompts_captured
    assert "academic" in prompts_captured
    assert "exam" in prompts_captured

    # 2. Beginner prompt must enforce plain English, analogies, de-jargonizing
    assert "BEGINNER FRIENDLY FOCUS" in prompts_captured["beginner"]
    assert "analogies" in prompts_captured["beginner"]
    assert "plain English" in prompts_captured["beginner"]

    # 3. Academic prompt must enforce formal depth, mathematical tuples, proofs
    assert "UNIVERSITY ACADEMIC FOCUS" in prompts_captured["academic"]
    assert "formal definitions" in prompts_captured["academic"]
    assert "theorems" in prompts_captured["academic"]

    # 4. Exam prompt must enforce mark distributions, model answers, 16-mark blueprint
    assert "EXAM PREPARATION FOCUS" in prompts_captured["exam"]
    assert "16-Mark" in prompts_captured["exam"]
    assert "Common Student Mistakes" in prompts_captured["exam"]


def test_api_generate_notes_all_three_levels(client):
    """Verifies that /api/generate-notes endpoint handles all three learning levels."""
    levels = ["beginner", "academic", "exam"]

    for lvl in levels:
        mock_output = f"# Variants of Turing Machines\n## 1. Introduction\nSample for {lvl} level."
        with patch("services.gemini_service._generate_with_fallback", return_value=mock_output):
            with client.session_transaction() as sess:
                sess["gemini_api_key"] = "test-fake-key"

            res = client.post("/api/generate-notes", json={
                "stream": "B.Tech",
                "department": "Computer Science & Engineering",
                "year": "3rd Year",
                "semester": "Semester 5",
                "subject": "Theory of Computation",
                "topic": "Variants of Turing Machines",
                "learning_level": lvl
            })

            assert res.status_code == 200
            data = res.get_json()
            assert data["status"] == "success"
            assert data["learning_level"] == lvl
            assert "material_id" in data

            # Verify persisted material has difficulty set to learning level
            material = get_material_by_id(data["material_id"])
            assert material is not None
            assert material["difficulty"] == lvl


def test_api_generate_notes_invalid_level_fallback(client):
    """Verifies that an invalid learning_level gracefully defaults to 'academic'."""
    with patch("services.gemini_service._generate_with_fallback", return_value="# Sample Fallback Notes"):
        with client.session_transaction() as sess:
            sess["gemini_api_key"] = "test-fake-key"

        res = client.post("/api/generate-notes", json={
            "stream": "B.Tech",
            "department": "CSE",
            "year": "3rd Year",
            "semester": "Semester 5",
            "subject": "Theory of Computation",
            "topic": "Variants of Turing Machines",
            "learning_level": "super_mega_ultra" # invalid
        })

        assert res.status_code == 200
        data = res.get_json()
        assert data["learning_level"] == "academic"


def test_pdf_export_with_tables_and_math():
    """Verifies that ReportLab PDF generation renders tables, math, and code blocks cleanly."""
    sample_notes = """
# Variants of Turing Machines: Complete Academic Study Notes
**Subject:** Theory of Computation | **Stream:** B.Tech CSE | **Level:** Academic

## 1. Introduction
The standard Turing Machine has a single infinite tape.

## 5. Formal Definition
A Multi-tape Turing Machine with $k$ tapes is formally defined as a 7-tuple:
$$M = (Q, \\Sigma, \\Gamma, \\delta, q_0, B, F)$$

| Symbol / Notation | Name | Mathematical Meaning | Domain / Permissible Values |
| :--- | :--- | :--- | :--- |
| $Q$ | Finite States | Set of internal control states | Non-empty finite set |
| $\\Sigma$ | Input Alphabet | Valid input characters | $\\sqcup \\notin \\Sigma$ |
| $\\Gamma$ | Tape Alphabet | Characters writable to tapes | $\\Sigma \\subset \\Gamma$ |
| $\\delta$ | Transition Function | State mapping rule | $\\delta: Q \\times \\Gamma^k \\to Q \\times \\Gamma^k \\times \\{L, R\\}^k$ |

```mermaid
flowchart LR
    A[Single Tape TM] -->|Simulation| B[Multi-Tape TM]
    B -->|Equivalence| C[Non-Deterministic TM]
```

```python
# Simulation pseudocode
def simulate_step(tape_heads):
    return new_states
```
"""
    pdf_bytes = generate_notes_pdf(
        title="Variants of Turing Machines",
        subject="Theory of Computation",
        topic="Variants of Turing Machines",
        stream="B.Tech CSE",
        notes_markdown=sample_notes,
        learning_level="academic"
    )

    assert pdf_bytes is not None
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


def test_clean_markdown_to_xml_math_symbols():
    """Verifies LaTeX symbol replacements in PDF XML preparation."""
    raw = "Let $\\delta: Q \\times \\Gamma \\to Q$ and $\\Sigma \\subseteq \\Gamma$."
    cleaned = _clean_markdown_to_xml(raw)
    assert "δ" in cleaned
    assert "Σ" in cleaned
    assert "Γ" in cleaned
    assert "→" in cleaned
    assert "⊆" in cleaned
