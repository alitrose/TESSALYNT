"""
Tessalynt - AI-Powered Personalized Learning Platform
Main Flask Application Factory and Route Handlers.
"""
import os
import re
import uuid
import json
import logging
from datetime import datetime, timezone
from flask import (
    Flask, render_template, request, jsonify, send_file,
    session, redirect, url_for, make_response
)
from dotenv import load_dotenv

from services.gemini_service import (
    generate_academic_notes, generate_quick_revision,
    generate_mcq_quiz, generate_flashcards, test_api_connection,
    GeminiAuthError, GeminiGenerationError
)
from services.pdf_service import (
    generate_notes_pdf, generate_revision_pdf,
    generate_mcq_question_paper_pdf, generate_mcq_answer_key_pdf,
    generate_flashcards_pdf
)
from services.db_service import (
    init_db, save_material, get_materials, get_material_by_id,
    delete_material, get_stats
)
import io

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("tessalynt")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "tessalynt-default-secret-production-grade")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize database schema on startup
with app.app_context():
    init_db()


def get_or_set_session_id():
    """Ensures each user has an isolated session ID for data privacy."""
    if "user_session_id" not in session:
        session["user_session_id"] = str(uuid.uuid4())
    return session["user_session_id"]


def get_effective_api_key():
    """Returns the API key from request header, session, or server environment."""
    # 1. Custom header (e.g. from frontend state)
    custom_header_key = request.headers.get("X-Gemini-Key")
    if custom_header_key and custom_header_key.strip():
        return custom_header_key.strip()
    
    # 2. Key stored in user's Flask session
    if "gemini_api_key" in session and session["gemini_api_key"]:
        return session["gemini_api_key"]
    
    # 3. Server environment variable
    env_key = os.getenv("GEMINI_API_KEY")
    if env_key and env_key.strip() not in ("", "your_new_api_key", "your_gemini_api_key_here"):
        return env_key.strip()
    
    return None


@app.context_processor
def inject_globals():
    """Injects common brand variables into all templates."""
    active_key = get_effective_api_key()
    return {
        "brand_name": "Tessalynt",
        "tagline": "Learn beyond limits.",
        "year": datetime.now(timezone.utc).year,
        "api_key_configured": bool(active_key)
    }


# ==========================================
# PAGE ROUTES
# ==========================================

@app.route("/")
def index():
    """Landing Page."""
    get_or_set_session_id()
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Student Dashboard."""
    sess_id = get_or_set_session_id()
    stats = get_stats(sess_id)
    recent_materials = get_materials(sess_id, limit=6)
    return render_template(
        "dashboard.html",
        stats=stats,
        recent_materials=recent_materials
    )


@app.route("/notes")
def notes_page():
    """AI Academic Notes Generator."""
    get_or_set_session_id()
    return render_template("notes.html")


@app.route("/revision")
def revision_page():
    """AI Quick Revision Module."""
    get_or_set_session_id()
    return render_template("revision.html")


@app.route("/mcq")
def mcq_page():
    """AI MCQ Generator and Interactive Quiz."""
    get_or_set_session_id()
    return render_template("mcq.html")


@app.route("/flashcards")
def flashcards_page():
    """AI Interactive Flashcard Generator."""
    get_or_set_session_id()
    return render_template("flashcards.html")


@app.route("/library")
def library_page():
    """Study Materials Library."""
    get_or_set_session_id()
    return render_template("library.html")


@app.route("/pdf-centre")
def pdf_centre_page():
    """Centralized PDF Export Studio."""
    get_or_set_session_id()
    return render_template("pdf_centre.html")


@app.route("/about")
def about_page():
    """About Tessalynt & Product Journey."""
    get_or_set_session_id()
    return render_template("about.html")


# ==========================================
# API ENDPOINTS
# ==========================================

@app.route("/api/status", methods=["GET"])
def api_status():
    """Returns API readiness status and configured models."""
    api_key = get_effective_api_key()
    if not api_key:
        return jsonify({
            "configured": False,
            "message": "Gemini API key is not configured. Please add GEMINI_API_KEY in .env or provide it in Settings."
        })
    try:
        check = test_api_connection(api_key)
        return jsonify({
            "configured": True,
            "model": check["model"],
            "message": "Gemini AI connection verified and operational."
        })
    except Exception as e:
        return jsonify({
            "configured": False,
            "error": str(e),
            "message": "API key was provided but failed verification. Please verify your Gemini API key."
        }), 400


@app.route("/api/set-session-key", methods=["POST"])
def set_session_key():
    """Allows setting or updating the Gemini API key for the current session."""
    data = request.get_json() or {}
    key = data.get("api_key", "").strip()
    if not key:
        session.pop("gemini_api_key", None)
        return jsonify({"status": "cleared", "message": "Session key cleared."})
    
    # Test key validity
    try:
        test = test_api_connection(key)
        session["gemini_api_key"] = key
        return jsonify({
            "status": "success",
            "model": test["model"],
            "message": f"API key verified successfully using model '{test['model']}'."
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid API Key: {str(e)}"
        }), 400


@app.route("/api/generate-notes", methods=["POST"])
def api_generate_notes():
    """Generates structured academic study notes."""
    data = request.get_json() or {}
    stream = data.get("stream", "").strip()
    department = data.get("department", "").strip()
    year = data.get("year", "").strip()
    semester = data.get("semester", "").strip()
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    instructions = data.get("instructions", "").strip()

    if not subject or not topic:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Subject and Topic are required fields."}), 400

    sess_id = get_or_set_session_id()
    api_key = get_effective_api_key()

    if not api_key:
        return jsonify({
            "error": "KEY_MISSING",
            "message": "Please configure your Gemini API key in .env or the Settings panel to generate study notes."
        }), 403

    try:
        notes_content = generate_academic_notes(
            stream=stream or "Engineering / Science",
            department=department or "General Department",
            year=year,
            semester=semester,
            subject=subject,
            topic=topic,
            additional_instructions=instructions,
            api_key=api_key
        )

        title = f"{topic} - Academic Notes"
        # Auto-save to study materials library
        material_id = save_material(
            session_id=sess_id,
            material_type="notes",
            title=title,
            subject=subject,
            topic=topic,
            content_text=notes_content,
            stream=stream,
            department=department,
            academic_year=year,
            semester=semester
        )

        return jsonify({
            "status": "success",
            "material_id": material_id,
            "title": title,
            "subject": subject,
            "topic": topic,
            "stream": stream,
            "content": notes_content
        })

    except GeminiAuthError as ae:
        return jsonify({"error": "AUTH_ERROR", "message": str(ae)}), 403
    except GeminiGenerationError as ge:
        return jsonify({"error": "GENERATION_ERROR", "message": str(ge)}), 502
    except Exception as e:
        logger.exception("Unexpected error in generate-notes")
        return jsonify({"error": "SERVER_ERROR", "message": f"An error occurred: {str(e)}"}), 500


@app.route("/api/generate-revision", methods=["POST"])
def api_generate_revision():
    """Generates rapid examination revision notes."""
    data = request.get_json() or {}
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    level = data.get("level", "").strip()
    focus = data.get("focus", "").strip()

    if not subject or not topic:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Subject and Topic are required fields."}), 400

    sess_id = get_or_set_session_id()
    api_key = get_effective_api_key()

    if not api_key:
        return jsonify({
            "error": "KEY_MISSING",
            "message": "Please configure your Gemini API key in .env or the Settings panel."
        }), 403

    try:
        revision_content = generate_quick_revision(
            subject=subject,
            topic=topic,
            level=level,
            focus=focus,
            api_key=api_key
        )

        title = f"{topic} - Quick Revision Sheet"
        material_id = save_material(
            session_id=sess_id,
            material_type="revision",
            title=title,
            subject=subject,
            topic=topic,
            content_text=revision_content
        )

        return jsonify({
            "status": "success",
            "material_id": material_id,
            "title": title,
            "subject": subject,
            "topic": topic,
            "content": revision_content
        })

    except GeminiAuthError as ae:
        return jsonify({"error": "AUTH_ERROR", "message": str(ae)}), 403
    except GeminiGenerationError as ge:
        return jsonify({"error": "GENERATION_ERROR", "message": str(ge)}), 502
    except Exception as e:
        logger.exception("Unexpected error in generate-revision")
        return jsonify({"error": "SERVER_ERROR", "message": f"An error occurred: {str(e)}"}), 500


@app.route("/api/generate-mcq", methods=["POST"])
def api_generate_mcq():
    """Generates an interactive multiple-choice assessment."""
    data = request.get_json() or {}
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    count = data.get("count", 5)
    difficulty = data.get("difficulty", "Medium").strip()

    if not subject or not topic:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Subject and Topic are required fields."}), 400

    sess_id = get_or_set_session_id()
    api_key = get_effective_api_key()

    if not api_key:
        return jsonify({
            "error": "KEY_MISSING",
            "message": "Please configure your Gemini API key in .env or the Settings panel."
        }), 403

    try:
        questions = generate_mcq_quiz(
            subject=subject,
            topic=topic,
            count=count,
            difficulty=difficulty,
            api_key=api_key
        )

        title = f"{topic} - MCQ Quiz ({difficulty})"
        material_id = save_material(
            session_id=sess_id,
            material_type="mcq",
            title=title,
            subject=subject,
            topic=topic,
            content_json=questions,
            difficulty=difficulty
        )

        return jsonify({
            "status": "success",
            "material_id": material_id,
            "title": title,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "questions": questions
        })

    except GeminiAuthError as ae:
        return jsonify({"error": "AUTH_ERROR", "message": str(ae)}), 403
    except GeminiGenerationError as ge:
        return jsonify({"error": "GENERATION_ERROR", "message": str(ge)}), 502
    except Exception as e:
        logger.exception("Unexpected error in generate-mcq")
        return jsonify({"error": "SERVER_ERROR", "message": f"An error occurred: {str(e)}"}), 500


@app.route("/api/generate-flashcards", methods=["POST"])
def api_generate_flashcards():
    """Generates an interactive set of study flashcards."""
    data = request.get_json() or {}
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "").strip()
    count = data.get("count", 8)
    difficulty = data.get("difficulty", "Medium").strip()

    if not subject or not topic:
        return jsonify({"error": "VALIDATION_ERROR", "message": "Subject and Topic are required fields."}), 400

    sess_id = get_or_set_session_id()
    api_key = get_effective_api_key()

    if not api_key:
        return jsonify({
            "error": "KEY_MISSING",
            "message": "Please configure your Gemini API key in .env or the Settings panel."
        }), 403

    try:
        flashcards = generate_flashcards(
            subject=subject,
            topic=topic,
            count=count,
            difficulty=difficulty,
            api_key=api_key
        )

        title = f"{topic} - Flashcard Deck"
        material_id = save_material(
            session_id=sess_id,
            material_type="flashcards",
            title=title,
            subject=subject,
            topic=topic,
            content_json=flashcards,
            difficulty=difficulty
        )

        return jsonify({
            "status": "success",
            "material_id": material_id,
            "title": title,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "flashcards": flashcards
        })

    except GeminiAuthError as ae:
        return jsonify({"error": "AUTH_ERROR", "message": str(ae)}), 403
    except GeminiGenerationError as ge:
        return jsonify({"error": "GENERATION_ERROR", "message": str(ge)}), 502
    except Exception as e:
        logger.exception("Unexpected error in generate-flashcards")
        return jsonify({"error": "SERVER_ERROR", "message": f"An error occurred: {str(e)}"}), 500


# ==========================================
# STUDY MATERIALS LIBRARY APIS
# ==========================================

@app.route("/api/materials", methods=["GET"])
def api_get_materials():
    """Lists study materials with filtering and search."""
    sess_id = get_or_set_session_id()
    search = request.args.get("search", "")
    mtype = request.args.get("type", "all")
    items = get_materials(session_id=sess_id, search=search, material_type=mtype)
    return jsonify({"materials": items})


@app.route("/api/materials/<int:material_id>", methods=["GET"])
def api_get_single_material(material_id):
    """Retrieves full content of a specific study material."""
    sess_id = get_or_set_session_id()
    item = get_material_by_id(material_id, session_id=sess_id)
    if not item:
        return jsonify({"error": "NOT_FOUND", "message": "Material not found"}), 404
    return jsonify({"material": item})


@app.route("/api/materials/<int:material_id>", methods=["DELETE"])
def api_delete_material(material_id):
    """Deletes a study material item."""
    sess_id = get_or_set_session_id()
    success = delete_material(material_id, session_id=sess_id)
    if not success:
        return jsonify({"error": "NOT_FOUND", "message": "Item could not be deleted"}), 404
    return jsonify({"status": "deleted", "id": material_id})


@app.route("/api/materials", methods=["POST"])
def api_save_material():
    """Explicitly saves or updates a study material."""
    sess_id = get_or_set_session_id()
    data = request.get_json() or {}
    mtype = data.get("material_type", "notes")
    title = data.get("title", "Untitled Study Material")
    subject = data.get("subject", "")
    topic = data.get("topic", "")
    content_text = data.get("content_text", "")
    content_json = data.get("content_json")

    new_id = save_material(
        session_id=sess_id,
        material_type=mtype,
        title=title,
        subject=subject,
        topic=topic,
        content_text=content_text,
        content_json=content_json,
        stream=data.get("stream", ""),
        department=data.get("department", ""),
        academic_year=data.get("academic_year", ""),
        semester=data.get("semester", ""),
        difficulty=data.get("difficulty", "")
    )
    return jsonify({"status": "saved", "id": new_id})


# ==========================================
# PDF & TXT EXPORT APIS
# ==========================================

@app.route("/api/export-pdf", methods=["POST"])
def api_export_pdf():
    """
    Exports publication-grade PDF documents for:
    - notes
    - revision
    - mcq_paper (without answers)
    - mcq_key (with answers & explanations)
    - flashcards
    """
    data = request.get_json() or {}
    export_type = data.get("export_type", "notes")
    title = data.get("title", "Tessalynt Document")
    subject = data.get("subject", "General Subject")
    topic = data.get("topic", "General Topic")
    stream = data.get("stream", "")
    difficulty = data.get("difficulty", "Standard")

    try:
        if export_type == "notes":
            content_text = data.get("content", "")
            pdf_bytes = generate_notes_pdf(title, subject, topic, stream, content_text)
            filename = f"Tessalynt_Notes_{slugify(topic)}.pdf"

        elif export_type == "revision":
            content_text = data.get("content", "")
            pdf_bytes = generate_revision_pdf(title, subject, topic, content_text)
            filename = f"Tessalynt_Revision_{slugify(topic)}.pdf"

        elif export_type == "mcq_paper":
            questions = data.get("questions", [])
            pdf_bytes = generate_mcq_question_paper_pdf(title, subject, topic, questions, difficulty)
            filename = f"Tessalynt_MCQ_Question_Paper_{slugify(topic)}.pdf"

        elif export_type == "mcq_key":
            questions = data.get("questions", [])
            pdf_bytes = generate_mcq_answer_key_pdf(title, subject, topic, questions, difficulty)
            filename = f"Tessalynt_MCQ_Answer_Key_{slugify(topic)}.pdf"

        elif export_type == "flashcards":
            cards = data.get("flashcards", [])
            pdf_bytes = generate_flashcards_pdf(title, subject, topic, cards)
            filename = f"Tessalynt_Flashcards_{slugify(topic)}.pdf"

        else:
            return jsonify({"error": "INVALID_TYPE", "message": f"Unknown export type: {export_type}"}), 400

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        logger.exception("Error generating PDF")
        return jsonify({"error": "PDF_ERROR", "message": f"Failed to generate PDF: {str(e)}"}), 500


@app.route("/api/export-txt", methods=["POST"])
def api_export_txt():
    """Generates and serves a clean plain-text study document."""
    data = request.get_json() or {}
    title = data.get("title", "Tessalynt Study Material")
    subject = data.get("subject", "")
    topic = data.get("topic", "")
    content = data.get("content", "")

    header = (
        f"{'=' * 60}\n"
        f"TESSALYNT — Learn beyond limits\n"
        f"Title:   {title}\n"
        f"Subject: {subject}\n"
        f"Topic:   {topic}\n"
        f"Date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"{'=' * 60}\n\n"
    )
    full_text = header + content
    filename = f"Tessalynt_{slugify(topic or 'study_material')}.txt"

    response = make_response(full_text)
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    response.headers["Content-Type"] = "text/plain; charset=utf-8"
    return response


def slugify(text):
    """Converts a title or topic string to a safe filename slug."""
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", text)[:40] or "document"


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
