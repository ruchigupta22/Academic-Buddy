from pydantic import BaseModel, Field
from typing import List, Optional

class UploadResponse(BaseModel):
    filename: str
    course_code: str
    pages_extracted: int
    chunks_stored: int 
    message: str

class PYQUploadResponse(BaseModel):
    filename: str
    course_code: str
    year: Optional[int]
    exam_type: str
    pages_parsed: int
    chunks_stored: int
    questions_extracted: int
    message: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500, example="What is Fick's First Law?")
    course_code: str = Field(example="CHE301")

class SourceCitation(BaseModel):
    source: str
    page: int
    similarity: float
 
 
class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    chunks_used: int
    
class PYQQuestionRequest(BaseModel):
    question: str = Field(example="What topics are asked most frequently?")
    course_code: str = Field(example="CHE301")
 
 
class PYQAnalyticsResponse(BaseModel):
    answer: str
    data: dict
 
 
class PYQReportResponse(BaseModel):
    report: str
    course_code: str