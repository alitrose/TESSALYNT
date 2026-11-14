"""
Tessalynt - Google Gemini AI Service
Handles communication with Google GenAI API, intelligent prompt engineering,
model cascade fallback, and JSON extraction.
"""
import os
import re
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Cached active model to avoid retrying failing models on every request
_ACTIVE_WORKING_MODEL = "gemini-3.5-flash-lite"

# Production-verified candidate models in order of speed, quota reliability, and academic depth
CANDIDATE_MODELS = [
    "gemini-3.5-flash-lite",    # Ultra-fast, highly responsive, dedicated free-tier quota
    "gemini-3.5-flash",         # Rich academic reasoning, high throughput
    "gemini-3.1-flash-lite",    # Secondary fast fallback
    "gemini-flash-lite-latest", # Auto-updating alias
    "gemini-flash-latest",      # Auto-updating alias
    "gemini-3.8-flash"          # Daily quota candidate
]


class GeminiAuthError(Exception):
    """Raised when Gemini API key is missing or invalid."""
    pass


class GeminiGenerationError(Exception):
    """Raised when content generation fails across available models."""
    pass


def get_active_api_key(override_key=None):
    """Retrieves and validates the Gemini API key from override, session or env."""
    key = override_key or os.getenv("GEMINI_API_KEY")
    if not key or key.strip() in ("", "your_new_api_key", "your_gemini_api_key_here"):
        raise GeminiAuthError(
            "Gemini API key is not configured. Please add your GEMINI_API_KEY to your .env file "
            "or enter it in the application settings."
        )
    return key.strip()


def get_genai_client(api_key=None):
    """Returns a configured modern google.genai Client."""
    key = get_active_api_key(api_key)
    try:
        from google import genai
        return genai.Client(api_key=key)
    except Exception as e:
        logger.warning(f"Could not initialize modern google.genai client: {e}")
        return None


def test_api_connection(api_key=None):
    """Tests the API connection and returns the working model name."""
    global _ACTIVE_WORKING_MODEL
    key = get_active_api_key(api_key)
    
    models_to_test = []
    if _ACTIVE_WORKING_MODEL and _ACTIVE_WORKING_MODEL in CANDIDATE_MODELS:
        models_to_test.append(_ACTIVE_WORKING_MODEL)
    for m in CANDIDATE_MODELS:
        if m not in models_to_test:
            models_to_test.append(m)

    client = get_genai_client(key)
    errors = []
    
    if client:
        from google.genai import types
        for model_name in models_to_test:
            try:
                res = client.models.generate_content(
                    model=model_name,
                    contents="Say 'OK'",
                    config=types.GenerateContentConfig(
                        temperature=0.1,
                        max_output_tokens=10
                    )
                )
                if res and res.text:
                    _ACTIVE_WORKING_MODEL = model_name
                    logger.info(f"Verified working Gemini model: {model_name}")
                    return {"status": "ok", "model": model_name, "message": "Connection successful"}
            except Exception as e:
                err_msg = str(e)
                logger.warning(f"Model test failed for {model_name}: {err_msg}")
                errors.append(f"{model_name}: {err_msg}")
                continue

    # Legacy SDK fallback if modern client is unavailable
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=key)
        for model_name in models_to_test:
            try:
                mod = legacy_genai.GenerativeModel(model_name)
                res = mod.generate_content("Say 'OK'", request_options={"timeout": 15})
                if res and res.text:
                    _ACTIVE_WORKING_MODEL = model_name
                    return {"status": "ok", "model": model_name, "message": "Connection successful"}
            except Exception as e:
                errors.append(f"{model_name}: {str(e)}")
                continue
    except Exception as e:
        errors.append(f"Legacy SDK: {str(e)}")

    raise GeminiGenerationError(f"Could not connect to Gemini API using any supported model. Errors: {'; '.join(errors[:3])}")


def _generate_with_fallback(prompt, api_key=None, temperature=0.5, response_mime_type=None, max_output_tokens=4096):
    """Generates text content using modern google.genai SDK with automatic model fallback."""
    global _ACTIVE_WORKING_MODEL
    key = get_active_api_key(api_key)
    client = get_genai_client(key)

    models_to_try = []
    if _ACTIVE_WORKING_MODEL and _ACTIVE_WORKING_MODEL in CANDIDATE_MODELS:
        models_to_try.append(_ACTIVE_WORKING_MODEL)
    for m in CANDIDATE_MODELS:
        if m not in models_to_try:
            models_to_try.append(m)

    last_error = None

    if client:
        from google.genai import types
        for model_name in models_to_try[:3]:
            try:
                config_kwargs = {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens
                }
                if response_mime_type:
                    config_kwargs["response_mime_type"] = response_mime_type

                config = types.GenerateContentConfig(**config_kwargs)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config
                )
                
                text = getattr(response, "text", None)
                if not text and getattr(response, "candidates", None):
                    cand = response.candidates[0]
                    if getattr(cand, "content", None) and getattr(cand.content, "parts", None):
                        text = "".join(getattr(p, "text", "") for p in cand.content.parts if hasattr(p, "text"))

                if text and text.strip():
                    _ACTIVE_WORKING_MODEL = model_name
                    logger.info(f"Successfully generated content using model: {model_name}")
                    return text.strip()

            except Exception as e:
                last_error = e
                logger.warning(f"Model {model_name} failed: {e}. Trying fallback...")
                continue

    # Legacy fallback if needed
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=key)
        for model_name in models_to_try[:2]:
            try:
                legacy_kwargs = {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens
                }
                if response_mime_type:
                    legacy_kwargs["response_mime_type"] = response_mime_type
                gen_config = legacy_genai.types.GenerationConfig(**legacy_kwargs)
                model = legacy_genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=gen_config
                )
                response = model.generate_content(prompt, request_options={"timeout": 45})
                text = response.text if hasattr(response, "text") else None
                if text and text.strip():
                    _ACTIVE_WORKING_MODEL = model_name
                    return text.strip()
            except Exception as e:
                last_error = e
                continue
    except Exception:
        pass

    raise GeminiGenerationError(f"Failed to generate content across available models. Last error: {str(last_error)}")


def clean_json_response(raw_text):
    """Extracts and parses JSON from LLM responses with robust error recovery."""
    text = raw_text.strip()
    # 1. Strip markdown code blocks if present
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        text = code_block_match.group(1).strip()
    
    # 2. Try direct parse with strict=False (allows literal newlines inside strings)
    try:
        return json.loads(text, strict=False)
    except Exception:
        pass

    # 3. Try removing trailing commas
    no_trailing = re.sub(r",\s*([\]}])", r"\1", text)
    try:
        return json.loads(no_trailing, strict=False)
    except Exception:
        pass

    # 4. Try extracting array between first '[' and last ']'
    start_arr = text.find('[')
    end_arr = text.rfind(']')
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        arr_str = text[start_arr:end_arr + 1]
        try:
            return json.loads(arr_str, strict=False)
        except Exception:
            arr_clean = re.sub(r",\s*([\]}])", r"\1", arr_str)
            try:
                return json.loads(arr_clean, strict=False)
            except Exception:
                pass

    # 5. Try extracting object between first '{' and last '}'
    start_obj = text.find('{')
    end_obj = text.rfind('}')
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        obj_str = text[start_obj:end_obj + 1]
        try:
            return json.loads(obj_str, strict=False)
        except Exception:
            obj_clean = re.sub(r",\s*([\]}])", r"\1", obj_str)
            try:
                return json.loads(obj_clean, strict=False)
            except Exception:
                pass

    raise ValueError("Could not parse valid JSON from AI response.")


# ==========================================
# FEATURE 1: ACADEMIC NOTES GENERATOR
# ==========================================
def generate_academic_notes(stream, department, year, semester, subject, topic, 
                            learning_level="academic", additional_instructions="", api_key=None):
    """
    Generates comprehensive, university-grade academic study notes
    using a teaching-first methodology across three distinct learning levels:
    - 'beginner': Level 1 – Beginner Friendly (Intuition, analogies, plain-English math, gradual examples)
    - 'academic': Level 2 – University Academic (Rigorous formal depth, complete symbol breakdowns, proofs, architecture)
    - 'exam':     Level 3 – Exam Preparation (Mark-based question schemes 2M, 5M, 8M, 13/16M model answers, rubrics)
    """
    level_key = (learning_level or "academic").strip().lower()
    if level_key not in ["beginner", "academic", "exam"]:
        level_key = "academic"

    level_meta = {
        "beginner": {
            "name": "Level 1: Beginner Friendly",
            "persona": "an expert pedagogical tutor, student mentor, and master visual educator",
            "tone": "warm, lucid, highly accessible, conversational yet intellectually sound",
            "temp": 0.35
        },
        "academic": {
            "name": "Level 2: University Academic (In-Depth)",
            "persona": "a distinguished university professor and accredited curriculum author",
            "tone": "academically rigorous, formally precise, exhaustive, and conceptually authoritative",
            "temp": 0.3
        },
        "exam": {
            "name": "Level 3: University Exam Preparation (Scoring Focused)",
            "persona": "a senior university chief examiner, evaluator, and exam strategy specialist",
            "tone": "laser-focused on university examination scoring rubrics, mark distributions, and structured model answers",
            "temp": 0.25
        }
    }[level_key]

    target_aud = academic_level_descriptor(year, semester, stream)

    if level_key == "beginner":
        level_guide = """### LEVEL 1: BEGINNER FRIENDLY FOCUS:
- Explain every technical term in plain English before or immediately upon introducing it.
- Use intuitive real-world analogies (e.g. libraries, postal systems, assembly lines, everyday objects).
- Demystify mathematical expressions: explain what each formula means in plain English sentences before showing the equation.
- Provide simple, gradual worked examples with every step clearly explained.
- Emphasize WHY this concept was invented and what problem it solves.
- Tone should make the student feel capable and eliminate academic anxiety."""
    elif level_key == "exam":
        level_guide = """### LEVEL 3: EXAM PREPARATION FOCUS:
- Structure content around university examination patterns and mark allocations.
- Highlight high-frequency 2-mark definitions, 5-mark short notes, and 8-mark comparative questions.
- Include a full 13-Mark / 16-Mark University Long-Answer Blueprint with Model Answer:
  * Introduction (1 mark)
  * Formal Definition & Notation (2 marks)
  * System Architecture / Block Diagram (3 marks)
  * Step-by-Step Working & Mathematical Derivation (5 marks)
  * Solved Numerical Problem or Scenario (3 marks)
  * Advantages, Limitations & Conclusion (2 marks)
- Include 'Common Student Mistakes & Mark Deductions' (where students lose marks and how to prevent it).
- Include high-yield comparison tables and a 5-minute pre-exam revision checklist."""
    else:
        level_guide = """### LEVEL 2: UNIVERSITY ACADEMIC FOCUS:
- Deliver exhaustive university-grade depth and theoretical completeness.
- Present full formal definitions, formal mathematical tuples, domain/codomain mappings, and invariant properties.
- Include symbol-by-symbol breakdown tables for all mathematical formulations.
- Include algorithms, state transition mechanisms, formal theorems, and rigorous proofs/derivations.
- Provide step-by-step advanced worked examples and comparison matrices.
- Align with top university curricula (e.g. MIT, Stanford, IIT, NPTEL syllabus standards)."""

    prompt = f"""
You are {level_meta["persona"]} delivering academic study notes for {stream} students in the Department of {department}.
Subject: {subject}
Topic: {topic}
Target Audience / Academic Level: {target_aud}
Selected Learning Level: {level_meta["name"]}
Tone & Stance: {level_meta["tone"]}

================================================================================
CORE PEDAGOGICAL DIRECTIVE: TEACHING-FIRST EXPLANATION METHOD
================================================================================
CRITICAL RULE: DO NOT overwhelm students with dry theoretical jargon or formal definitions before they understand the underlying idea!
For every major concept, adhere to the Teaching-First sequence:
1. SIMPLE MEANING: Explain what the concept means in simple, clear language.
2. INTUITION: Explain the core logic and 'why' behind it.
3. RELATABLE ANALOGY: Provide an intuitive, real-world analogy.
4. FORMAL DEFINITION: State the formal textbook definition. Highlight technical keywords in **bold**.
5. TECHNICAL BREAKDOWN & SYMBOL DICTIONARY: Explain every variable, symbol, and term.
6. STEP-BY-STEP WORKING: Explain the operational mechanics chronologically.
7. WORKED EXAMPLES: Walk through concrete examples starting simple and increasing in depth.
8. EXAMINATION SCORING TIP: Note key points students must include in exam answers.

================================================================================
LEARNING LEVEL SPECIALIZATION ({level_meta["name"].upper()})
================================================================================
{level_guide}

================================================================================
FLEXIBLE 23-SECTION EDUCATIONAL SYLLABUS STRUCTURE
================================================================================
Structure the notes using the following standard sections (intelligently adapt to the subject matter; e.g. Theory of Computation needs formal tuples and transition diagrams; Mathematics needs derivations; CS needs code; DBMS needs SQL/schemas):

# {topic}: Complete Academic Study Notes
**Subject:** {subject} | **Stream/Degree:** {stream} ({department}) | **Academic Level:** {target_aud} | **Mode:** {level_meta["name"]}

## 1. Topic Overview & Context
Brief executive overview of {topic} within {subject}, explaining its academic significance and industry relevance.

## 2. Introduction & Background
Historical context, motivation, and why traditional methods were insufficient before this concept was developed.

## 3. Learning Objectives
Specific, measurable competencies the student will gain after studying these notes.

## 4. Prerequisites
Foundational concepts required before studying this topic, with quick 1-sentence refresher summaries.

## 5. Basic Concept Explained Simply (Intuition & Analogy)
Explain the core concept in plain English. Include a relatable real-world analogy that makes the mechanism immediately clear.

## 6. Important Terminology & Keywords
De-jargonized vocabulary list defining key technical terms in simple language.

## 7. Formal Academic Definition
Standard accredited textbook definitions with key terminology in **bold**.

## 8. Detailed Conceptual Explanation
In-depth theoretical breakdown of underlying principles, theories, and mechanisms.

## 9. System Architecture & Working Principles
How the system/concept is structured, its internal components, and how they interact.

## 10. Step-by-Step Operational Mechanics
Chronological walkthrough of the operational cycle or algorithm from start to finish.

## 11. Diagrams & Visual Representations
CRITICAL DIAGRAM INSTRUCTION:
- Never generate broken ASCII art or raw text boxes.
- Provide a clean, valid Mermaid.js diagram fenced inside ```mermaid ... ``` (e.g. flowchart TD, stateDiagram-v2, or graph LR).
- Follow the Mermaid diagram with a clear textual walkthrough explaining each node, transition, and data path.

## 12. Mathematical Formulations & Symbol Explanations
For every mathematical formula or formal specification:
- Display the equation in clean LaTeX formatting ($...$ inline or $$...$$ display).
- Provide an explicit Symbol Breakdown Table:
| Symbol / Notation | Name | Mathematical Meaning | Domain / Permissible Values |
| :--- | :--- | :--- | :--- |
- Explain when and why this expression is applied.

## 13. Step-by-Step Worked Examples
At least 2 concrete educational examples:
- Example 1: Foundational baseline problem with complete step-by-step solution.
- Example 2: More advanced / multi-step scenario with full trace, intermediate values, and final verification.

## 14. Real-World Applications & Industry Use Cases
Concrete implementations in modern technology, research, or industrial software.

## 15. Advantages, Trade-offs & Limitations
Balanced assessment of strengths, bottlenecks, trade-offs, and boundary conditions.

## 16. Comprehensive Comparison Table
Structured Markdown comparison table contrasting {topic} against alternative approaches, variants, or precursor models.

## 17. Important Properties, Theorems & Formulas
Cheat-sheet summary of core mathematical properties, lemmas, complexity classes, or invariant theorems.

## 18. Common Student Mistakes & Misconceptions
Top errors students make in conceptual understanding, problem solving, or exam writing, paired with corrections.

## 19. High-Yield Examination Points
Essential takeaway points that examiners expect to see in top-scoring university answer scripts.

## 20. Short-Answer Examination Questions & Model Answers
- 2-Mark Question: Model answer in 2-3 precise sentences.
- 5-Mark Question: Model answer with bullet points, brief mechanism, and key diagram reference.

## 21. Long-Answer Examination Questions (University Blueprint)
- 8-Mark Question & Model Answer.
- 13/16-Mark Comprehensive University Long-Answer Question & Model Answer following the structural blueprint (Introduction, Formal Definition, Block Diagram, Step-by-Step Working, Solved Scenario, Conclusion).

## 22. Quick 60-Second Revision Summary
Bullet-point rapid review designed for last-minute recall right before an examination.

## 23. Comprehensive Glossary
Alphabetical glossary of terms, symbols, and concepts covered in these notes.

================================================================================
CONCISENESS & PACING DIRECTIVE (CRITICAL FOR LIVE EXAM READINESS)
================================================================================
- Cover all 23 syllabus sections systematically, concisely, and completely.
- In Section 20, provide exactly 1 distinct 2-mark question with concise model answer and 1 distinct 5-mark question with structured model answer.
- In Section 21, provide ONE comprehensive 16-mark long-answer model blueprint question with a focused, structured model answer covering the 6 parts.
- ALWAYS conclude completely with Section 22 (Quick 60-Second Revision Summary) and Section 23 (Comprehensive Glossary). Never leave sections truncated.
- Maintain crisp, dense prose so that all 23 sections are fully delivered within approximately 2,200 to 2,800 words.

---
ADDITIONAL USER INSTRUCTIONS:
{additional_instructions if additional_instructions else "Ensure high pedagogical clarity, zero broken ASCII, and full academic accuracy."}

FORMATTING REQUIREMENTS:
- Use clean Markdown with clear headings (`#`, `##`, `###`), bullet points, bold highlights, LaTeX math (`$...$`), and tables.
- For diagrams, ALWAYS use valid ```mermaid blocks followed by a textual walkthrough. Never produce raw broken ASCII lines.
- Be exhaustive, structured, authoritative, and deeply instructional.
"""
    return _generate_with_fallback(
        prompt, 
        api_key=api_key, 
        temperature=level_meta["temp"],
        max_output_tokens=5500
    )


def academic_level_descriptor(year, semester, stream):
    parts = []
    if stream:
        parts.append(stream)
    if year:
        parts.append(year)
    if semester:
        parts.append(semester)
    return " - ".join(parts) if parts else "Undergraduate University Level"


# ==========================================
# FEATURE 2: QUICK REVISION MODULE
# ==========================================
def generate_quick_revision(subject, topic, level="", focus="", api_key=None):
    """
    Generates high-yield, compact last-minute revision materials for exam preparation.
    """
    prompt = f"""
You are an elite academic revision coach specializing in high-yield exam preparation.
Generate a concise, high-impact Quick Revision Sheet for:
Subject: {subject}
Topic: {topic}
Target Level: {level if level else "University / College Examination"}
Specific Focus: {focus if focus else "Core concepts, definitions, formulas, and high-frequency exam questions"}

Format your output in clean Markdown with the following exact sections:

# Quick Revision Sheet: {topic}
**Subject:** {subject} | **Exam Preparation Module**

## 1. Executive Summary (60-Second Overview)
A rapid 3-4 sentence elevator pitch capturing the core essence of {topic}.

## 2. Essential Definitions
Key technical definitions with critical keywords highlighted in **bold**.

## 3. Core Principles & Architecture
High-level summary of the fundamental laws, theorems, or mechanisms.

## 4. Key Formulas / Equations / Syntax Cheat Sheet
Essential formulas, equations, complexity classes, or syntax snippets that often appear in objective or numerical exam problems. (If purely qualitative, present core rules).

## 5. High-Yield Keywords & Mnemonics
Mnemonics, acronyms, and memory triggers designed for quick recall under exam stress.

## 6. Frequently Tested Exam Patterns
Top recurring exam traps, commonly confused concepts, and "difference between X and Y" tables.

## 7. 5-Minute Last-Minute Revision Checklist
A rapid bulleted checklist that a student can read right outside the examination hall.

Keep the content ultra-sharp, readable, concise, and focused on maximum exam scoring.
"""
    return _generate_with_fallback(prompt, api_key=api_key, temperature=0.4)


# ==========================================
# FEATURE 3: INTERACTIVE MCQ GENERATOR
# ==========================================
def generate_mcq_quiz(subject, topic, count=5, difficulty="Medium", api_key=None):
    """
    Generates multiple-choice questions with 4 options, correct answer, and explanation.
    Returns a Python list of dictionaries validated from JSON.
    """
    count = min(max(int(count), 3), 25)
    prompt = f"""
You are a senior academic test designer creating a high-standard multiple-choice assessment.
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty} (strictly adhere to this cognitive depth)
Number of questions: {count}

REQUIREMENTS:
1. Generate EXACTLY {count} unique, high-quality multiple choice questions.
2. Each question MUST have exactly 4 plausible options labeled "A", "B", "C", and "D".
3. Only ONE option must be correct. Avoid trivial distractors.
4. Provide a thorough, educational explanation for why the correct option is right and why others are incorrect.
5. Difficulty guidance:
   - Easy: Direct conceptual definitions, basic properties, foundational recall.
   - Medium: Application, comparison, mechanism identification, moderate problem-solving.
   - Hard: Edge cases, multi-step deductions, algorithmic analysis, subtle nuances.

OUTPUT FORMAT:
Return ONLY a valid JSON array of objects. Do not write any conversational text before or after the JSON.
Each object in the array must follow this exact schema:
[
  {{
    "id": 1,
    "question": "Question statement here?",
    "options": {{
      "A": "First option text",
      "B": "Second option text",
      "C": "Third option text",
      "D": "Fourth option text"
    }},
    "correct_answer": "A",
    "explanation": "Detailed explanation of the correct answer and concepts involved."
  }}
]
"""
    raw_response = _generate_with_fallback(prompt, api_key=api_key, temperature=0.3, response_mime_type="application/json")
    parsed = clean_json_response(raw_response)
    if not isinstance(parsed, list) or len(parsed) == 0:
        raise ValueError("AI response did not contain a valid list of MCQ items.")

    # Validate and standardize items
    validated_questions = []
    for idx, item in enumerate(parsed, 1):
        q_text = item.get("question", "").strip()
        options = item.get("options", {})
        correct = str(item.get("correct_answer", "")).strip().upper()
        explanation = item.get("explanation", "").strip()

        if not q_text or not isinstance(options, dict) or len(options) < 4:
            continue

        # Ensure keys A, B, C, D exist
        clean_opts = {
            "A": str(options.get("A", "")).strip(),
            "B": str(options.get("B", "")).strip(),
            "C": str(options.get("C", "")).strip(),
            "D": str(options.get("D", "")).strip()
        }

        if correct not in ["A", "B", "C", "D"]:
            correct = "A"

        validated_questions.append({
            "id": idx,
            "question": q_text,
            "options": clean_opts,
            "correct_answer": correct,
            "explanation": explanation or "No explanation provided."
        })

    if not validated_questions:
        raise ValueError("Failed to validate generated MCQ questions.")

    return validated_questions


# ==========================================
# FEATURE 4: FLASHCARD GENERATOR
# ==========================================
def generate_flashcards(subject, topic, count=8, difficulty="Medium", api_key=None):
    """
    Generates interactive flashcards with front (prompt/question) and back (concise answer/summary).
    Returns a Python list of dictionaries validated from JSON.
    """
    count = min(max(int(count), 4), 30)
    prompt = f"""
You are an expert cognitive learning specialist and memory retention expert.
Generate {count} dynamic study flashcards for:
Subject: {subject}
Topic: {topic}
Difficulty: {difficulty}

FLASHCARD GUIDELINES:
- Front: A clear, stimulating question, definition prompt, formula challenge, or problem statement.
- Back: A concise, memorable, and complete answer or explanation. Use punchy bullet points where helpful.
- Tag: A short category tag (e.g. 'Definition', 'Mechanism', 'Formula', 'Application', 'Key Law').

OUTPUT FORMAT:
Return ONLY a valid JSON array of objects. Do not write any conversational text before or after the JSON.
Schema:
[
  {{
    "id": 1,
    "tag": "Definition",
    "front": "What is the primary function of ...?",
    "back": "The primary function is ... because ..."
  }}
]
"""
    raw_response = _generate_with_fallback(prompt, api_key=api_key, temperature=0.4, response_mime_type="application/json")
    parsed = clean_json_response(raw_response)
    if not isinstance(parsed, list) or len(parsed) == 0:
        raise ValueError("AI response did not contain a valid list of flashcards.")

    validated_cards = []
    for idx, card in enumerate(parsed, 1):
        front = card.get("front", "").strip()
        back = card.get("back", "").strip()
        tag = card.get("tag", "Concept").strip()

        if front and back:
            validated_cards.append({
                "id": idx,
                "front": front,
                "back": back,
                "tag": tag
            })

    if not validated_cards:
        raise ValueError("Failed to extract valid flashcards from AI response.")

    return validated_cards
