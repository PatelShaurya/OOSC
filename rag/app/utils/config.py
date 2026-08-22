"""
Configuration and constants for RAG service.

Configuration:
- EMBEDDING_MODEL: Model name/path
- LLM_MODEL: Claude model (e.g., claude-3-sonnet-20240229)
- VECTOR_DB_URL: Supabase connection string
- CHUNK_SIZE: Tokens per chunk
- CHUNK_OVERLAP: Overlap between chunks
- TOP_K: Default number of results to retrieve
- CONFIDENCE_THRESHOLD: Minimum confidence to return answer
- REQUEST_TIMEOUT: Max seconds for LLM call

Constants:
- SERVICE_TYPES: Allowed services
- LANGUAGES: Supported languages
- DOCUMENT_TYPES: Allowed document types
- ERROR_CODES: All possible error codes

Classes:
- RAGConfig: Configuration dataclass
"""
