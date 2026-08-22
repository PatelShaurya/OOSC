"""
Dependency Injection Manager for CivicAI RAG Service.
Ensures single initialization of heavy ML models across API requests.
"""
import threading
from typing import Optional
from rag.app.pipeline import RAGPipeline

_pipeline_instance: Optional[RAGPipeline] = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> RAGPipeline:
    """
    FastAPI dependency provider returning single initialized RAGPipeline instance.
    Models (BGE-M3, Cross-Encoder) are loaded once and reused across all requests.
    """
    global _pipeline_instance
    if _pipeline_instance is None:
        with _pipeline_lock:
            if _pipeline_instance is None:
                print("Initializing RAGPipeline singleton dependency for FastAPI service...")
                _pipeline_instance = RAGPipeline()
                print("RAGPipeline initialized successfully.")
    return _pipeline_instance


def set_pipeline_override(pipeline: RAGPipeline) -> None:
    """
    Helper function for unit tests to inject a mocked RAGPipeline instance.
    """
    global _pipeline_instance
    with _pipeline_lock:
        _pipeline_instance = pipeline


def reset_pipeline_dependency() -> None:
    """
    Resets the pipeline singleton instance (useful for testing cleanup).
    """
    global _pipeline_instance
    with _pipeline_lock:
        _pipeline_instance = None
