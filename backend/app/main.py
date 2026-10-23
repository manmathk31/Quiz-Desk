from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
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


@app.get("/health/live", tags=["Health"])
async def health_liveness():
    """Liveness probe verifying that the application process is running."""
    return {"status": "alive"}


@app.get("/health/ready", tags=["Health"])
async def health_readiness(db: Session = Depends(get_db)):
    """
    Readiness probe verifying database connectivity and operational readiness.
    Fails closed with HTTP 503 if the database connection cannot be established.
    """
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unreachable or unready",
        ) from exc


# Mount versioned API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

