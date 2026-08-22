"""
FastAPI Router exposing CivicAI RAG endpoints under /api/v1.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from rag.app.api.dependencies import get_pipeline
from rag.app.api.models import RAGQueryRequest, RAGQueryResponse
from rag.app.pipeline import RAGPipeline

router = APIRouter(tags=["RAG Service"])


@router.get(
    "/health",
    summary="Service Readiness Check",
    status_code=status.HTTP_200_OK
)
def check_readiness():
    """
    Returns service readiness status.
    """
    return {"status": "ready"}


@router.post(
    "/query",
    response_model=RAGQueryResponse,
    summary="Execute Grounded RAG Query",
    description="Performs candidate retrieval, cross-encoder reranking, grounded LLM answer generation, and verified citation mapping.",
    status_code=status.HTTP_200_OK
)
def run_rag_query(
    request: RAGQueryRequest,
    pipeline: RAGPipeline = Depends(get_pipeline)
) -> RAGQueryResponse:
    """
    Executes end-to-end RAG query pipeline.
    """
    try:
        response = pipeline.query(
            query=request.query,
            top_k=request.top_k,
            candidate_k=request.candidate_k,
            document_id=request.document_id,
            document_type=request.document_type,
            issuing_authority=request.issuing_authority
        )
        return response

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as exc:
        print(f"Error executing RAG query pipeline: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="RAG pipeline execution failed or dependency service unavailable."
        )
