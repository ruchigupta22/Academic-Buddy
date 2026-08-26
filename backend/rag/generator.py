

from typing import List, Dict, Any
#import google.generativeai as genai

from backend.rag.retriever import retrieve_relevant_chunks
from backend.db.chroma_client import get_chroma_client, get_collection
from backend.config import settings

# genai.configure(api_key=settings.GEMINI_API_KEY)
from backend.llm.provider import generate_text

def build_prompt(question: str, chunks: List[Dict[str, Any]]) -> str:
    """
    Inject retrieved chunks into the prompt as numbered context blocks.
    """
    context_blocks = []
    for i, chunk in enumerate(chunks, start=1):
        context_blocks.append(
            f"[Context {i}] Source: {chunk['source']}, Page {chunk['page']}\n"
            f"{chunk['text']}"
        )
    context_str = "\n\n---\n\n".join(context_blocks)

    return f"""You are a precise academic tutor helping a student understand their course material.

RULES:
1. Answer ONLY using the context provided below. No outside knowledge.
2. After every fact, cite like this: [Source: filename.pdf, Page: 5]
3. If context is insufficient, say: "I could not find this in your uploaded materials."
4. Use bullet points for lists. Be concise but complete.
5. End with a "📚 Sources" section listing all files and pages used.

STUDENT QUESTION:
{question}

CONTEXT FROM COURSE MATERIALS:
{context_str}

ANSWER:"""


def generate_answer(question: str, course_code: str) -> Dict[str, Any]:
    """
    Full RAG pipeline: retrieve → prompt → generate → return.

    Args:
        question:    Student's natural language question
        course_code: e.g. "CHE301" — which course to search

    Returns:
        {
          "answer":      "Fick's First Law states...",
          "sources":     [{"source": "lecture.pdf", "page": 12}, ...],
          "chunks_used": 5
        }
    """
    # Step 1: Get ChromaDB collection for this course
    client = get_chroma_client()
    collection = get_collection(client, course_code)

    # Step 2: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(query=question, collection=collection)

    if not chunks:
        return {
            "answer": "No documents found for this course. Please upload lecture materials first.",
            "sources": [],
            "chunks_used": 0,
        }

    # Step 3: Build prompt with context
    prompt = build_prompt(question, chunks)

    # Step 4: Call Gemini
    result = generate_text(
    prompt,
    temperature=0.2,
    max_tokens=1024,
)
    answer= result["text"]
    # Step 5: Build source list (deduplicated)
    seen = set()
    sources = []
    for c in chunks:
        key = (c["source"], c["page"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": c["source"],
                "page": c["page"],
                "similarity": c["similarity_score"],
            })

    return {
        "answer": answer,
        "sources": sources,
        "chunks_used": len(chunks),
    }