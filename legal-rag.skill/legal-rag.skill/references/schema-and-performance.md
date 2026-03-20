# Schema & Performance Notes

Reference for sub-agents writing SQL, migrations, or debugging database performance.
Adapted from `guidelines/database-reviewer.md` (PostgreSQL best practices).

---

## Index Inventory

| Index | Table | Columns | Type | Purpose |
|-------|-------|---------|------|---------|
| `idx_chunks_embedding` | chunks | `embedding` | HNSW (cosine) | Vector similarity search — m=16, ef_construction=64 |
| `idx_chunks_search` | chunks | `search_vector` | GIN | Full-text search (`tsvector`) |
| `idx_chunks_document_id` | chunks | `document_id` | BTree | FK lookup — always index foreign keys |
| `idx_chunks_chunk_index` | chunks | `(document_id, chunk_index)` | BTree | Ordered chunk retrieval — equality (doc_id) first |
| `idx_documents_metadata` | documents | `metadata` | GIN | JSONB field lookups |
| `idx_documents_created_at` | documents | `created_at DESC` | BTree | Time-ordered queries |
| `documents_source_unique` | documents | `source` | UNIQUE | Prevents duplicate ingestion |

**Foreign key rule:** `chunks.document_id → documents.id` is indexed (`idx_chunks_document_id`). Always index FK columns — unindexed FKs cause sequential scans on DELETE/UPDATE cascades.

---

## Column Types — What We Use and Why

| Column | Type | Why |
|--------|------|-----|
| `id` | `UUID` (uuid_generate_v4) | Standard PK — note: random UUIDv4 causes index fragmentation at scale; UUIDv7 or BIGINT IDENTITY would be better, but migration cost is high |
| `content` | `TEXT` | No `varchar(n)` — PostgreSQL `text` is equivalent and avoids arbitrary length limits |
| `embedding` | `vector(1536)` | PGVector type, 1536 dims for OpenAI text-embedding-3-small |
| `metadata` | `JSONB` | Binary JSON — GIN-indexed for fast key lookups |
| `created_at` / `updated_at` | `TIMESTAMP WITH TIME ZONE` | Always use timestamptz — plain `timestamp` loses timezone info |
| `token_count` | `INTEGER` | Fine for chunk sizes (always < 2B) |

---

## Known Anti-Patterns in This Codebase

### `SELECT *` from SQL functions
The MCP server originally used `SELECT * FROM match_chunks_hybrid(...)`. This is an anti-pattern:
- Fetches `metadata JSONB` and `chunk_id UUID` columns that are never used in the response
- Any future column additions silently bloat the result set

**Fixed:** `mcp_server.py` now explicitly selects `chunk_id, document_id, content, similarity, document_title, document_source`.

### Column name aliasing — know your return names
`match_chunks_hybrid` returns:
```sql
d.source AS document_source   -- NOT "source"
d.title AS document_title     -- NOT "title"
c.id AS chunk_id              -- NOT "id"
```
When accessing asyncpg `Record` objects (or converting with `dict(row)`), use the **alias** name, not the original column name:
```python
row["document_source"]   # ✓
row["source"]            # ✗ — returns KeyError or None
```

---

## Transaction Pattern — Why We Acquire Connection After Embedding

Embedding generation calls the OpenAI API (network I/O, ~200–500ms). Our code correctly acquires the DB connection **after** the embedding is ready:

```python
query_embedding = await embedder.embed_query(query)  # network call — outside connection
async with db_pool.acquire() as conn:                # acquire only for DB work
    rows = await conn.fetch(...)
```

**Why this matters:** Holding a DB connection during external API calls wastes pool slots and risks hitting connection limits. Always keep transactions short — no external calls inside `async with conn`.

---

## RLS (Row Level Security)

RLS is **not currently enabled** on `documents` or `chunks`. For this single-user lawyer setup that's acceptable, but if multi-user access is added:

- Enable RLS: `ALTER TABLE documents ENABLE ROW LEVEL SECURITY;`
- Use `(SELECT auth.uid())` pattern (not `auth.uid()`) to avoid per-row function calls
- Index the `user_id` column used in RLS policies (critical for performance)
- Revoke public schema access: `REVOKE ALL ON SCHEMA public FROM anon, authenticated;`

---

## Performance Checklist for New SQL

Before adding any new query:

- [ ] WHERE/JOIN columns have indexes
- [ ] No `SELECT *` in function calls — name the columns you need
- [ ] No N+1 patterns — batch lookups where possible
- [ ] Connection acquired after any external I/O (embeddings, HTTP calls)
- [ ] Use `LIMIT` to bound result sets
- [ ] For new functions returning aliased columns: document the alias names here

---

## Useful Diagnostic Queries

Run against Supabase via `psql $DATABASE_URL` or Supabase SQL editor:

```sql
-- Slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 10;

-- Table sizes
SELECT relname, pg_size_pretty(pg_total_relation_size(relid))
FROM pg_stat_user_tables
ORDER BY pg_total_relation_size(relid) DESC;

-- Index usage — find unused indexes
SELECT indexrelname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- Check HNSW index is being used for vector search
EXPLAIN ANALYZE
SELECT id FROM chunks
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```
