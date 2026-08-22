"""
Vector retrieval module.

Workflow:
1. Embed query with same model as documents
2. Perform vector similarity search in pgvector
3. Apply metadata filters based on service
4. Optional reranking
5. Return top-K results

Classes:
- Retriever: Main retrieval engine

Functions:
- retrieve(): Get relevant chunks for a query
- retrieve_with_filter(): Apply service-specific filtering
- similarity_search(): Low-level vector similarity search
"""
