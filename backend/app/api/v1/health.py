from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.config import Settings, get_settings
from app.integrations.rag_client import RAGClient

router = APIRouter(tags=["Health & Status"])


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/health/ready")
async def readiness_check(settings: Settings = Depends(get_settings)):
    rag_client = RAGClient()
    rag_online = await rag_client.check_health()

    return {
        "status": "ready",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "components": {
            "backend_api": "healthy",
            "database": "configured" if settings.SUPABASE_URL else "fallback_mode",
            "rag_service": "connected" if rag_online else "mock_fallback",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
