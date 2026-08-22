-- CivicAI RAG Vector Store Schema
-- Enable the pgvector extension to work with vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing legal document chunks and BGE-M3 1024-dimensional embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chunk_id TEXT NOT NULL,
    document_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    document_title TEXT,
    document_type TEXT,
    issuing_authority TEXT,
    source_url TEXT,
    page_start INT,
    page_end INT,
    chapter TEXT,
    section TEXT,
    parent_section TEXT,
    subsection TEXT,
    chunk_index INT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_doc_chunk UNIQUE (document_id, chunk_id)
);

-- HNSW Vector Index optimized for Cosine Distance (<=>)
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON document_chunks 
USING hnsw (embedding vector_cosine_ops);

-- Additional lookup index for fast filtered document queries
CREATE INDEX IF NOT EXISTS document_chunks_doc_id_idx 
ON document_chunks (document_id);
