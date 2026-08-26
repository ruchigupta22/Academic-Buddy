from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from backend.quiz_generator import generate_quiz
#from backend.config import settings
#import google.generativeai as genai
from backend.llm.provider import generate_text
#genai.configure(api_key=settings.GEMINI_API_KEY)
 
router = APIRouter(prefix="/quiz", tags=["Quiz Generator"])

class QuizRequest(BaseModel):
    course_code: str = Field(example="CHE301")
    topic: str = Field(example="Fick's Law of Diffusion", min_length=2)
    question_types: List[str] = Field(
        default=["mcq", "short", "numerical"],
        example=["mcq", "short", "numerical"],
        description="Any combination of: mcq, short, numerical"
    )
    count_per_type: int = Field(default=3, ge=1, le=10)
    difficulty: str = Field(default="medium", example="medium",
                            description="easy | medium | hard")
 
 
class AnswerCheckRequest(BaseModel):
    question: str
    question_type: str          # mcq | short | numerical
    model_answer: str
    student_answer: str
    marks: int = 5
 
 
class AnswerCheckResponse(BaseModel):
    score: int                  # out of marks
    max_marks: int
    feedback: str
    is_correct: bool


@router.post("/generate")
async def generate(request: QuizRequest):
    """
    Generate a quiz on any topic from uploaded course material.
 
    The system:
    1. Retrieves relevant chunks from ChromaDB for the topic
    2. Sends those chunks to Gemini as context
    3. Gemini writes exam-style questions from YOUR notes
    """
    # Validate difficulty
    if request.difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(400, "difficulty must be 'easy', 'medium', or 'hard'")
 
    # Validate question types
    valid_types = {"mcq", "short", "numerical"}
    bad = [t for t in request.question_types if t not in valid_types]
    if bad:
        raise HTTPException(400, f"Invalid question types: {bad}. Use: mcq, short, numerical")
 
    try:
        result = generate_quiz(
            course_code=request.course_code.upper().strip(),
            topic=request.topic,
            question_types=request.question_types,
            count_per_type=request.count_per_type,
            difficulty=request.difficulty,
        )
    except Exception as e:
        raise HTTPException(500, f"Quiz generation failed: {e}")
 
    return result
 
 
@router.post("/check", response_model=AnswerCheckResponse)
async def check_answer(request: AnswerCheckRequest):
    """
    Evaluate a student's answer using LLM-as-judge.
 
    For MCQ: simple exact match.
    For short/numerical: Gemini compares student answer to model answer
    and returns a score + specific feedback.
 
    INTERVIEW: "LLM-as-judge" is a production pattern where you use
    an LLM to evaluate another LLM's output (or a human's answer).
    It's more flexible than regex matching for open-ended answers.
    """
 
    # MCQ: simple string match
    if request.question_type == "mcq":
        student = request.student_answer.strip().upper()[:1]
        correct = request.model_answer.strip().upper()[:1]
        is_correct = student == correct
        return AnswerCheckResponse(
            score=request.marks if is_correct else 0,
            max_marks=request.marks,
            feedback="Correct! Well done." if is_correct
                     else f"Incorrect. The correct answer is {correct}.",
            is_correct=is_correct,
        )
 
    # Short / Numerical: LLM-as-judge
    prompt = f"""You are a strict but fair academic examiner.
 
Question: {request.question}
Model answer (full marks): {request.model_answer}
Student answer: {request.student_answer}
Total marks: {request.marks}
 
Evaluate the student's answer. Award marks based on:
- Correct key concepts mentioned
- Correct formula/method (numerical)
- Accuracy of final answer (numerical)
 
Return ONLY JSON (no markdown):
{{
  "score": <integer 0 to {request.marks}>,
  "feedback": "<2-3 sentences: what was correct, what was missing>",
  "is_correct": <true if score >= 60% of marks, else false>
}}"""
 
    import json, re

    result = generate_text(
        prompt,
        temperature=0.1,
        max_tokens=256,
    )
    raw = result["text"].strip()
    try:
        data = json.loads(raw)
    except Exception:
        m = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(m.group()) if m else {"score": 0, "feedback": raw, "is_correct": False}
 
    return AnswerCheckResponse(
        score=min(int(data.get("score", 0)), request.marks),
        max_marks=request.marks,
        feedback=data.get("feedback", "Could not evaluate."),
        is_correct=bool(data.get("is_correct", False)),
    )
 