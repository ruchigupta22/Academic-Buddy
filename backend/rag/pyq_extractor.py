import json
import re
from typing import List
import time
# import google.generativeai as genai
from pydantic import BaseModel, field_validator
# from backend.config import settings
from backend.llm.provider import generate_text

# genai.configure(api_key= settings.GEMINI_API_KEY)

EXTRACTION_PROMPT = """You are an academic question-paper analyser.
 
    Extract every question from the text below and return a JSON array.
    Each element must have exactly these keys:
    - topic         (string): main topic/concept being tested
    - subtopic      (string): specific aspect (empty string if none)
    - question_type (string): one of "numerical", "theory", "derivation", "short", "mcq"
    - marks         (integer): marks for this question (0 if not stated)
    - raw_question  (string): the full question text verbatim
    - difficulty    (string): one of "easy", "medium", "hard"
    
    RULES:
    - Return ONLY the JSON array. No explanation. No markdown. No backticks.
    - Sub-parts like (a), (b) should each be a separate item.
    - Infer topic from context if not stated — use standard textbook names.
    - Marks: look for [8], (8 marks), 8M patterns. Default 0 if not found.
    
    QUESTION PAPER TEXT:
    {text}
    
    JSON ARRAY:"""

class ExtractedQuestion(BaseModel):
    """One question extracted from a PYQ paper."""
    topic: str
    subtopic: str = ""
    question_type: str = "theory"
    marks: int = 0
    raw_question: str = ""
    difficulty: str = "medium"

    @field_validator("question_type")
    @classmethod
    def normalize_type(cls,v: str)-> str:
        allowed= {"numerical", "theory", "derivation", "short", "mcq" }
        v = v.lower().strip()
        return v if v in allowed else "theory"
    
    @field_validator("difficulty")
    @classmethod
    def normalize_difficulty(cls, v: str) -> str:
        v = v.lower().strip()
        return v if v in {"easy", "medium", "hard"} else "medium"
    
    @field_validator("marks")
    @classmethod
    def clamp_marks(cls, v: int) -> int:
        return max(0, min(v, 100))
    
    
    
    
def extract_questions(paper_text: str) -> List[ExtractedQuestion]:
        """
        Send PYQ paper text to Gemini, get back structured question list.
    
        Returns list of validated ExtractedQuestion objects.
        Returns empty list if parsing fails.
        """
        
    
        prompt = EXTRACTION_PROMPT.format(text=paper_text[:8000])
        # response = model.generate_content(prompt)
        # raw = response.text.strip()

        result = generate_text(
            prompt,
            temperature=0.1,
        )
        raw= result["text"].strip()

        # raw = result["text"].strip()
        # Try 1: direct JSON parse
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try 2: find JSON array anywhere in response
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    return []
            else:
                return []
    
        if not isinstance(data, list):
            return []
    
        # Validate each item
        questions = []
        for item in data:
            try:
                questions.append(ExtractedQuestion(**item))
            except Exception:
                continue
    
        return questions
    
 
def extract_year(filename: str) -> int | None:
        """Pull 4-digit year from filename. e.g. EndSem_2022.pdf → 2022"""
        match = re.search(r'(20\d{2}|19\d{2})', filename)
        return int(match.group()) if match else None
    
    
def infer_exam_type(filename: str, text: str) -> str:
        """Detect mid-sem / end-sem / quiz from filename or paper content."""
        combined = (filename + " " + text[:300]).lower()
        if any(k in combined for k in ["endsem", "end-sem", "end sem", "final"]):
            return "end-sem"
        if any(k in combined for k in ["midsem", "mid-sem", "mid sem", "midterm"]):
            return "mid-sem"
        if "quiz" in combined:
            return "quiz"
        return "end-sem"