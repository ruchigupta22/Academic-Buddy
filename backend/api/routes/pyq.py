from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from backend.api.models.schemas import (
    PYQUploadResponse,
    PYQQuestionRequest,
    PYQAnalyticsResponse,
    PYQReportResponse,
)
from backend.pyq_ingest import ingest_pyq
from backend.pyq_intelligence import (
    answer_pyq_question,
    generate_analysis_report,
    get_structured_analytics,
)
 
router = APIRouter(prefix="/pyq", tags=["PYQ Intelligence"])
ALLOWED = {".pdf", ".pptx", ".ppt"}

@router.post("/upload", response_model=PYQUploadResponse)
async def upload_pyq(
    file: UploadFile = File(...),
    course_code: str = Form(...),
    year: int = Form(None),
):
    """
    Upload a previous year question paper.
    Stores in ChromaDB (for search) AND extracts structured
    questions into SQLite (for frequency/trend analytics).
    """
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
 
    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type '{ext}'.")
 
    file_bytes = await file.read()
 
    try:
        result = ingest_pyq(
            file_bytes=file_bytes,
            filename=filename,
            course_code=course_code.upper().strip(),
            year_override=year,
        )
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"PYQ ingestion failed: {e}")
 
    return PYQUploadResponse(**result)
 
 
@router.post("/ask", response_model=PYQAnalyticsResponse)
async def ask_pyq(request: PYQQuestionRequest):
    """
    Ask a free-form question about PYQ patterns.
 
    Examples:
      "What topics are most frequently asked?"
      "How many marks does heat transfer typically carry?"
      "What exam type has the most numerical questions?"
    """
    try:
        result = answer_pyq_question(
            question=request.question,
            course_code=request.course_code.upper().strip(),
        )
    except Exception as e:
        raise HTTPException(500, f"Error: {e}")
 
    return PYQAnalyticsResponse(**result)
 
 
@router.get("/report", response_model=PYQReportResponse)
async def get_report(course_code: str = Query(..., example="CHE301")):
    """
    Generate a full natural-language analysis report for a course.
    Uses SQL analytics + Gemini to write insights.
    """
    try:
        report = generate_analysis_report(course_code.upper().strip())
    except Exception as e:
        raise HTTPException(500, f"Error generating report: {e}")
 
    return PYQReportResponse(report=report, course_code=course_code.upper())
 
 
@router.get("/analytics")
async def get_analytics(course_code: str = Query(..., example="CHE301")):
    """
    Get raw structured analytics data for chart rendering.
    Returns topic frequency, high-value topics, and type distribution.
    No LLM call — fast.
    """
    try:
        return get_structured_analytics(course_code.upper().strip())
    except Exception as e:
        raise HTTPException(500, f"Error fetching analytics: {e}")