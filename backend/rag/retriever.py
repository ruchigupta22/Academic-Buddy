from typing import List, Dict, Any
import chromadb
from backend.rag.embedder import embed_query
from backend.config import settings

def retrieve_relevant_chunks(
    query: str,
    collection: chromadb.Collection,
    top_k: int | None = None,
) -> List[Dict[str, Any]]:
    k = top_k or settings.TOP_K_RESULTS
 
    # Step 1: Embed the question
    query_vector = embed_query(query)
 
    # Step 2: Query ChromaDB
    # n_results: how many chunks to return
    # include: what fields to include in the response

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    chunks = []
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
 
    for doc, meta, dist in zip(documents, metadatas, distances):
        # ChromaDB cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity score: 1 = identical, 0 = unrelated
        similarity = 1 - (dist / 2)
 
        chunks.append({
            "text": doc,
            "source": meta.get("source", "Unknown"),
            "page": meta.get("page", "?"),
            "similarity_score": round(similarity, 3),
        })
 
    return chunks
