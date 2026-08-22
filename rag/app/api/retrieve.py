"""
Debug endpoint for RAG retrieval evaluation.

POST /retrieve
Returns raw retrieved chunks before LLM processing.
Used by RAG team for testing and evaluation.

Input: query, service, language, top_k
Output: chunks with scores and metadata
"""
