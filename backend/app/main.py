"""FastAPI Application Entrypoint for Quizdesk."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import api_v1_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url=None,
)

# Enforce explicit, restricted CORS origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)



@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify service availability."""
    return {"status": "ok"}


# Mount versioned API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

