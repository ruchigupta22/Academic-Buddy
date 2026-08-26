"""
backend/api/routes/profile.py
------------------------------
FastAPI routes for Phase 5 — Personalised Learning.

ENDPOINTS:
  POST /api/v1/profile/init           — create/get user
  GET  /api/v1/profile/summary        — full dashboard data
  POST /api/v1/profile/save-quiz      — record a completed quiz
  POST /api/v1/profile/save-chat      — record a chat message
  GET  /api/v1/profile/recommendations — personalised study recs
  GET  /api/v1/profile/ai-message     — LLM-generated advice
  GET  /api/v1/profile/history        — quiz score history for charts
  GET  /api/v1/profile/accuracy       — per-topic accuracy for charts
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional

from backend.user_profile import (
    get_or_create_user,
    get_user_summary,
    save_quiz_attempt,
    save_chat_message,
    get_recommendations,
    generate_ai_recommendation_message,
    get_performance_history,
    get_topic_accuracy_breakdown,
)

router = APIRouter(prefix="/profile", tags=["Personalised Learning"])


# ── Request models ─────────────────────────────────────────────────────────────

class UserInit(BaseModel):
    username: str
    course_code: str


class SaveQuizRequest(BaseModel):
    username: str
    course_code: str
    topic: str
    difficulty: str = "medium"
    questions: List[Dict]       # full question list from quiz generator
    results: Dict[str, Dict]    # {str(idx): {score, max_marks, is_correct}}


class SaveChatRequest(BaseModel):
    username: str
    course_code: str
    question: str
    answer: str
    topic_tag: Optional[str] = None


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post("/init")
async def init_user(body: UserInit):
    """Create or retrieve a user profile."""
    try:
        user = get_or_create_user(body.username, body.course_code)
        return {"status": "ok", "user": user}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.get("/summary")
async def profile_summary(
    username: str = Query(...),
    course_code: str = Query(...),
):
    """
    Full dashboard data for one student.
    Returns quiz stats, weak topics, strong topics, recent activity.
    """
    try:
        return get_user_summary(username, course_code)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.post("/save-quiz")
async def record_quiz(body: SaveQuizRequest):
    """
    Save a completed quiz attempt.
    Called automatically from the frontend after quiz submission.
    Updates weak_topics aggregates.
    """
    try:
        # Convert string keys back to int (JSON keys are always strings)
        results_int = {int(k): v for k, v in body.results.items()}
        attempt_id = save_quiz_attempt(
            username=body.username,
            course_code=body.course_code,
            topic=body.topic,
            difficulty=body.difficulty,
            questions=body.questions,
            results=results_int,
        )
        return {"status": "saved", "attempt_id": attempt_id}
    except Exception as e:
        raise HTTPException(500, f"Error saving quiz: {e}")


@router.post("/save-chat")
async def record_chat(body: SaveChatRequest):
    """Save a chat Q&A for history tracking."""
    try:
        save_chat_message(
            body.username, body.course_code,
            body.question, body.answer, body.topic_tag
        )
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.get("/recommendations")
async def recommendations(
    username: str = Query(...),
    course_code: str = Query(...),
):
    """
    Get personalised study recommendations.
    Weak topics → revise. Medium → practice. Untouched → try quiz.
    Falls back to PYQ frequency if user has < 2 quizzes (cold start).
    """
    try:
        return get_recommendations(username, course_code)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.get("/ai-message")
async def ai_message(
    username: str = Query(...),
    course_code: str = Query(...),
):
    """
    LLM-generated personalised coaching message.
    Uses quiz stats + weak topics to write natural-language advice.
    """
    try:
        msg = generate_ai_recommendation_message(username, course_code)
        return {"message": msg, "username": username}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.get("/history")
async def quiz_history(
    username: str = Query(...),
    course_code: str = Query(...),
):
    """Quiz score history sorted by date — for the progress line chart."""
    try:
        return get_performance_history(username, course_code)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")


@router.get("/accuracy")
async def topic_accuracy(
    username: str = Query(...),
    course_code: str = Query(...),
):
    """Per-topic accuracy breakdown — for the bar chart."""
    try:
        return get_topic_accuracy_breakdown(username, course_code)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")