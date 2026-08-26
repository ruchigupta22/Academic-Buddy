import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import settings

def get_chroma_client() -> chromadb.PersistentClient:
    """
    Returns a persistent ChromaDB client.
    Data is saved to disk so it survives server restarts.
    """
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )
    return client

def get_collection(client: chromadb.PersistentClient, course_code: str):
    """
    Get or create a ChromaDB collection for lecture notes.
    Collection name: course_CHE301
    """
    collection = client.get_or_create_collection(
        name=f"course_{course_code}",
        metadata={"hnsw:space": "cosine"},
    )
    return collection

def get_pyq_collection(client: chromadb.PersistentClient, course_code: str):
    """
    Separate collection for PYQ papers.
    Collection name: pyq_CHE301
    Kept separate so PYQ search doesn't mix with lecture notes.
    """
    collection = client.get_or_create_collection(
        name=f"pyq_{course_code}",
        metadata={"hnsw:space": "cosine"},
    )
    return collection