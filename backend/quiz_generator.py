import json
import re
from typing import List, Dict, Any

from backend.llm.provider import generate_text
from backend.rag.embedder import embed_query
from backend.rag.retriever import retrieve_relevant_chunks
from backend.db.chroma_client import get_chroma_client, get_collection
from backend.config import settings

class QuizQuestion:
    def __init__(self, data: dict):
        self.question_type = data.get("type", "mcq")
        self.question = data.get("question", "")
        self.options = data.get("options", [])          # MCQ only
        self.correct_answer = data.get("correct_answer", "")
        self.explanation = data.get("explanation", "")
        self.difficulty = data.get("difficulty", "medium")
        self.topic = data.get("topic", "")
        self.marks = data.get("marks", 2)
 
    def to_dict(self):
        return {
            "type": self.question_type,
            "question": self.question,
            "options": self.options,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "topic": self.topic,
            "marks": self.marks,
        }
MCQ_PROMPT = """You are an expert professor creating exam questions.
 
Generate {count} MCQ questions from the study material below.
Difficulty level: {difficulty}
 
RULES:
- Each question tests ONE specific concept
- 4 options labeled A, B, C, D
- Exactly one correct answer
- Options must be plausible (no obviously wrong answers)
- Include a brief explanation of why the answer is correct
- Questions should match difficulty: easy=definition/recall, medium=application, hard=analysis/derivation
 
Return ONLY a JSON array. No markdown, no explanation. Format:
[
  {{
    "type": "mcq",
    "question": "What does Fick's First Law describe?",
    "options": ["A. Heat transfer by conduction", "B. Mass flux due to concentration gradient", "C. Momentum transfer in fluids", "D. Energy conservation in open systems"],
    "correct_answer": "B",
    "explanation": "Fick's First Law states J = -D(dC/dx), relating mass flux J to the concentration gradient.",
    "difficulty": "{difficulty}",
    "topic": "topic name here",
    "marks": 2
  }}
]
 
STUDY MATERIAL:
{context}
 
JSON ARRAY:"""
 
 
SHORT_ANSWER_PROMPT = """You are an expert professor creating exam questions.
 
Generate {count} short-answer questions from the study material below.
Difficulty level: {difficulty}
 
RULES:
- Each question requires a 2-4 sentence answer
- Questions should test understanding, not just memory
- Include a model answer (what a full-marks answer looks like)
- hard questions may require deriving or comparing concepts
 
Return ONLY a JSON array. No markdown. Format:
[
  {{
    "type": "short",
    "question": "Explain the physical significance of the diffusion coefficient D.",
    "options": [],
    "correct_answer": "The diffusion coefficient D (m²/s) quantifies how fast a species diffuses through a medium. A higher D means faster diffusion. It depends on temperature, the diffusing species, and the medium.",
    "explanation": "Full marks: mentions units, physical meaning, and at least one factor it depends on.",
    "difficulty": "{difficulty}",
    "topic": "topic name here",
    "marks": 5
  }}
]
 
STUDY MATERIAL:
{context}
 
JSON ARRAY:"""
 
 
NUMERICAL_PROMPT = """You are an expert professor creating numerical exam problems.
 
Generate {count} numerical problems from the study material below.
Difficulty level: {difficulty}
 
RULES:
- Each problem must have specific numerical values given
- Include a complete step-by-step solution
- Show all units and conversions
- Formula used must be explicitly stated
- Final answer must include units
 
Return ONLY a JSON array. No markdown. Format:
[
  {{
    "type": "numerical",
    "question": "A species diffuses through a membrane of thickness 2mm. The concentration on one side is 0.5 mol/m³ and the other is 0.1 mol/m³. If D = 1.2×10⁻⁹ m²/s, calculate the molar flux J.",
    "options": [],
    "correct_answer": "J = 2.4×10⁻⁷ mol/m²·s",
    "explanation": "Step 1: Fick's First Law: J = -D(dC/dx)\\nStep 2: dC/dx = (0.1-0.5)/0.002 = -200 mol/m⁴\\nStep 3: J = -(1.2×10⁻⁹)×(-200) = 2.4×10⁻⁷ mol/m²·s",
    "difficulty": "{difficulty}",
    "topic": "topic name here",
    "marks": 8
  }}
]
 
STUDY MATERIAL:
{context}
 
JSON ARRAY:"""

PROMPT_MAP = {
    "mcq":       MCQ_PROMPT,
    "short":     SHORT_ANSWER_PROMPT,
    "numerical": NUMERICAL_PROMPT,
}

def _get_context(topic: str, course_code: str, top_k: int = 8) -> str:
    """
    Retrieve the most relevant chunks for a topic from ChromaDB.
    Returns concatenated text to use as context for question generation.
    """
    client = get_chroma_client()
    collection = get_collection(client, course_code)
 
    chunks = retrieve_relevant_chunks(query=topic, collection=collection, top_k=top_k)
 
    if not chunks:
        return ""
 
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(f"[Excerpt {i} — {c['source']}, Page {c['page']}]\n{c['text']}")
 
    return "\n\n".join(parts)
 
 
def _call_gemini(prompt: str) -> List[Dict]:
    """
    Call the shared LLM provider and parse JSON response robustly.
    Returns list of question dicts, empty list on failure.
    """
    result = generate_text(
        prompt,
        temperature=0.4,
        max_tokens=4096,
        model_name=settings.GEMINI_MODEL,
    )
    raw = result["text"]
 
    # Try direct parse
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        pass
 
    # Try extracting array from response
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            pass
 
    return []
 
 
def generate_quiz(
    course_code: str,
    topic: str,
    question_types: List[str],
    count_per_type: int = 3,
    difficulty: str = "medium",
) -> Dict[str, Any]:
    """
    Main quiz generation function.
 
    Args:
        course_code:      e.g. "CHE301"
        topic:            e.g. "heat transfer" or "Fick's Law"
        question_types:   list of "mcq", "short", "numerical"
        count_per_type:   how many questions per type
        difficulty:       "easy", "medium", or "hard"
 
    Returns:
        {
          "topic": "heat transfer",
          "total_questions": 9,
          "questions": [...],
          "context_sources": ["lecture.pdf p.12", ...]
        }
    """
    # Step 1: Retrieve relevant context from notes
    context = _get_context(topic, course_code, top_k=10)
 
    if not context:
        return {
            "topic": topic,
            "total_questions": 0,
            "questions": [],
            "context_sources": [],
            "error": "No material found for this topic. Upload lecture notes first.",
        }
 
    # Step 2: Generate each question type
    all_questions = []
 
    for qtype in question_types:
        if qtype not in PROMPT_MAP:
            continue
 
        prompt = PROMPT_MAP[qtype].format(
            count=count_per_type,
            difficulty=difficulty,
            context=context[:6000],   # Token budget per call
        )
 
        raw_questions = _call_gemini(prompt)
 
        for item in raw_questions:
            try:
                q = QuizQuestion(item)
                all_questions.append(q.to_dict())
            except Exception:
                continue
 
    # Step 3: Extract source list for UI display
    client = get_chroma_client()
    collection = get_collection(client, course_code)
    chunks = retrieve_relevant_chunks(query=topic, collection=collection, top_k=5)
    sources = list({f"{c['source']} p.{c['page']}" for c in chunks})
 
    return {
        "topic": topic,
        "difficulty": difficulty,
        "total_questions": len(all_questions),
        "questions": all_questions,
        "context_sources": sources,
    }