
from typing import List, Dict, Any
from backend.db.sql_client import get_db


def get_topic_frequency(course_code: str, limit: int = 15) -> List[Dict[str, Any]]:
    """
    Rank topics by how many times they appear across all PYQ papers.

    SQL: GROUP BY topic → COUNT appearances → ORDER BY most frequent
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                topic,
                COUNT(*)                                  AS frequency,
                SUM(marks)                                AS total_marks,
                ROUND(AVG(marks), 1)                      AS avg_marks,
                GROUP_CONCAT(DISTINCT year ORDER BY year) AS years_appeared,
                GROUP_CONCAT(DISTINCT question_type)      AS question_types
            FROM pyq_questions
            WHERE course_code = ?
            GROUP BY topic
            ORDER BY frequency DESC, total_marks DESC
            LIMIT ?
        """, (course_code.upper(), limit)).fetchall()

    return [dict(row) for row in rows]


def get_high_value_topics(course_code: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Topics ranked by TOTAL MARKS ever awarded — not just frequency.

    WHY THIS MATTERS:
      Topic A asked 5 times × 2 marks = 10 total marks
      Topic B asked 2 times × 8 marks = 16 total marks
      Topic B is more important for scoring even though asked less often.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                topic,
                COUNT(*)   AS frequency,
                SUM(marks) AS total_marks,
                MAX(marks) AS max_marks,
                GROUP_CONCAT(DISTINCT question_type) AS types
            FROM pyq_questions
            WHERE course_code = ? AND marks > 0
            GROUP BY topic
            ORDER BY total_marks DESC
            LIMIT ?
        """, (course_code.upper(), limit)).fetchall()

    return [dict(row) for row in rows]


def get_topic_trend(course_code: str, topic: str) -> List[Dict[str, Any]]:
    """
    Year-by-year frequency of one specific topic.
    Answers: "Is heat transfer asked more in recent years?"
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT year, COUNT(*) AS count, SUM(marks) AS total_marks
            FROM pyq_questions
            WHERE course_code = ? AND year IS NOT NULL AND topic LIKE ?
            GROUP BY year
            ORDER BY year
        """, (course_code.upper(), f"%{topic}%")).fetchall()

    return [dict(row) for row in rows]


def get_type_distribution(course_code: str) -> List[Dict[str, Any]]:
    """
    Breakdown: how many numerical vs theory vs derivation questions?
    Tells students what TYPE of questions to practice.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT
                question_type,
                COUNT(*)            AS count,
                SUM(marks)          AS total_marks,
                ROUND(AVG(marks),1) AS avg_marks
            FROM pyq_questions
            WHERE course_code = ?
            GROUP BY question_type
            ORDER BY count DESC
        """, (course_code.upper(),)).fetchall()

    return [dict(row) for row in rows]


def get_available_years(course_code: str) -> List[int]:
    """All years for which PYQ data exists for this course."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT DISTINCT year FROM pyq_questions
            WHERE course_code = ? AND year IS NOT NULL
            ORDER BY year DESC
        """, (course_code.upper(),)).fetchall()

    return [row["year"] for row in rows]


def get_full_summary(course_code: str) -> Dict[str, Any]:
    """
    All analytics in one dict.
    Passed to the LLM to generate a natural-language report.
    """
    return {
        "top_topics":       get_topic_frequency(course_code, limit=10),
        "high_value":       get_high_value_topics(course_code, limit=8),
        "type_distribution": get_type_distribution(course_code),
        "years_covered":    get_available_years(course_code),
    }