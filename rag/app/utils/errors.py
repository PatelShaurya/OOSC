"""
Custom exception and error handling.

Error Codes (matching RAG contract):
- INVALID_REQUEST: Bad input format
- NO_RELEVANT_CONTEXT: No chunks found in knowledge base
- RAG_RETRIEVAL_ERROR: Vector search failed
- LLM_ERROR: Claude API error
- EMBEDDING_ERROR: Embedding generation failed
- VECTOR_DATABASE_ERROR: Database connection/query error
- MODEL_TIMEOUT: LLM took too long
- INTERNAL_ERROR: Unexpected error

Classes:
- RAGError: Base custom exception
- InvalidRequestError
- NoRelevantContextError
- RetrievalError
- LLMError
- EmbeddingError
- VectorDatabaseError
- TimeoutError

Functions:
- format_error_response(): Convert exception to response format
"""
