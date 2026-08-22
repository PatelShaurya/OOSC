"""
FastAPI Main Application Entrypoint for CivicAI RAG Service.
"""
import os
from typing import List
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from rag.app.api.routes import router as api_v1_router


def get_allowed_origins() -> List[str]:
    """
    Parses configured CORS allowed origins from environment variable CORS_ALLOWED_ORIGINS.
    Defaults to common frontend/backend local development origins if not explicitly set.
    """
    raw_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if raw_origins:
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]


app = FastAPI(
    title="CivicAI RAG Service",
    description="API for CivicAI legal document search, cross-encoder reranking, grounded answer generation, and verified citation mapping.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS Middleware safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include API v1 router
app.include_router(api_v1_router, prefix="/api/v1")


@app.get(
    "/health",
    summary="Root Service Health Check",
    status_code=status.HTTP_200_OK
)
def root_health_check():
    """
    Lightweight health endpoint for load balancers and uptime checks.
    Does not query database or ML models.
    """
    return {
        "status": "ok",
        "service": "civicai-rag"
    }


@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    """
    Global exception handler preventing internal error/secrets exposure.
    """
    print(f"Unhandled Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected internal server error occurred."}
    )
