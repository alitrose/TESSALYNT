# TESSALYNT
### *Learn beyond limits.*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg)](https://flask.palletsprojects.com/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev/)
[![ReportLab](https://img.shields.io/badge/PDF-ReportLab%205.0-red.svg)](https://www.reportlab.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Tessalynt** is an AI-powered personalized learning platform that transforms university-level curriculums into exhaustive academic study notes, rapid exam revision sheets, interactive multiple-choice quizzes with blind scoring, active-recall 3D flashcards, and publication-ready A4 PDF documents.

Originating as a Google Generative AI Workshop prototype, Tessalynt has been completely re-architected into a full-featured, production-ready educational SaaS platform.

---

## 🌟 Key Features

### 1. 📝 AI Academic Notes Generator
- **13-Section Pedagogical Structure**:
  1. Introduction & Context
  2. Formal Definitions & Terminology
  3. Detailed Explanations
  4. Core Concepts
  5. Types & Classifications
  6. Working Principles & Mechanisms
  7. Real-World Examples & Case Studies
  8. Advantages & Strengths
  9. Limitations & Disadvantages
  10. Practical Applications & Industry Usage
  11. Important Points / Key Takeaways
  12. Conclusion & Summary
  13. Frequently Asked University Examination Questions (FAQs)
- Contextualized by Degree/Stream, Department, Year, and Semester.
- Instant actions: Copy to Clipboard, TXT Download, Vector PDF Download, Print, and Regenerate.

### 2. ⚡ AI Quick Revision Module
- High-yield last-minute study sheets for exam sprints.
- 60-second executive summaries, essential definitions, formula & syntax cheat sheets, examiner traps, and 5-minute pre-exam checklists.

### 3. 🎯 Smart MCQ Generator & Quiz System
- Generates 5 to 20 multiple-choice questions per assessment with calibrated cognitive difficulty (*Easy*, *Medium*, *Hard*).
- **Strict Blind Testing**: Correct answers are concealed until submission.
- Instant automated grading, percentage calculations, performance badges, and in-depth rationales for every option.
- **Dual PDF Publishing**:
  1. *MCQ Question Paper* (clean test paper with answer marking brackets).
  2. *MCQ Answer Key & Explanations Manual* (with quick-scoring matrix and complete pedagogical analysis).

### 4. 🃏 Interactive 3D Flashcard Studio
- Active-recall cognitive cards with smooth 3D flip physics.
- Shuffle mode, keyboard shortcuts (`Space` to flip, `Arrow Left/Right` to navigate).
- Spaced-repetition tracking: *Mark as Known* (✓) and *Need Revision* (⚡).
- Export printable flashcard sheets to PDF.

### 5. 📚 Study Materials Library
- SQLite-backed persistence with session-based privacy isolation.
- Search by keyword, subject, or topic.
- Category pills filter across Notes, Revision, MCQs, and Flashcards.
- Interactive modal viewer to inspect previous studies or re-take saved quizzes.

### 6. 📄 PDF Export Centre
- Powered by **ReportLab Platypus** with two-pass `NumberedCanvas` rendering.
- Produces clean A4 vector documents with running headers, page numbers ("Page X of Y"), colored metadata banners, and styled question grids.

---

## 🎨 Brand Identity

- **Name**: TESSALYNT
- **Tagline**: *Learn beyond limits.*
- **Logo Concept**: An elegant synthesis of an open textbook (human knowledge), neural network synapses (artificial intelligence), and the apex spark (intellectual enlightenment).
- **Visual Palette**: Midnight Navy background (`#0B0F19`), Deep Indigo accents (`#4F46E5`), Electric Violet (`#8B5CF6`), and Cyan highlight (`#06B6D4`) with subtle glassmorphism and modern Inter typography.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 Glassmorphism, Vanilla JavaScript (ES6+), SVG Vectors |
| **Backend** | Python 3.13 / 3.11+, Flask 3.1 |
| **Artificial Intelligence** | Google Gemini API (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) |
| **Document Publishing** | ReportLab 5.0 (A4 Platypus & NumberedCanvas) |
| **Data Persistence** | SQLite 3 with Session UUID Isolation |
| **WSGI Server** | Gunicorn (Production) |

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/alitrose/WORKSHOP-GENERATIVE-AI.git
cd WORKSHOP-GENERATIVE-AI
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_ENV=development
FLASK_DEBUG=0
SECRET_KEY=generate_a_secure_random_key_here
PORT=5000
```
> **Note**: Obtain a free API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### 5. Run the Application
```bash
python app.py
```
Open your browser at: `http://localhost:5000`

---

## 🧪 Running Automated Tests

Run the complete test suite with `pytest`:
```bash
pytest -v
```

---

## 🔒 Security & Key Management

- **Zero Hardcoded Secrets**: Actual credentials are never committed to version control.
- **Git Protection**: `.env` is explicitly ignored via `.gitignore`.
- **Session Key Override**: Users can optionally supply a session API key in the browser interface without writing to disk.
- **Key Rotation**: If an API key was ever accidentally exposed in previous commits, immediately revoke it in [Google AI Studio](https://aistudio.google.com/app/apikey) and generate a fresh key.

---

## ☁️ Deployment Guide (Render)

Tessalynt is configured for deployment on [Render](https://render.com/).

### Option A: Render Blueprint (Recommended)
1. Push your changes to your GitHub repository.
2. In Render Dashboard, click **New +** -> **Blueprint**.
3. Connect your repository. Render automatically reads `render.yaml`.
4. Under Environment Variables, add `GEMINI_API_KEY`.
5. Click **Apply**.

### Option B: Manual Web Service
- **Environment**: Python
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --workers 2 --threads 4 --timeout 120`
- **Environment Variables**:
  - `FLASK_ENV`: `production`
  - `FLASK_DEBUG`: `0`
  - `SECRET_KEY`: `<secure random string>`
  - `GEMINI_API_KEY`: `<your key from Google AI Studio>`

---

## 📁 Project Structure

```
Tessalynt/
├── .env.example              # Template for environment configuration
├── .gitignore                # Protects secrets, cache, and local databases
├── requirements.txt          # Python dependencies
├── Procfile                  # Process file for production WSGI runners
├── render.yaml               # Render Cloud Blueprint specification
├── README.md                 # Project documentation
├── app.py                    # Main Flask application and API route controllers
├── pro.py                    # Legacy entry point (sanitized and delegating to app.py)
├── test.py                   # Gemini connection diagnostic script
├── services/
│   ├── __init__.py
│   ├── gemini_service.py     # Gemini model cascade, prompts, and JSON parsing
│   ├── pdf_service.py        # ReportLab A4 document generator with NumberedCanvas
│   └── db_service.py         # SQLite persistence for Study Materials Library
├── static/
│   ├── css/
│   │   └── style.css         # Midnight Navy & Indigo Glassmorphic design system
│   ├── js/
│   │   ├── main.js           # API key modal, toasts, status, clipboard & PDF helpers
│   │   ├── notes.js          # Notes generator controller
│   │   ├── revision.js       # Quick revision sprint controller
│   │   ├── mcq.js            # Interactive quiz engine, score evaluation & dual PDFs
│   │   ├── flashcards.js     # 3D interactive flashcards with active-recall state
│   │   └── library.js        # Study materials library with search & modal viewer
│   └── images/
│       ├── logo.svg          # Official Tessalynt vector logo
│       ├── logo-icon.svg     # Compact logo icon (Book + Neural Net + Apex Spark)
│       └── favicon.svg       # Favicon
├── templates/
│   ├── base.html             # Base layout with navbar, footer, modals, and toasts
│   ├── index.html            # Landing page
│   ├── dashboard.html        # Student dashboard with stats & feature launchers
│   ├── notes.html            # AI Academic Notes Generator
│   ├── revision.html         # Quick Revision Studio
│   ├── mcq.html              # MCQ Practice & Assessment
│   ├── flashcards.html       # Interactive 3D Flashcards
│   ├── library.html          # Study Materials Library
│   ├── pdf_centre.html       # Academic PDF Export Centre
│   └── about.html            # About Tessalynt & Product Journey
└── tests/
    └── test_app.py           # Pytest test suite for routes, persistence, and PDFs
```

---

## 📜 License & Credits

- Developed by **Alit Rose M M** as an evolution of the **Google Generative AI Workshop** project.
- Distributed under the MIT License.
