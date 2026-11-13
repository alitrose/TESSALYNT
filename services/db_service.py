"""
Tessalynt - SQLite Database Service
Manages local persistence for generated study materials with session-based isolation.
"""
import os
import sqlite3
import json
from datetime import datetime, timezone

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance")
DB_PATH = os.path.join(DB_DIR, "tessalynt.db")


def get_db_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema if not present."""
    os.makedirs(DB_DIR, exist_ok=True)
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                material_type TEXT NOT NULL, /* notes, revision, mcq, flashcards */
                title TEXT NOT NULL,
                subject TEXT NOT NULL,
                topic TEXT NOT NULL,
                stream TEXT,
                department TEXT,
                academic_year TEXT,
                semester TEXT,
                difficulty TEXT,
                content_text TEXT,
                content_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def save_material(session_id, material_type, title, subject, topic, 
                  content_text=None, content_json=None, stream="", 
                  department="", academic_year="", semester="", difficulty=""):
    """Saves a study material record."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO study_materials (
                session_id, material_type, title, subject, topic,
                stream, department, academic_year, semester, difficulty,
                content_text, content_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            material_type,
            title,
            subject,
            topic,
            stream,
            department,
            academic_year,
            semester,
            difficulty,
            content_text if content_text else "",
            json.dumps(content_json) if content_json is not None else "",
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return cursor.lastrowid


def get_materials(session_id=None, search=None, material_type=None, limit=50):
    """Retrieves saved materials with optional filtering by type, search keyword, and session."""
    init_db()
    query = "SELECT * FROM study_materials WHERE 1=1"
    params = []

    if session_id:
        query += " AND (session_id = ? OR session_id = 'public')"
        params.append(session_id)

    if material_type and material_type.lower() != "all":
        query += " AND material_type = ?"
        params.append(material_type.lower())

    if search and search.strip():
        term = f"%{search.strip()}%"
        query += " AND (title LIKE ? OR subject LIKE ? OR topic LIKE ? OR stream LIKE ?)"
        params.extend([term, term, term, term])

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_db_connection() as conn:
        rows = conn.execute(query, params).fetchall()
        materials = []
        for r in rows:
            item = dict(r)
            if item.get("content_json"):
                try:
                    item["content_json"] = json.loads(item["content_json"])
                except Exception:
                    pass
            materials.append(item)
        return materials


def get_material_by_id(material_id, session_id=None):
    """Retrieves a single material by ID."""
    init_db()
    query = "SELECT * FROM study_materials WHERE id = ?"
    params = [material_id]
    if session_id:
        query += " AND (session_id = ? OR session_id = 'public')"
        params.append(session_id)

    with get_db_connection() as conn:
        row = conn.execute(query, params).fetchone()
        if not row:
            return None
        item = dict(row)
        if item.get("content_json"):
            try:
                item["content_json"] = json.loads(item["content_json"])
            except Exception:
                pass
        return item


def delete_material(material_id, session_id=None):
    """Deletes a material by ID."""
    init_db()
    query = "DELETE FROM study_materials WHERE id = ?"
    params = [material_id]
    if session_id:
        query += " AND (session_id = ? OR session_id = 'public')"
        params.append(session_id)

    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0


def get_stats(session_id=None):
    """Returns count of materials for dashboard stats."""
    init_db()
    base_query = "SELECT material_type, COUNT(*) as cnt FROM study_materials"
    params = []
    if session_id:
        base_query += " WHERE (session_id = ? OR session_id = 'public')"
        params.append(session_id)
    base_query += " GROUP BY material_type"

    stats = {
        "total": 0,
        "notes": 0,
        "revision": 0,
        "mcq": 0,
        "flashcards": 0
    }
    with get_db_connection() as conn:
        rows = conn.execute(base_query, params).fetchall()
        for r in rows:
            mtype = r["material_type"]
            cnt = r["cnt"]
            stats[mtype] = cnt
            stats["total"] += cnt
    return stats
