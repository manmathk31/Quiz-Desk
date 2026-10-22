"""FastAPI Application Entrypoint for Quizdesk."""
from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import api_v1_router

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


# Mount versioned API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

