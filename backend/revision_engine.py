
import json
from typing import List, Dict, Any

from backend.llm.provider import generate_text
from backend.rag.retriever import retrieve_relevant_chunks
from backend.rag.pyq_analytics import get_topic_frequency, get_high_value_topics, get_full_summary
from backend.db.chroma_client import get_chroma_client, get_collection
from backend.config import settings


# ── Helper: call Gemini with a prompt ─────────────────────────────────────────

def _gemini(prompt: str, temperature: float = 0.3, max_tokens: int = 2048) -> str:
    return generate_text(
        prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        model_name=settings.GEMINI_MODEL,
    )["text"]


# ── Helper: get ChromaDB context for a topic ──────────────────────────────────

def _get_context(topic: str, course_code: str, top_k: int = 6) -> str:
    client = get_chroma_client()
    collection = get_collection(client, course_code)
    chunks = retrieve_relevant_chunks(query=topic, collection=collection, top_k=top_k)
    if not chunks:
        return ""
    parts = [f"[Source: {c['source']}, Page {c['page']}]\n{c['text']}" for c in chunks]
    return "\n\n---\n\n".join(parts)


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 1 — Priority Topics
# ══════════════════════════════════════════════════════════════════════════════

def get_priority_topics(course_code: str, days_left: int) -> Dict[str, Any]:
    """
    Rank topics by exam importance using PYQ data from SQLite.

    RANKING FORMULA:
      score = (frequency × 2) + (total_marks × 0.5)
      → Topics asked often AND worth many marks rank highest

    DAYS_LEFT adjusts how many topics to return:
      1 day  → top 5 only (survive mode)
      3 days → top 10
      7 days → top 15 (full preparation)

    Returns:
        {
          "topics": [{"topic","frequency","total_marks","priority_score","study_time_mins"}, ...],
          "total_topics": 10,
          "days_left": 3,
          "strategy": "Focus on high-frequency topics..."
        }
    """
    # Get analytics from SQLite (Phase 2)
    freq_data = get_topic_frequency(course_code, limit=20)
    value_data = {row["topic"]: row for row in get_high_value_topics(course_code, limit=20)}

    if not freq_data:
        return {
            "topics": [],
            "total_topics": 0,
            "days_left": days_left,
            "strategy": "No PYQ data found. Upload previous year papers to enable priority ranking.",
        }

    # Score and rank
    scored = []
    for row in freq_data:
        topic = row["topic"]
        freq = row.get("frequency", 0)
        marks = row.get("total_marks", 0) or 0
        priority_score = round((freq * 2) + (marks * 0.5), 1)

        # Estimate study time based on question type and difficulty
        types = (row.get("question_types") or "").lower()
        if "derivation" in types or "numerical" in types:
            base_time = 45  # Complex topics need more time
        elif "theory" in types:
            base_time = 25
        else:
            base_time = 30

        scored.append({
            "topic": topic,
            "frequency": freq,
            "total_marks": marks,
            "avg_marks": row.get("avg_marks", 0),
            "question_types": row.get("question_types", ""),
            "years_appeared": row.get("years_appeared", ""),
            "priority_score": priority_score,
            "study_time_mins": base_time,
        })

    # Sort by priority score
    scored.sort(key=lambda x: x["priority_score"], reverse=True)

    # Limit based on days left
    if days_left <= 1:
        limit = 5
        strategy = "🚨 Emergency mode: Focus ONLY on these top 5 topics. Skip derivations — focus on formulas and key definitions."
    elif days_left <= 3:
        limit = 10
        strategy = "⚡ Fast prep: Cover all topics below in order. Spend more time on high-priority ones. Do 1-2 PYQ questions per topic."
    elif days_left <= 7:
        limit = 15
        strategy = "✅ Good time available: Cover all topics, practice numericals, and attempt full PYQ papers."
    else:
        limit = 20
        strategy = "🎯 Full preparation mode: Cover all topics deeply. Attempt multiple PYQ papers and identify weak areas."

    return {
        "topics": scored[:limit],
        "total_topics": len(scored[:limit]),
        "days_left": days_left,
        "strategy": strategy,
    }


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 2 — Study Plan
# ══════════════════════════════════════════════════════════════════════════════

def build_study_plan(course_code: str, days_left: int, hours_per_day: int = 4) -> Dict[str, Any]:
    """
    Build a day-by-day study schedule from priority topics.

    Algorithm:
      1. Get prioritised topics with estimated study times
      2. Pack topics into days based on hours_per_day
      3. Reserve last day for revision + PYQ practice

    Returns:
        {
          "days": [
            {
              "day": 1,
              "date_label": "Day 1",
              "topics": [...],
              "total_minutes": 240,
              "tasks": ["Study Fick's Law", "Solve 3 numericals", ...]
            }
          ],
          "summary": "..."
        }
    """
    priority_data = get_priority_topics(course_code, days_left)
    topics = priority_data.get("topics", [])

    if not topics:
        return {"days": [], "summary": "No PYQ data found. Upload previous year papers first."}

    available_mins_per_day = hours_per_day * 60
    # Reserve last day for revision (if more than 1 day)
    study_days = max(1, days_left - 1)

    days = []
    topic_pool = list(topics)
    topic_idx = 0

    for day_num in range(1, study_days + 1):
        day_topics = []
        day_minutes = 0
        day_tasks = []

        while topic_idx < len(topic_pool):
            t = topic_pool[topic_idx]
            needed = t["study_time_mins"]

            if day_minutes + needed <= available_mins_per_day:
                day_topics.append(t)
                day_minutes += needed
                types = (t.get("question_types") or "").lower()
                if "numerical" in types or "derivation" in types:
                    day_tasks.append(f"📐 {t['topic']} — study theory + solve 3 numericals")
                else:
                    day_tasks.append(f"📖 {t['topic']} — read notes + write key points")
                topic_idx += 1
            else:
                break

        days.append({
            "day": day_num,
            "date_label": f"Day {day_num}",
            "topics": day_topics,
            "total_minutes": day_minutes,
            "tasks": day_tasks,
        })

    # Last day: revision + PYQ
    if days_left > 1:
        days.append({
            "day": days_left,
            "date_label": f"Day {days_left} — Revision Day",
            "topics": [],
            "total_minutes": available_mins_per_day,
            "tasks": [
                "📋 Quick revision of all topics (30 min each)",
                "📝 Attempt 1 full PYQ paper under timed conditions",
                "❌ Review wrong answers and revisit those topics",
                "📌 Re-read formula sheet",
                "😴 Sleep early — rest is part of preparation",
            ],
        })

    total_topics_covered = topic_idx
    return {
        "days": days,
        "total_topics_planned": total_topics_covered,
        "hours_per_day": hours_per_day,
        "summary": f"Study plan for {days_left} days covering {total_topics_covered} priority topics.",
    }


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 3 — Formula Sheet
# ══════════════════════════════════════════════════════════════════════════════

def generate_formula_sheet(course_code: str, topics: List[str] = None) -> str:
    """
    Extract all formulas, equations, and key relationships from notes.

    If topics provided → retrieve chunks for each topic.
    If no topics → use generic "formula equation law" query.

    The LLM reads the retrieved chunks and extracts ONLY formulas —
    no prose, no explanations. Clean, exam-ready format.
    """
    if not topics:
        # Generic search for formulas
        context = _get_context("formula equation law derivation units", course_code, top_k=12)
    else:
        # Get context for each topic and combine
        parts = []
        for t in topics[:5]:
            ctx = _get_context(t, course_code, top_k=4)
            if ctx:
                parts.append(ctx)
        context = "\n\n===\n\n".join(parts)

    if not context:
        return "No notes found. Upload lecture materials first."

    prompt = f"""You are creating a formula sheet for an exam.

Extract ALL formulas, equations, laws, and key relationships from the text below.

FORMAT (strictly follow):
## [Topic Name]
- **Formula name**: formula with all symbols defined
  - Variables: what each symbol means + SI units
  - When to use: one-line condition

Example:
## Mass Transfer
- **Fick's First Law**: J = -D (dC/dx)
  - Variables: J = molar flux (mol/m²s), D = diffusivity (m²/s), C = concentration (mol/m³)
  - When to use: Steady-state diffusion only

RULES:
- Include EVERY formula, even simple ones
- Always write SI units
- Group by topic
- No extra prose — formulas only

NOTES TEXT:
{context[:7000]}

FORMULA SHEET:"""

    return _gemini(prompt, temperature=0.1, max_tokens=2048)


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 4 — Revision Notes
# ══════════════════════════════════════════════════════════════════════════════

def generate_revision_notes(course_code: str, topic: str) -> str:
    """
    Generate concise revision notes for one topic.

    These are NOT a full explanation — they are REVISION notes:
    - Written for someone who already studied the topic
    - Bullet points, not paragraphs
    - Key facts, formulas, common mistakes, exam tips

    Think: the notes you'd write on a single index card.
    """
    context = _get_context(topic, course_code, top_k=8)

    if not context:
        return f"No notes found for '{topic}'. Upload relevant lecture material."

    prompt = f"""You are helping a student do last-minute revision before an exam.

Create concise revision notes for: **{topic}**

FORMAT:
### 🎯 Core Concept (2-3 sentences max)
[What it is in plain language]

### 📐 Key Formulas
[All formulas with symbols defined]

### ⚡ Key Points to Remember
[5-8 bullet points — most important facts]

### ❌ Common Mistakes
[3-4 things students get wrong in exams]

### 🔗 Connections
[How this topic links to other concepts]

### 📝 Typical Exam Questions
[2-3 examples of how this is asked]

RULES:
- Be concise — this is for quick revision, not learning from scratch
- Use bullet points everywhere
- Prioritise exam-relevant content
- Include units wherever applicable

NOTES FROM COURSE MATERIAL:
{context[:6000]}

REVISION NOTES:"""

    return _gemini(prompt, temperature=0.2, max_tokens=1024)


# ══════════════════════════════════════════════════════════════════════════════
# FUNCTION 5 — Confused Concepts
# ══════════════════════════════════════════════════════════════════════════════

def get_confused_concepts(course_code: str) -> str:
    """
    Find pairs of concepts that students commonly confuse.

    Strategy:
      1. Get top frequent topics from SQLite
      2. Retrieve notes content for those topics
      3. Ask Gemini: "What pairs of concepts here are often confused?"

    INTERVIEW: "How do you find confused concepts without student data?"
      We ask the LLM to identify conceptually similar or related topics
      from the notes — things that share similar names, formulas, or
      contexts. This is a proxy for what students typically confuse.
      In Phase 5, we'd use actual wrong-answer data from the quiz.
    """
    # Get top topics from SQL
    top_topics = get_topic_frequency(course_code, limit=8)
    if not top_topics:
        return "No PYQ data available. Upload previous year papers first."

    topic_names = [t["topic"] for t in top_topics]

    # Get context for all top topics
    context_parts = []
    for t in topic_names[:5]:
        ctx = _get_context(t, course_code, top_k=3)
        if ctx:
            context_parts.append(f"### {t}\n{ctx}")

    context = "\n\n".join(context_parts)

    if not context:
        return "No notes found. Upload lecture materials first."

    prompt = f"""You are an experienced professor who has graded thousands of exam papers.

Based on the course material below, identify pairs of concepts that students FREQUENTLY CONFUSE.

FORMAT for each pair:
---
### ⚠️ [Concept A] vs [Concept B]
**Why students confuse them:** [one sentence]
**Concept A:** [key distinguishing fact]
**Concept B:** [key distinguishing fact]
**Memory trick:** [how to remember the difference]
---

Topics covered in this course: {', '.join(topic_names)}

COURSE MATERIAL:
{context[:6000]}

List 5-7 commonly confused pairs. Only include pairs where confusion could cost marks.

CONFUSED CONCEPTS:"""

    return _gemini(prompt, temperature=0.3, max_tokens=1500)


# ══════════════════════════════════════════════════════════════════════════════
# MASTER FUNCTION — Full Revision Package
# ══════════════════════════════════════════════════════════════════════════════

def generate_revision_package(
    course_code: str,
    days_left: int,
    hours_per_day: int = 4,
) -> Dict[str, Any]:
    """
    Generate the complete exam revision package in one call.
    Called when student clicks "Generate Full Revision Plan".

    Returns all 5 components together.
    The frontend can also call each function via its own API endpoint
    for progressive loading (better UX for slow connections).
    """
    priority = get_priority_topics(course_code, days_left)
    plan = build_study_plan(course_code, days_left, hours_per_day)

    top_topic_names = [t["topic"] for t in priority.get("topics", [])[:5]]
    formula_sheet = generate_formula_sheet(course_code, topics=top_topic_names)
    confused = get_confused_concepts(course_code)

    return {
        "course_code": course_code,
        "days_left": days_left,
        "hours_per_day": hours_per_day,
        "priority_topics": priority,
        "study_plan": plan,
        "formula_sheet": formula_sheet,
        "confused_concepts": confused,
    }