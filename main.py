from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import upload,chat, pyq, quiz, revision, profile
from backend.db.sql_client import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialised")
    yield

app= FastAPI(
    title="Academic Chatbot API",
    description="RAG-powered study assistant — Phase 1 (Chat) + Phase 2 (PYQ Intelligence)",
    version="2.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins= ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(upload.router, prefix="/api/v1")
app.include_router(chat.router,   prefix="/api/v1")
app.include_router(pyq.router,    prefix="/api/v1")
app.include_router(quiz.router,   prefix="/api/v1")   # NEW Phase 3
app.include_router(revision.router, prefix="/api/v1") 
app.include_router(profile.router, prefix="/api/v1")
@app.get("/health")
async def health():
     return {"status": "ok", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)