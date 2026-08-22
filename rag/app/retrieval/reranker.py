"""
Reranking module (optional for MVP).

Reranks initial retrieval results by relevance.

Usage: Optional enhancement after initial vector search
Trigger: When basic retrieval quality is poor

Classes:
- Reranker: Reranking engine

Functions:
- rerank(): Reorder chunks by relevance
- calculate_relevance_score(): Score chunk relevance
"""
