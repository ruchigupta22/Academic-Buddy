from fastapi import APIRouter, HTTPException
from backend.api.models.schemas import ChatRequest, ChatResponse
from backend.rag.generator import generate_answer
 
router = APIRouter(prefix="/chat", tags=["Chat"])
 
 
@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question. Returns answer + source citations.
 
    Example body:
    {
      "question": "What is Fick's First Law?",
      "course_code": "CHE301"
    }
    """
    try:
        result = generate_answer(
            question=request.question,
            course_code=request.course_code.upper().strip(),
        )
    except Exception as e:
        raise HTTPException(500, f"Error generating answer: {e}")
 
    return ChatResponse(**result)