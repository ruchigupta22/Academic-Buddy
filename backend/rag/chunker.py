from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.config import settings


def chunk_pages(pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
   
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,        # Max chars per chunk
        chunk_overlap=settings.CHUNK_OVERLAP,  # Overlap between chunks
        # Try these separators in order; fall back to the next if text is still too big
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    all_chunks = []

    for page in pages:
        # Split one page's text into multiple chunks
        raw_chunks = splitter.split_text(page["text"])

        for i, chunk_text in enumerate(raw_chunks):
            all_chunks.append({
                "text": chunk_text,
                "page": page["page"],           # Preserved from original page
                "source": page["source"],        # Preserved from original page
                "chunk_index": i,                # Position within the page
            })

    return all_chunks