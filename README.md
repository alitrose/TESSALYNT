# TESSALYNT
### *Learn Beyond Limits.*

A modern AI-powered learning platform that transforms study materials into structured notes, revision resources, interactive quizzes and flashcards.

---

### 🚀 **LIVE DEMO**: [**Visit TESSALYNT Web App**](https://tessalynt-ai-platform.onrender.com)
### 💻 **GitHub Repository**: [**View Source Code**](https://github.com/alitrose/TESSALYNT)
### 🌐 **Try TESSALYNT Online**: [**https://tessalynt-ai-platform.onrender.com**](https://tessalynt-ai-platform.onrender.com)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render%20Online-success?style=for-the-badge&logo=render&logoColor=white)](https://tessalynt-ai-platform.onrender.com)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.1-black.svg?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-orange.svg?style=for-the-badge&logo=googlegemini&logoColor=white)](https://ai.google.dev/)
[![ReportLab](https://img.shields.io/badge/PDF-ReportLab%205.0-red.svg?style=for-the-badge)](https://www.reportlab.com/)

---

## 🌟 Accessing the Live Application

Anyone can access and use **TESSALYNT** directly in their web browser without cloning the repository or running any local setup:

> 👉 **Official Web Application**: [**https://tessalynt-ai-platform.onrender.com**](https://tessalynt-ai-platform.onrender.com)

1. Open the [Live Demo](https://tessalynt-ai-platform.onrender.com).
2. Choose a learning studio from the navigation bar or dashboard (**AI Notes**, **Quick Revision**, **MCQ Quiz**, **Flashcards**, or **Library**).
3. Input your academic subject and topic.
4. Generate textbook-aligned notes, take interactive quizzes, practice active-recall flashcards, and download publication-ready PDFs.

---

## 📖 About Tessalynt

**Tessalynt** is an AI-powered personalized educational platform engineered to elevate university learning, semester examination prep, and cognitive retention. 

Originating from an experimental project developed during a **Google Generative AI Workshop**, Tessalynt has been completely re-architected into an enterprise-grade full-stack SaaS platform featuring:
- High-yield syllabus alignment across Engineering, Sciences, Medicine, and Humanities.
- A 13-section pedagogical framework for exhaustive academic comprehension.
- Blind multiple-choice assessment quizzes with instant scoring and detailed step-by-step rationales.
- Active-recall 3D flashcards with retention tracking (*Mark as Known* / *Need Revision*).
- Publication-quality vector PDF generation using ReportLab Platypus and two-pass `NumberedCanvas`.
- Local persistence using SQLite with session-isolated UUID partitioning for student data privacy.

---

## 🎨 Brand Identity

- **Official Name**: TESSALYNT
- **Tagline**: *Learn Beyond Limits.*
- **Logo Concept**: Dynamic union of an **Open Book** (foundational textbook knowledge), **Neural Synaptic Connections** (artificial intelligence), and the **Apex Spark** (intellectual illumination).
- **Design Language**: Midnight Navy background (`#0B0F19`), Deep Indigo accents (`#4F46E5`), Electric Violet (`#8B5CF6`), and Cyan highlight (`#06B6D4`) with subtle glassmorphic elevation and Inter typography.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 Glassmorphism, Vanilla JavaScript (ES6+), SVG Vector Assets |
| **Backend** | Python 3.13 / 3.11+, Flask 3.1 WSGI Framework |
| **Artificial Intelligence** | Google Gemini API (`gemini-3.8-flash`, `gemini-2.5-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`) with dynamic model discovery |
| **Document Publishing** | ReportLab 5.0 (A4 Platypus with two-pass dynamic page numbering) |
| **Data Persistence** | SQLite 3 with Session UUID Isolation |
| **Production WSGI Server** | Gunicorn |
| **Cloud Hosting** | Render Cloud Platform |

---

## 📚 Core Features & Learning Studios

### 1. 📝 AI Academic Notes Generator
- **13 Standard Textbook Sections**:
  1. Introduction & Academic Context
  2. Formal Definition & Technical Terminology
  3. Detailed Explanation
  4. Core Concepts & Taxonomy
  5. Types and Classifications
  6. Working Principles & Mechanisms
  7. Real-World Examples & Case Studies
  8. Advantages & Strengths
  9. Limitations & Disadvantages
  10. Practical Applications & Industry Usage
  11. Key Takeaways & Exam Points
  12. Conclusion & Summary
  13. Frequently Asked University Examination Questions (FAQs with model answers)
- Contextualized by Degree/Stream, Department, Year, and Semester.
- Instant actions: **Copy to Clipboard**, **Download TXT**, **Download ReportLab PDF**, **Print**, and **Regenerate**.

### 2. ⚡ AI Quick Revision Module
- Last-minute study sheets for exam sprints.
- Features 60-second executive summaries, essential definitions, formula & syntax cheat sheets, examiner traps, and 5-minute pre-exam checklists.

### 3. 🎯 Smart MCQ Generator & Quiz System
- Generates 5 to 20 multiple-choice questions per assessment with calibrated cognitive difficulty (*Easy*, *Medium*, *Hard*).
- **Strict Blind Testing Protocol**: Correct answers and rationales are withheld until submission.
- Real-time score grading, percentage calculations, performance badges, and in-depth rationales for every option.
- **Dual PDF Publishing**:
  1. *MCQ Question Paper* (clean test sheet with candidate instructions and answer marking brackets `[   ]`).
  2. *MCQ Answer Key & Explanations Manual* (with quick-scoring matrix and complete pedagogical rationales).

### 4. 🃏 Interactive 3D Flashcard Studio
- Active-recall cognitive cards with smooth 3D flip physics.
- Shuffle mode and keyboard shortcuts (`Space` to flip, `Arrow Left/Right` to navigate).
- Spaced-repetition tracking: *Mark as Known* (✓) and *Need Revision* (⚡).
- Export printable flashcard sheets to PDF.

### 5. 📚 Study Materials Library
- SQLite-backed persistence with session-based privacy isolation.
- Live search by keyword, subject, or topic.
- Category filters (*All*, *Notes*, *Revision*, *MCQs*, *Flashcards*).
- Interactive modal viewer to inspect previous studies or re-take saved quizzes.

### 6. 📄 PDF Export Centre
- Centralized publishing studio for all 5 document types.
- Engineered with ReportLab Platypus and a custom `NumberedCanvas` computing dynamic `"Page X of Y"`, running brand headers, metadata banners, and wrapped tables.

---

## 💻 Local Installation & Setup

If you prefer to run Tessalynt locally on your machine:

### 1. Clone the Repository
```bash
git clone https://github.com/alitrose/TESSALYNT.git
cd TESSALYNT
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

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

### 5. Run the Local Development Server
```bash
python app.py
```
Open your browser at: `http://localhost:5000`

---

## 🧪 Automated Testing

Run the complete test suite with `pytest`:
```bash
pytest -v
```
All 9 core integration and unit tests pass with zero warnings:
- Landing Page & Dashboard rendering
- Learning Studios route verification
- API Status & Input validation
- Secret isolation & Key security
- SQLite CRUD & Session isolation
- ReportLab PDF byte streaming
- Plain-text document downloads

---

## 🔒 Security & Credential Isolation

- **Zero Hardcoded Secrets**: Actual credentials are never committed to version control.
- **Git Protection**: `.env` is explicitly ignored via `.gitignore`.
- **Purged Commit History**: Past workshop commits have been scrubbed to ensure no leaked keys exist in the git log.
- **Client Safety**: API credentials are never bundled into client-side code or HTML responses.
- **Session Key Override**: Users can optionally supply a session API key in the browser interface without writing to disk.

---

## ☁️ Deployment Architecture (Render)

Tessalynt is continuously deployed on [Render](https://render.com/).

- **Repository**: `https://github.com/alitrose/TESSALYNT`
- **Branch**: `main`
- **Service Name**: `tessalynt-ai-platform`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --workers 2 --threads 4 --timeout 120`
- **Live URL**: [https://tessalynt-ai-platform.onrender.com](https://tessalynt-ai-platform.onrender.com)

---

## 📜 License & Credits

- Developed by **Alit Rose M M** as an evolution of the **Google Generative AI Workshop** project.
- Distributed under the MIT License.
