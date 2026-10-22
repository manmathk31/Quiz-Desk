"""FastAPI Application Entrypoint for Quizdesk."""
from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None,
)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify service availability."""
    return {"status": "ok"}
