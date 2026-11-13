"""
Tessalynt - Google Gemini AI Service
Handles communication with the Gemini API, intelligent prompt engineering,
model cascade fallback, and JSON extraction.
"""
import os
import re
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Model fallback cascade
CANDIDATE_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-pro"
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


def get_configured_genai_client(api_key=None):
    """Configures the google.generativeai SDK with the active key."""
    key = get_active_api_key(api_key)
    import google.generativeai as genai
    genai.configure(api_key=key)
    return genai


def test_api_connection(api_key=None):
    """Tests the API connection and returns the working model name."""
    genai = get_configured_genai_client(api_key)
    errors = []
    for model_name in CANDIDATE_MODELS:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Ping. Reply with 'PONG'")
            if response and response.text:
                return {"status": "ok", "model": model_name, "message": "Connection successful"}
        except Exception as e:
            errors.append(f"{model_name}: {str(e)}")
            continue

    raise GeminiGenerationError(f"Could not connect using any model. Errors: {'; '.join(errors)}")


def _generate_with_fallback(prompt, api_key=None, temperature=0.7):
    """Generates text content with automatic model fallback."""
    genai = get_configured_genai_client(api_key)
    last_error = None

    for model_name in CANDIDATE_MODELS:
        try:
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=8192
            )
            model = genai.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config
            )
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text
        except Exception as e:
            last_error = e
            logger.warning(f"Model {model_name} failed: {e}. Trying fallback...")
            continue

    raise GeminiGenerationError(f"Failed to generate content: {str(last_error)}")


def clean_json_response(raw_text):
    """Extracts and parses JSON from markdown-wrapped LLM responses."""
    text = raw_text.strip()
    # Strip markdown code blocks if present
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if code_block_match:
        text = code_block_match.group(1).strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array or object inside text
    array_match = re.search(r"\[\s*\{[\s\S]*\}\s*\]", text)
    if array_match:
        try:
            return json.loads(array_match.group(0))
        except json.JSONDecodeError:
            pass

    object_match = re.search(r"\{[\s\S]*\}", text)
    if object_match:
        try:
            return json.loads(object_match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError("Could not parse valid JSON from AI response.")


# ==========================================
# FEATURE 1: ACADEMIC NOTES GENERATOR
# ==========================================
def generate_academic_notes(stream, department, year, semester, subject, topic, 
                            additional_instructions="", api_key=None):
    """
    Generates comprehensive, university-grade academic study notes
    following the 13 required academic sections.
    """
    prompt = f"""
You are an expert university professor and master educator for {stream} students in the Department of {department}.
Your task is to write comprehensive, rigorous, yet accessible study notes for the subject '{subject}' on the topic '{topic}'.
Target Audience: {academic_level_descriptor(year, semester, stream)}.

IMPORTANT ARCHITECTURAL REQUIREMENTS:
You MUST structure the study notes using the following 13 numbered sections. Adapt and contextualize each section naturally to the topic:

# {topic}: Complete Academic Study Notes
**Subject:** {subject} | **Stream/Degree:** {stream} ({department}) | **Academic Level:** {year}, {semester}

## 1. Introduction
Provide a clear, engaging overview of {topic}. Explain what it is, why it matters in modern academia/industry, and how it connects to the broader curriculum of {subject}.

## 2. Formal Definition
Provide accurate, formal definitions as established in textbook standards and accredited syllabi. Highlight key technical terminology in **bold**.

## 3. Detailed Explanation
Deliver a comprehensive, in-depth conceptual breakdown. Explain fundamental theories, underlying mechanics, and architectural or mathematical intuition. Use step-by-step paragraphs and formatting.

## 4. Important Concepts & Terminology
Define the core building blocks, keywords, axioms, or components necessary for mastering this topic. Present with clear bullet points.

## 5. Types and Classifications
Present any taxonomies, categories, models, or variants of {topic}. Explain the criteria used for categorization and distinguish between types clearly.

## 6. Working Principles & Mechanism
Explain step-by-step how {topic} operates or functions in practice. If relevant, include logical workflows, execution steps, or equations.

## 7. Real-World Examples & Case Studies
Provide at least 2 to 3 concrete real-world examples, industrial applications, or case studies showing where this is used in actual systems or real-life scenarios.

## 8. Advantages & Strengths
List the key benefits, performance improvements, or practical value provided by this concept or approach.

## 9. Limitations & Disadvantages
Discuss constraints, potential bottlenecks, trade-offs, security considerations, or scenarios where alternative approaches are preferred.

## 10. Practical Applications & Industry Usage
Describe how engineering teams, scientists, or professionals leverage this knowledge in current industry trends.

## 11. Important Points & Key Takeaways
Provide a high-impact summary checklist of critical points students must memorize for exams.

## 12. Conclusion & Summary
Synthesize the entire discussion, summarizing key insights and highlighting future trends or related advanced topics.

## 13. Frequently Asked University Examination Questions (FAQs)
Provide 4-5 high-yield exam questions (mix of conceptual, analytical, and short-answer questions) complete with concise model answers.

---
ADDITIONAL USER INSTRUCTIONS:
{additional_instructions if additional_instructions else "Ensure clarity, high academic rigor, and beginner-friendly clarity."}

FORMATTING RULES:
- Use clean Markdown with clear headings (`#`, `##`, `###`), bullet points, bold highlights, and code/math blocks where appropriate.
- Be exhaustive, structured, and informative. Avoid shallow placeholders or generic summaries.
"""
    return _generate_with_fallback(prompt, api_key=api_key, temperature=0.5)


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
    raw_response = _generate_with_fallback(prompt, api_key=api_key, temperature=0.3)
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
    raw_response = _generate_with_fallback(prompt, api_key=api_key, temperature=0.4)
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
