"""
backend/api/routes/upload.py
-----------------------------
POST /api/v1/upload/lecture — upload lecture notes
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.api.models.schemas import UploadResponse
from backend.ingest import ingest_lecture

router = APIRouter(prefix="/upload", tags=["Upload"])
ALLOWED = {".pdf", ".pptx", ".ppt"}


@router.post("/lecture", response_model=UploadResponse)
async def upload_lecture(
    file: UploadFile = File(...),
    course_code: str = Form(...),
):
    """Upload a lecture PDF or PPTX and store in ChromaDB for Q&A."""
    filename = file.filename or "unknown"
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in ALLOWED:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Upload PDF or PPTX.")

    file_bytes = await file.read()

    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(413, "File too large. Max 50 MB.")

    try:
        result = ingest_lecture(file_bytes, filename, course_code.upper().strip())
    except ValueError as e:
        raise HTTPException(422, str(e))
    except Exception as e:
        raise HTTPException(500, f"Ingestion failed: {e}")

    return UploadResponse(**result)