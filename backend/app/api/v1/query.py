from fastapi import APIRouter, Depends
from app.api.deps import get_rag_client
from app.integrations.rag_client import RAGClient
from app.schemas.common import APIResponse
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse

router = APIRouter(tags=["RAG Query Engine"])


@router.post("/query", response_model=APIResponse[RAGQueryResponse])
async def query_rag_engine(
    payload: RAGQueryRequest,
    rag_client: RAGClient = Depends(get_rag_client),
):
    """
    Exposes RAG Query endpoint on Main FastAPI Backend to delegate queries to the RAG microservice.
    """
    response_data = await rag_client.query(
        query=payload.query,
        top_k=payload.top_k,
        candidate_k=payload.candidate_k,
        document_id=payload.document_id,
        document_type=payload.document_type,
        issuing_authority=payload.issuing_authority,
    )
    return APIResponse(
        success=True,
        data=response_data,
        message="RAG query executed successfully",
    )
