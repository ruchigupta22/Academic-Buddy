"""
backend/pyq_intelligence.py
----------------------------
Combines SQL analytics + Gemini to answer PYQ-related questions.

TWO ROLES OF THE LLM HERE:
  Phase 1: LLM as RETRIEVER — finds relevant text chunks
  Phase 2: LLM as ANALYST  — interprets SQL data, explains patterns

  The LLM does NOT know frequency counts from your papers.
  SQL gives the numbers. LLM explains what they mean.
  This is more reliable than asking LLM to recall statistics.

IMPORTS USE YOUR EXACT FOLDER STRUCTURE:
  backend/rag/pyq_analytics.py → get_full_summary, get_topic_frequency, etc.
"""

import json
from typing import Dict, Any

from backend.llm.provider import generate_text

from backend.rag.pyq_analytics import (
    get_full_summary,
    get_topic_frequency,
    get_high_value_topics,
    get_type_distribution,
)
from backend.config import settings


def generate_analysis_report(course_code: str) -> str:
    """
    Full LLM-powered analysis of PYQ patterns.
    SQL gives the numbers, Gemini writes the insight.
    """
    summary = get_full_summary(course_code)

    if not summary["top_topics"]:
        return (
            "No PYQ data found for this course. "
            "Please upload previous year question papers first."
        )

    n_years = len(summary["years_covered"])
    data_json = json.dumps(summary, indent=2)

    prompt = f"""You are an expert academic advisor analyzing previous year exam papers.

Course: {course_code}
Years of data: {n_years}

VERIFIED DATA FROM DATABASE (do not change these numbers):
{data_json}

Write a helpful analysis covering:
1. Most important topics (appear most often + carry most marks)
2. Exam pattern (numerical-heavy? theory-heavy? mixed?)
3. Trend (any topics appearing more recently? any dropped?)
4. Top 5 topics to study first

Use bullet points. Be specific — cite topic names and numbers.
End with bold "📌 Top 5 Priority Topics" list.
Keep under 400 words."""

    result = generate_text(prompt, temperature=0.3, max_tokens=1024)
    return result["text"]


def answer_pyq_question(question: str, course_code: str) -> Dict[str, Any]:
    """
    Answer any free-form question about PYQ patterns.

    Examples:
      "What topics are most frequently asked?"
      "How many marks does Fick's Law typically carry?"
      "What type of questions appear most?"

    SQL gives the data, LLM answers the question using that data.
    """
    summary = get_full_summary(course_code)

    if not summary["top_topics"]:
        return {
            "answer": "No PYQ data found. Upload past exam papers to enable this feature.",
            "data": {},
        }

    prompt = f"""You are analyzing previous year question papers for {course_code}.

Student question: "{question}"

DATA FROM DATABASE (accurate counts):
{json.dumps(summary, indent=2)}

Answer the student's question using ONLY the data above.
Be specific: cite topic names and numbers.
Keep answer under 200 words. Use bullet points if listing items."""

    result = generate_text(prompt, temperature=0.2, max_tokens=512)

    return {
        "answer": result["text"],
        "data": summary,
    }


def get_structured_analytics(course_code: str) -> Dict[str, Any]:
    """
    Return raw analytics data for chart rendering in the UI.
    No LLM call — fast and free.
    """
    return {
        "topic_frequency":   get_topic_frequency(course_code),
        "high_value_topics": get_high_value_topics(course_code),
        "type_distribution": get_type_distribution(course_code),
    }