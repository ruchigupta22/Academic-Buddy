"""
backend/user_profile.py
------------------------
Phase 5 — Personalised Learning Engine.

WHAT THIS FILE DOES:
  Tracks every student interaction and uses it to:
  1. Identify weak topics (low quiz accuracy)
  2. Identify strong topics (high quiz accuracy)
  3. Track chat patterns (what they ask about most)
  4. Generate personalised study recommendations
  5. Show a learning dashboard with progress over time

DATA FLOW:
  Student takes quiz
       ↓
  save_quiz_attempt()     ← stores quiz_attempts + quiz_responses rows
       ↓
  update_weak_topics()    ← recalculates accuracy per topic
       ↓
  get_recommendations()   ← reads weak_topics → suggests what to do next

  Student asks a question
       ↓
  save_chat_message()     ← stores chat_history row
       ↓
  (used in dashboard: "You ask about heat transfer the most")

RECOMMENDATION ENGINE (interview-ready explanation):
  We use a simple rule-based system (not ML) for Phase 5:

  Weak topic   = accuracy < 50%  → "Revise this topic"
  Medium topic = accuracy 50-79% → "Practice more questions"
  Strong topic = accuracy >= 80% → "You're good here"
  Untouched    = never attempted → "Try a quiz on this"

  In a real production system, you'd use collaborative filtering
  (users similar to you also struggled with X) or knowledge graphs.
  For an interview, explaining this progression shows maturity:
  Rule-based → Statistical → ML-based recommendations.

COLD START SOLUTION:
  New user with no quiz history → fall back to PYQ frequency data
  (Phase 2). Recommend the most-asked exam topics first.
  This is how Spotify recommends popular songs to new users.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from backend.llm.provider import generate_text
from backend.db.sql_client import get_db
from backend.rag.pyq_analytics import get_topic_frequency
from backend.config import settings


# ══════════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def get_or_create_user(username: str, course_code: str) -> Dict:
    """
    Get existing user or create new one.
    Returns the user row as a dict.
    """
    username = username.strip().lower()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()

        if row:
            return dict(row)

        conn.execute(
            "INSERT INTO users (username, course_code) VALUES (?, ?)",
            (username, course_code.upper()),
        )
        return {"username": username, "course_code": course_code.upper()}


def get_user_summary(username: str, course_code: str) -> Dict[str, Any]:
    """
    Full profile summary — used for the dashboard.
    Returns: quiz stats, chat count, weak topics, strong topics.
    """
    username = username.strip().lower()
    code = course_code.upper()

    with get_db() as conn:
        # Quiz stats
        quiz_stats = conn.execute("""
            SELECT
                COUNT(*)            AS total_quizzes,
                ROUND(AVG(pct_score),1) AS avg_score,
                MAX(pct_score)      AS best_score,
                SUM(total_marks)    AS total_marks_attempted,
                SUM(scored_marks)   AS total_marks_scored
            FROM quiz_attempts
            WHERE username = ? AND course_code = ?
        """, (username, code)).fetchone()

        # Chat count
        chat_count = conn.execute("""
            SELECT COUNT(*) AS count FROM chat_history
            WHERE username = ? AND course_code = ?
        """, (username, code)).fetchone()

        # Recent quiz attempts
        recent_quizzes = conn.execute("""
            SELECT topic, difficulty, pct_score, scored_marks, total_marks, attempted_at
            FROM quiz_attempts
            WHERE username = ? AND course_code = ?
            ORDER BY attempted_at DESC LIMIT 5
        """, (username, code)).fetchall()

        # Weak topics (accuracy < 50%)
        weak = conn.execute("""
            SELECT topic, total_attempts, correct_count, wrong_count, accuracy_pct
            FROM weak_topics
            WHERE username = ? AND course_code = ? AND accuracy_pct < 50
              AND total_attempts >= 2
            ORDER BY accuracy_pct ASC LIMIT 8
        """, (username, code)).fetchall()

        # Strong topics (accuracy >= 80%)
        strong = conn.execute("""
            SELECT topic, total_attempts, accuracy_pct
            FROM weak_topics
            WHERE username = ? AND course_code = ? AND accuracy_pct >= 80
              AND total_attempts >= 2
            ORDER BY accuracy_pct DESC LIMIT 5
        """, (username, code)).fetchall()

        # Most asked topics in chat
        chat_topics = conn.execute("""
            SELECT topic_tags, COUNT(*) AS freq
            FROM chat_history
            WHERE username = ? AND course_code = ? AND topic_tags IS NOT NULL
            GROUP BY topic_tags ORDER BY freq DESC LIMIT 5
        """, (username, code)).fetchall()

    return {
        "username": username,
        "course_code": code,
        "quiz_stats": dict(quiz_stats) if quiz_stats else {},
        "chat_count": dict(chat_count).get("count", 0) if chat_count else 0,
        "recent_quizzes": [dict(r) for r in recent_quizzes],
        "weak_topics": [dict(r) for r in weak],
        "strong_topics": [dict(r) for r in strong],
        "chat_topics": [dict(r) for r in chat_topics],
    }


# ══════════════════════════════════════════════════════════════════════════════
# TRACKING — called automatically after quiz submit and chat
# ══════════════════════════════════════════════════════════════════════════════

def save_quiz_attempt(
    username: str,
    course_code: str,
    topic: str,
    difficulty: str,
    questions: List[Dict],      # full question list
    results: Dict[int, Dict],   # {idx: {score, max_marks, is_correct}}
) -> int:
    """
    Save a completed quiz attempt to the database.
    Returns the attempt_id for linking individual responses.

    Called from the frontend after the student submits a quiz.
    """
    username = username.strip().lower()
    code = course_code.upper()

    total_marks = sum(q.get("marks", 2) for q in questions)
    scored_marks = sum(r.get("score", 0) for r in results.values())
    pct = round((scored_marks / total_marks * 100) if total_marks else 0, 1)

    # Insert attempt
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO quiz_attempts
                (username, course_code, topic, difficulty, total_marks, scored_marks, pct_score)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username, code, topic, difficulty, total_marks, scored_marks, pct))
        attempt_id = cursor.lastrowid

    # Insert per-question responses
    with get_db() as conn:
        for idx, q in enumerate(questions):
            result = results.get(idx, {})
            is_correct = 1 if result.get("is_correct") else 0
            conn.execute("""
                INSERT INTO quiz_responses
                    (attempt_id, username, course_code, topic, question_type,
                     is_correct, marks_scored, marks_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                attempt_id, username, code,
                q.get("topic", topic),      # use question-level topic if available
                q.get("type", "mcq"),
                is_correct,
                result.get("score", 0),
                q.get("marks", 2),
            ))

    # Recalculate weak_topics aggregates
    _update_weak_topics(username, code, questions, results, topic)

    return attempt_id


def _update_weak_topics(
    username: str,
    course_code: str,
    questions: List[Dict],
    results: Dict[int, Dict],
    default_topic: str,
):
    """
    Upsert the weak_topics table after a quiz.
    Uses INSERT OR REPLACE to update existing rows or create new ones.

    UPSERT PATTERN (interview concept):
      INSERT OR REPLACE handles "insert if new, update if exists"
      in a single SQL statement — no need for separate SELECT first.
    """
    # Group results by topic
    topic_stats: Dict[str, Dict] = {}

    for idx, q in enumerate(questions):
        t = q.get("topic", default_topic)
        result = results.get(idx, {})
        correct = 1 if result.get("is_correct") else 0

        if t not in topic_stats:
            topic_stats[t] = {"attempts": 0, "correct": 0, "wrong": 0}

        topic_stats[t]["attempts"] += 1
        topic_stats[t]["correct"]  += correct
        topic_stats[t]["wrong"]    += (1 - correct)

    with get_db() as conn:
        for topic, stats in topic_stats.items():
            # Get existing row
            existing = conn.execute("""
                SELECT total_attempts, correct_count, wrong_count
                FROM weak_topics
                WHERE username = ? AND course_code = ? AND topic = ?
            """, (username, course_code, topic)).fetchone()

            if existing:
                new_attempts = existing["total_attempts"] + stats["attempts"]
                new_correct  = existing["correct_count"]  + stats["correct"]
                new_wrong    = existing["wrong_count"]    + stats["wrong"]
            else:
                new_attempts = stats["attempts"]
                new_correct  = stats["correct"]
                new_wrong    = stats["wrong"]

            accuracy = round((new_correct / new_attempts * 100) if new_attempts else 0, 1)

            conn.execute("""
                INSERT INTO weak_topics
                    (username, course_code, topic, total_attempts, correct_count,
                     wrong_count, accuracy_pct, last_attempted)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(username, course_code, topic) DO UPDATE SET
                    total_attempts = ?,
                    correct_count  = ?,
                    wrong_count    = ?,
                    accuracy_pct   = ?,
                    last_attempted = CURRENT_TIMESTAMP
            """, (
                username, course_code, topic,
                new_attempts, new_correct, new_wrong, accuracy,
                new_attempts, new_correct, new_wrong, accuracy,
            ))


def save_chat_message(
    username: str,
    course_code: str,
    question: str,
    answer: str,
    topic_tag: str = None,
):
    """
    Save a chat Q&A to history for dashboard analytics.
    topic_tag is inferred by the chat route (optional).
    """
    with get_db() as conn:
        conn.execute("""
            INSERT INTO chat_history (username, course_code, question, answer, topic_tags)
            VALUES (?, ?, ?, ?, ?)
        """, (username.strip().lower(), course_code.upper(), question, answer, topic_tag))


# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════════════

def get_recommendations(username: str, course_code: str) -> Dict[str, Any]:
    """
    Generate personalised study recommendations.

    LOGIC (rule-based):
      1. Weak topics (accuracy < 50%, ≥2 attempts) → "Revise + retry quiz"
      2. Medium topics (accuracy 50-79%) → "Practice more"
      3. Untouched high-freq PYQ topics → "Try a quiz on this"
      4. Strong topics → "You're good — focus elsewhere"

    COLD START:
      If user has < 2 quiz attempts, fall back to PYQ frequency ranking.
    """
    username = username.strip().lower()
    code = course_code.upper()

    with get_db() as conn:
        quiz_count = conn.execute(
            "SELECT COUNT(*) AS c FROM quiz_attempts WHERE username=? AND course_code=?",
            (username, code)
        ).fetchone()["c"]

        all_topics = conn.execute("""
            SELECT topic, total_attempts, accuracy_pct, wrong_count
            FROM weak_topics
            WHERE username=? AND course_code=?
            ORDER BY accuracy_pct ASC
        """, (username, code)).fetchall()

    recs = []

    # ── Cold start: no quiz history yet ───────────────────────────────────────
    if quiz_count < 2:
        pyq_topics = get_topic_frequency(code, limit=5)
        for t in pyq_topics:
            recs.append({
                "topic": t["topic"],
                "reason": f"High-frequency exam topic (asked {t['frequency']}× in PYQs)",
                "action": "Take a quiz",
                "priority": "high",
                "accuracy": None,
            })
        return {
            "mode": "cold_start",
            "message": "Take a few quizzes to unlock personalised recommendations!",
            "recommendations": recs,
            "quiz_count": quiz_count,
        }

    # ── Personalised: use quiz history ────────────────────────────────────────
    attempted_topics = {row["topic"] for row in all_topics}

    # Weak topics → must revise
    for row in all_topics:
        if row["accuracy_pct"] < 50 and row["total_attempts"] >= 2:
            recs.append({
                "topic": row["topic"],
                "reason": f"You got {row['accuracy_pct']:.0f}% accuracy ({row['wrong_count']} wrong answers)",
                "action": "Revise notes, then retake quiz",
                "priority": "high",
                "accuracy": row["accuracy_pct"],
            })

    # Medium topics → need more practice
    for row in all_topics:
        if 50 <= row["accuracy_pct"] < 80 and row["total_attempts"] >= 2:
            recs.append({
                "topic": row["topic"],
                "reason": f"You scored {row['accuracy_pct']:.0f}% — close but needs more practice",
                "action": "Practice 5 more questions",
                "priority": "medium",
                "accuracy": row["accuracy_pct"],
            })

    # Untouched high-PYQ topics
    pyq_topics = get_topic_frequency(code, limit=10)
    for t in pyq_topics:
        if t["topic"] not in attempted_topics:
            recs.append({
                "topic": t["topic"],
                "reason": f"You've never attempted this — asked {t['frequency']}× in PYQs",
                "action": "Take a quiz on this topic",
                "priority": "medium",
                "accuracy": None,
            })

    return {
        "mode": "personalised",
        "message": f"Based on your {quiz_count} quizzes:",
        "recommendations": recs[:10],   # Top 10
        "quiz_count": quiz_count,
    }


def generate_ai_recommendation_message(username: str, course_code: str) -> str:
    """
    Generate a friendly, personalised message using Gemini.
    Combines quiz stats + weak topics into natural language advice.

    INTERVIEW: "LLM for personalisation"
      We don't ask the LLM to DECIDE what to recommend (that's rule-based).
      We give it the DECISION (weak topics list) and ask it to PHRASE it
      naturally. This keeps recommendations accurate while making them
      feel personal and motivating — not like a robot output.
    """
    summary = get_user_summary(username, course_code)
    recs = get_recommendations(username, course_code)

    if not summary["quiz_stats"].get("total_quizzes"):
        return f"Welcome, {username}! Upload your lecture notes and take your first quiz to get personalised recommendations."

    prompt = f"""You are a friendly, encouraging academic coach.

Student: {username}
Course: {course_code}
Quizzes taken: {summary['quiz_stats'].get('total_quizzes', 0)}
Average score: {summary['quiz_stats'].get('avg_score', 0):.0f}%
Best score: {summary['quiz_stats'].get('best_score', 0):.0f}%

Weak topics (accuracy < 50%):
{json.dumps([t['topic'] for t in summary['weak_topics']], indent=2)}

Strong topics (accuracy >= 80%):
{json.dumps([t['topic'] for t in summary['strong_topics']], indent=2)}

Top recommendations:
{json.dumps([r['topic'] + ' — ' + r['reason'] for r in recs['recommendations'][:4]], indent=2)}

Write a SHORT (4-6 sentences), encouraging personalised message:
- Acknowledge their effort
- Be specific about what they're weak at
- Give 2-3 concrete next steps
- End with a motivating line
- Use their name
- Do NOT use bullet points — write in natural paragraphs"""

    result = generate_text(prompt, temperature=0.6, max_tokens=256)
    return result["text"].strip()


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE HISTORY (for charts)
# ══════════════════════════════════════════════════════════════════════════════

def get_performance_history(username: str, course_code: str) -> List[Dict]:
    """
    Quiz scores over time — used to draw the progress chart.
    Returns list sorted oldest → newest.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT topic, difficulty, pct_score, scored_marks, total_marks,
                   attempted_at
            FROM quiz_attempts
            WHERE username = ? AND course_code = ?
            ORDER BY attempted_at ASC
        """, (username.strip().lower(), course_code.upper())).fetchall()

    return [dict(r) for r in rows]


def get_topic_accuracy_breakdown(username: str, course_code: str) -> List[Dict]:
    """
    Per-topic accuracy — used to draw the bar chart on the dashboard.
    """
    with get_db() as conn:
        rows = conn.execute("""
            SELECT topic, total_attempts, accuracy_pct, correct_count, wrong_count
            FROM weak_topics
            WHERE username = ? AND course_code = ? AND total_attempts >= 1
            ORDER BY accuracy_pct ASC
        """, (username.strip().lower(), course_code.upper())).fetchall()

    return [dict(r) for r in rows]