"""
CivicAI RAG (Retrieval-Augmented Generation) service.

Main components:
- api: REST API endpoints
- ingestion: Document processing pipeline
- embeddings: Vector embedding generation
- retrieval: Semantic search
- generation: LLM-based answer generation
- vector_store: Pgvector database integration
- schemas: Request/response validation
- utils: Helpers and utilities

Usage:
from backend.app.rag.api.generate import generate_answer
answer = await generate_answer(query, service, language)
"""
