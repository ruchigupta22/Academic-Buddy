import uuid
from typing import List, Dict, Any

from backend.rag.loader import parse_file
from backend.rag.chunker import chunk_pages
from backend.rag.embedder import embed_texts
from backend.db.chroma_client import get_chroma_client, get_collection
def ingest_lecture(
    file_bytes: bytes,
    filename: str,
    course_code: str,
) -> Dict[str, Any]:
    pages = parse_file(file_bytes, filename)
 
    if not pages:
        raise ValueError(
            "No text could be extracted. "
            "The file may be a scanned image PDF with no text layer."
        )
 
    # Step 2: Chunk — split into overlapping segments
    chunks = chunk_pages(pages)
 
    # Step 3: Embed — convert chunk text to 768-d vectors
    texts = [c["text"] for c in chunks]
    vectors = embed_texts(texts)
 
    # Step 4: Store — save to ChromaDB with metadata
    client = get_chroma_client()
    collection = get_collection(client, course_code)
 
    collection.add(
        ids=[str(uuid.uuid4()) for _ in chunks],
        documents=texts,
        embeddings=vectors,
        metadatas=[
            {
                "page": c["page"],
                "source": c["source"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ],
    )
 
    return {
        "filename": filename,
        "course_code": course_code,
        "pages_extracted": len(pages),
        "chunks_stored": len(chunks),
        "message": f"Successfully ingested {filename}",
    }
