-- Phase 2: Add pgvector extension and embedding column for semantic search
-- Run this in Supabase SQL Editor after running the main schema.sql

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column to document_chunks table
ALTER TABLE document_chunks 
ADD COLUMN IF NOT EXISTS embedding vector(1536); 
-- 1536 dimensions for OpenAI text-embedding-3-small (or text-embedding-ada-002)
-- For text-embedding-3-large, use 3072 dimensions

-- Create index for fast similarity search using cosine distance
CREATE INDEX IF NOT EXISTS idx_chunks_embedding 
ON document_chunks 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
-- Note: ivfflat index works best with at least 100 rows
-- For smaller datasets, you can use a regular index or no index

-- Optional: Create a function to find similar chunks
CREATE OR REPLACE FUNCTION find_similar_chunks(
    query_embedding vector(1536),
    kb_id_param UUID,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INTEGER,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE 
        dc.knowledge_base_id = kb_id_param
        AND dc.embedding IS NOT NULL
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Add comment
COMMENT ON COLUMN document_chunks.embedding IS 'Vector embedding for semantic search (1536 dimensions for OpenAI embeddings)';
COMMENT ON FUNCTION find_similar_chunks IS 'Find similar chunks using cosine similarity search';












