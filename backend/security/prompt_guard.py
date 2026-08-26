"""
backend/security/prompt_guard.py
----------------------------------
Defends the RAG pipeline against two attack surfaces:
  1. Direct injection: malicious text in the user's own question
  2. Indirect injection: malicious hidden instructions inside uploaded
     documents that get retrieved and inserted as "trusted" context

Defense strategy (layered, not a single silver bullet):
  - Pattern-based detection of known injection phrasings (catches obvious attempts)
  - Structural isolation: wrap retrieved context in explicit delimiters and
    tell the model directly that content inside is DATA, never INSTRUCTIONS
    (this is the primary defense — pattern matching alone is easily evaded)
  - Output-side check: flag if the model's response shows signs the
    instruction hierarchy was violated (e.g. system prompt leakage)
"""

import re
from typing import List, Dict, Tuple

# Known injection patterns - not exhaustive, but catches common/naive attempts.
# This is a DETECTION layer, not the primary defense (see structural isolation below).
INJECTION_PATTERNS = [
    r"ignore (all |the )?(above|previous|prior) instructions",
    r"disregard (all |the )?(above|previous|prior) (instructions|rules)",
    r"system\s*prompt",
    r"you are now",
    r"new instructions?:",
    r"reveal (your|the) (instructions|system prompt|rules)",
    r"act as (if you (were|are)|though you (were|are)) (not|no longer)",
    r"pretend (you are|to be)",
    r"developer mode",
    r"override (your|the) (rules|instructions)",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def scan_for_injection(text: str) -> Tuple[bool, List[str]]:
    """
    Returns (is_suspicious, matched_patterns).
    Used on BOTH user questions and retrieved document chunks.
    """
    matches = []
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            matches.append(pattern.pattern)
    return (len(matches) > 0, matches)


def sanitize_question(question: str) -> Dict:
    """
    Check the user's own question for injection attempts.
    We don't hard-block (avoids false-positive frustration for legitimate
    questions that happen to contain a flagged phrase) - we log/flag,
    and the structural isolation below is the real defense.
    """
    is_suspicious, matches = scan_for_injection(question)
    return {
        "question": question,
        "flagged": is_suspicious,
        "matched_patterns": matches,
    }


def wrap_context_safely(chunks: List[Dict]) -> str:
    """
    THE PRIMARY DEFENSE.

    Instead of trusting retrieved chunks blindly, we:
    1. Scan each chunk for injection attempts and flag suspicious ones
    2. Wrap all context in explicit <document> tags with an instruction
       telling the model this content is DATA to read, never commands
       to follow - this is the standard structural-isolation technique
       used in production RAG systems, since pattern matching alone is
       trivially evaded by rephrasing.
    """
    blocks = []
    flagged_sources = []

    for i, chunk in enumerate(chunks, start=1):
        is_suspicious, matches = scan_for_injection(chunk["text"])
        if is_suspicious:
            flagged_sources.append({"source": chunk["source"], "page": chunk["page"], "matches": matches})

        blocks.append(
            f'<document index="{i}" source="{chunk["source"]}" page="{chunk["page"]}">\n'
            f"{chunk['text']}\n"
            f"</document>"
        )

    context_str = "\n\n".join(blocks)
    return context_str, flagged_sources


def check_output_integrity(answer: str) -> Tuple[bool, List[str]]:
    """
    Lightweight output-side check: does the generated answer show signs
    the model was hijacked (e.g. it starts discussing its own system
    prompt/instructions, rather than answering the academic question)?
    """
    suspicious_phrases = [
        "my instructions are", "i am programmed to", "system prompt",
        "as an ai language model, my rules", "ignoring previous",
    ]
    found = [p for p in suspicious_phrases if p in answer.lower()]
    return (len(found) > 0, found)