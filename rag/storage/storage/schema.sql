CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS documents CASCADE;
DROP INDEX IF EXISTS idx_chunks_embedding;
DROP INDEX IF EXISTS idx_chunks_document_id;
DROP INDEX IF EXISTS idx_documents_metadata;

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
CREATE INDEX idx_documents_created_at ON documents (created_at DESC);

-- UNIQUE constraint to prevent phantom duplicates from concurrent ingestion
ALTER TABLE documents ADD CONSTRAINT documents_source_unique UNIQUE (source);

CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),
    chunk_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    token_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_chunks_document_id ON chunks (document_id);
CREATE INDEX idx_chunks_chunk_index ON chunks (document_id, chunk_index);

CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(1536),
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id AS chunk_id,
        c.document_id,
        c.content,
        1 - (c.embedding <=> query_embedding) AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source
    FROM chunks c
    JOIN documents d ON c.document_id = d.id
    WHERE c.embedding IS NOT NULL
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- OneDrive sync tracking
CREATE TABLE IF NOT EXISTS synced_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    onedrive_item_id TEXT UNIQUE NOT NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    filename TEXT NOT NULL,
    etag TEXT,
    last_synced_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    onedrive_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_synced_files_item_id ON synced_files (onedrive_item_id);
CREATE INDEX IF NOT EXISTS idx_synced_files_document_id ON synced_files (document_id);

-- Key/value store for sync state (e.g. delta link)
CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Hybrid Search (Feature 2)

-- Add full-text search column to chunks
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS search_vector tsvector;
CREATE INDEX IF NOT EXISTS idx_chunks_search ON chunks USING gin(search_vector);

-- Auto-populate search_vector on insert/update
CREATE OR REPLACE FUNCTION chunks_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', coalesce(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER chunks_search_vector_trigger
BEFORE INSERT OR UPDATE ON chunks
FOR EACH ROW EXECUTE FUNCTION chunks_search_vector_update();

-- Hybrid search function using RRF scoring
CREATE OR REPLACE FUNCTION match_chunks_hybrid(
    query_embedding vector(1536),
    query_text TEXT,
    match_count INT DEFAULT 5,
    rrf_k INT DEFAULT 60
)
RETURNS TABLE (
    chunk_id UUID,
    document_id UUID,
    content TEXT,
    similarity FLOAT,
    metadata JSONB,
    document_title TEXT,
    document_source TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH vector_ranked AS (
        SELECT c.id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) AS rank
        FROM chunks c WHERE c.embedding IS NOT NULL
    ),
    text_ranked AS (
        SELECT c.id, ROW_NUMBER() OVER (
            ORDER BY ts_rank_cd(
                c.search_vector,
                websearch_to_tsquery('english', query_text),
                1
            ) DESC
        ) AS rank
        FROM chunks c WHERE c.search_vector @@ websearch_to_tsquery('english', query_text)
    ),
    rrf AS (
        SELECT
            COALESCE(v.id, t.id) AS id,
            COALESCE(1.0/(rrf_k + v.rank), 0) + COALESCE(1.0/(rrf_k + t.rank), 0) AS score
        FROM vector_ranked v FULL OUTER JOIN text_ranked t ON v.id = t.id
    )
    SELECT
        c.id AS chunk_id,
        c.document_id,
        c.content,
        r.score AS similarity,
        c.metadata,
        d.title AS document_title,
        d.source AS document_source
    FROM rrf r
    JOIN chunks c ON c.id = r.id
    JOIN documents d ON d.id = c.document_id
    ORDER BY r.score DESC
    LIMIT match_count;
END;
$$;
