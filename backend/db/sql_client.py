import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path("./backend/studyai.db")

@contextmanager
def get_db():
    """
    Safe database connection using context manager.

    WHY CONTEXT MANAGER?
      Guarantees the connection closes even if an error occurs.
      Auto-commits on success, auto-rollbacks on failure.

    Usage:
        with get_db() as conn:
            conn.execute("INSERT INTO ...")
        # auto committed and closed here
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # rows act like dicts: row["topic"]
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """
    Create tables if they don't exist.
    Call this ONCE at app startup.
    Safe to call multiple times — IF NOT EXISTS prevents duplicates.
    """
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS pyq_papers (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT    NOT NULL,
                filename    TEXT    NOT NULL,
                year        INTEGER,
                exam_type   TEXT,
                uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS pyq_questions (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                paper_id      INTEGER NOT NULL REFERENCES pyq_papers(id),
                course_code   TEXT    NOT NULL,
                year          INTEGER,
                topic         TEXT    NOT NULL,
                subtopic      TEXT,
                question_type TEXT,
                marks         INTEGER,
                raw_question  TEXT,
                difficulty    TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                course_code TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, course_code)
            );

            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                course_code TEXT NOT NULL,
                topic TEXT NOT NULL,
                difficulty TEXT,
                total_marks INTEGER NOT NULL,
                scored_marks INTEGER NOT NULL,
                pct_score REAL NOT NULL,
                attempted_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS quiz_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL REFERENCES quiz_attempts(id) ON DELETE CASCADE,
                username TEXT NOT NULL,
                course_code TEXT NOT NULL,
                topic TEXT NOT NULL,
                question_type TEXT,
                is_correct INTEGER NOT NULL,
                marks_scored INTEGER NOT NULL,
                marks_total INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS weak_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                course_code TEXT NOT NULL,
                topic TEXT NOT NULL,
                total_attempts INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                wrong_count INTEGER NOT NULL,
                accuracy_pct REAL NOT NULL,
                last_attempted DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(username, course_code, topic)
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                course_code TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                topic_tags TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_course ON pyq_questions(course_code);
            CREATE INDEX IF NOT EXISTS idx_topic ON pyq_questions(topic);
            CREATE INDEX IF NOT EXISTS idx_year ON pyq_questions(year);
            CREATE INDEX IF NOT EXISTS idx_quiz_user ON quiz_attempts(username, course_code);
            CREATE INDEX IF NOT EXISTS idx_quiz_topic ON quiz_attempts(topic);
            CREATE INDEX IF NOT EXISTS idx_resp_attempt ON quiz_responses(attempt_id);
            CREATE INDEX IF NOT EXISTS idx_weak_user ON weak_topics(username, course_code);
            CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(username, course_code);
        """)

