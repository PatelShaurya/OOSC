"""
Supabase PostgreSQL + pgvector integration.

Handles:
- Connect to Supabase
- Perform similarity search with pgvector
- Store embeddings with metadata
- Metadata filtering in queries
- Chunk storage and retrieval

Classes:
- SupabaseVectorStore: Supabase vector database wrapper

Functions:
- connect(): Establish connection
- insert_embedding(): Store embedding + metadata
- similarity_search(): Query by vector similarity
- similarity_search_with_filter(): Add metadata filters
- delete_embedding(): Remove embedding
- health_check(): Test connection
"""
