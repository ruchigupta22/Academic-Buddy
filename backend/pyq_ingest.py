"""
backend/pyq_ingest.py
---------------------
Phase 2 pipeline: Upload PYQ paper → ChromaDB + SQLite.

TWO STORAGE PATHS IN ONE UPLOAD:

  Upload PYQ PDF
        │
        ├──── ChromaDB path ────────────────────────────────
        │     parse_file → chunk_pages → embed_texts → add_to_chroma                  
        │     (so students can search PYQ text semantically) 
        │
        └──── SQLite path ───────────────────────────────────
              extract_questions() via Gemini → INSERT rows   
              (so we can COUNT topics, SUM marks, GROUP BY)  

IMPORTS USE YOUR EXACT FOLDER STRUCTURE:
  backend/rag/loader.py        → parse_file
  backend/rag/chunker.py       → chunk_pages
  backend/rag/embedder.py      → embed_texts
  backend/rag/pyq_extractor.py → extract_questions, extract_year, infer_exam_type
  backend/db/chroma_client.py  → get_chroma_client, get_pyq_collection
  backend/db/sql_client.py     → get_db
"""

import uuid
from typing import Dict, Any

from backend.rag.loader import parse_file
from backend.rag.chunker import chunk_pages
from backend.rag.embedder import embed_texts
from backend.rag.pyq_extractor import extract_questions, extract_year, infer_exam_type
from backend.db.chroma_client import get_chroma_client, get_pyq_collection
from backend.db.sql_client import get_db


def ingest_pyq(
    file_bytes: bytes,
    filename: str,
    course_code: str,
    year_override: int = None,
) -> Dict[str, Any]:
    """
    Full PYQ ingestion: parse → ChromaDB (semantic search) + SQLite (analytics).

    Args:
        file_bytes:    Raw bytes of uploaded PDF
        filename:      Original filename
        course_code:   e.g. "CHE301"
        year_override: If student manually specifies the year in UI

    Returns:
        Summary dict with counts from both storage paths
    """
    code = course_code.upper().strip()

    # Step 1: Parse raw text from PDF
    pages = parse_file(file_bytes, filename)
    if not pages:
        raise ValueError("No text extracted — may be a scanned image PDF.")

    full_text = "\n\n".join(p["text"] for p in pages)

    # ── Path A: ChromaDB (for semantic search) ─────────────────────────────────
    chunks = chunk_pages(pages)
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)

    client = get_chroma_client()
    pyq_collection = get_pyq_collection(client, code)

    pyq_collection.add(
        ids=[str(uuid.uuid4()) for _ in chunks],
        documents=texts,
        embeddings=vectors,
        metadatas=[
            {
                "page": c["page"],
                "source": filename,
                "chunk_index": c["chunk_index"],
                "doc_type": "pyq",
            }
            for c in chunks
        ],
    )

    # ── Path B: SQLite (for analytics) ─────────────────────────────────────────
    year = year_override or extract_year(filename)
    exam_type = infer_exam_type(filename, full_text)

    # Register the paper
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO pyq_papers (course_code, filename, year, exam_type) VALUES (?, ?, ?, ?)",
            (code, filename, year, exam_type),
        )
        paper_id = cursor.lastrowid

    # Extract structured questions using Gemini
    questions = extract_questions(full_text)

    # Store questions in SQLite
    if questions:
        with get_db() as conn:
            conn.executemany(
                """INSERT INTO pyq_questions
                   (paper_id, course_code, year, topic, subtopic,
                    question_type, marks, raw_question, difficulty)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (paper_id, code, year, q.topic, q.subtopic,
                     q.question_type, q.marks, q.raw_question, q.difficulty)
                    for q in questions
                ],
            )

    return {
        "filename": filename,
        "course_code": code,
        "year": year,
        "exam_type": exam_type,
        "pages_parsed": len(pages),
        "chunks_stored": len(chunks),
        "questions_extracted": len(questions),
        "message": f"PYQ ingested: {len(questions)} questions extracted.",
    }