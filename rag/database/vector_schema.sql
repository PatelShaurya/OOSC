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

-- Additional lookup indexes for fast document filtering
CREATE INDEX IF NOT EXISTS document_chunks_doc_id_idx ON document_chunks (document_id);
CREATE INDEX IF NOT EXISTS document_chunks_doc_type_idx ON document_chunks (document_type);
CREATE INDEX IF NOT EXISTS document_chunks_authority_idx ON document_chunks (issuing_authority);

-- PostgreSQL RPC Function for Cosine Similarity Search with Metadata Filtering
-- Supports optional filtering by document_id, document_type, and issuing_authority.
CREATE OR REPLACE FUNCTION match_document_chunks (
    query_embedding vector(1024),
    match_count INT DEFAULT 5,
    filter_document_id TEXT DEFAULT NULL,
    filter_document_type TEXT DEFAULT NULL,
    filter_issuing_authority TEXT DEFAULT NULL
)
RETURNS TABLE (
    id BIGINT,
    chunk_id TEXT,
    document_id TEXT,
    content TEXT,
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
    similarity_score FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.chunk_id,
        dc.document_id,
        dc.content,
        dc.document_title,
        dc.document_type,
        dc.issuing_authority,
        dc.source_url,
        dc.page_start,
        dc.page_end,
        dc.chapter,
        dc.section,
        dc.parent_section,
        dc.subsection,
        dc.chunk_index,
        (1 - (dc.embedding <=> query_embedding))::FLOAT AS similarity_score
    FROM document_chunks dc
    WHERE dc.embedding IS NOT NULL
      AND (filter_document_id IS NULL OR dc.document_id = filter_document_id)
      AND (filter_document_type IS NULL OR dc.document_type = filter_document_type)
      AND (filter_issuing_authority IS NULL OR dc.issuing_authority = filter_issuing_authority)
    ORDER BY dc.embedding <=> query_embedding ASC
    LIMIT match_count;
END;
$$;
