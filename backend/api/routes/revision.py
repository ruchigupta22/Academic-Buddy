from fastapi import APIRouter, HTTPException, Query
from backend.revision_engine import (
    get_priority_topics,
    build_study_plan,
    generate_formula_sheet,
    generate_revision_notes,
    get_confused_concepts,
    generate_revision_package,
)
 
router = APIRouter(prefix="/revision", tags=["Exam Revision"])
 
 
@router.get("/priority")
async def priority_topics(
    course_code: str = Query(..., example="CHE301"),
    days_left: int = Query(..., ge=1, le=30, example=3),
):
    """
    Get topics ranked by exam importance using PYQ analytics.
    Combines frequency + total marks into a priority score.
    """
    try:
        return get_priority_topics(course_code.upper(), days_left)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
 
@router.get("/plan")
async def study_plan(
    course_code: str = Query(..., example="CHE301"),
    days_left: int = Query(..., ge=1, le=30, example=3),
    hours_per_day: int = Query(default=4, ge=1, le=12, example=4),
):
    """
    Generate a day-by-day study schedule.
    Packs priority topics into days based on available hours.
    Last day is always reserved for revision + PYQ practice.
    """
    try:
        return build_study_plan(course_code.upper(), days_left, hours_per_day)
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
 
@router.get("/formula-sheet")
async def formula_sheet(
    course_code: str = Query(..., example="CHE301"),
):
    """
    Extract all formulas and equations from uploaded lecture notes.
    Returns a clean, exam-ready formula reference sheet.
    """
    try:
        result = generate_formula_sheet(course_code.upper())
        return {"formula_sheet": result, "course_code": course_code.upper()}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
 
@router.get("/notes")
async def revision_notes(
    course_code: str = Query(..., example="CHE301"),
    topic: str = Query(..., example="Fick's Law of Diffusion"),
):
    """
    Generate concise revision notes for a specific topic.
    Includes key formulas, common mistakes, and exam tips.
    Written for someone who already studied — quick recall format.
    """
    try:
        result = generate_revision_notes(course_code.upper(), topic)
        return {"notes": result, "topic": topic, "course_code": course_code.upper()}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
 
@router.get("/confused")
async def confused_concepts(
    course_code: str = Query(..., example="CHE301"),
):
    """
    Identify pairs of concepts students commonly confuse.
    Includes memory tricks to keep them straight.
    """
    try:
        result = get_confused_concepts(course_code.upper())
        return {"confused_concepts": result, "course_code": course_code.upper()}
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
 
@router.get("/full-package")
async def full_package(
    course_code: str = Query(..., example="CHE301"),
    days_left: int = Query(..., ge=1, le=30, example=3),
    hours_per_day: int = Query(default=4, ge=1, le=12, example=4),
):
    """
    Generate the complete revision package in one call.
    Returns: priority topics + study plan + formula sheet + confused concepts.
    Use individual endpoints for progressive loading.
    """
    try:
        return generate_revision_package(
            course_code.upper(), days_left, hours_per_day
        )
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 