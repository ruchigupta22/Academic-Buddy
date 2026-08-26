from pydantic_settings import BaseSettings
from pathlib import Path
 
 
class Settings(BaseSettings):
    # --- LLM ---
    GEMINI_API_KEY: str  # Required — app won't start without this
    GROQ_API_KEY: str = ""
    # --- Vector DB ---
    CHROMA_PERSIST_DIR: str = "./chroma_db"
 
    # --- RAG tuning knobs ---
    TOP_K_RESULTS: int = 5          # How many chunks to retrieve per question
    CHUNK_SIZE: int = 1500          # Characters per chunk (≈ 375 tokens)
    CHUNK_OVERLAP: int = 200        # Overlap between consecutive chunks
 
    # --- Embedding model ---
    # models/embedding-001 is Google's free embedding model
    EMBEDDING_MODEL: str = "models/text-embedding-004"
 
    # --- Chat model ---
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Fast and free tier available
 
    class Config:
        # Looks for a file called .env in the current working directory
        env_file = ".env"
        env_file_encoding = "utf-8"
 
 
# Create a single instance — import this everywhere
settings = Settings()