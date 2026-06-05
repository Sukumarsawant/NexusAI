import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.services.gemini_client import gemini_service

router = APIRouter(tags=["System Health & Readiness"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NexusAI Enterprise RAG Platform",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute(text("SELECT 1;"))
    except Exception as e:
        db_status = f"unhealthy: {e}"

    gemini_configured = gemini_service.is_configured()

    return {
        "status": "ready" if db_status == "connected" else "degraded",
        "database": db_status,
        "gemini_api_configured": gemini_configured,
        "active_model": settings.GEMINI_MODEL,
        "embedding_model": settings.GEMINI_EMBEDDING_MODEL,
    }
