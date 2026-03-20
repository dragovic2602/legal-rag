# Scaling Notes

Things that are intentionally left as-is because they are correct for current scale,
but need to be revisited when the dataset grows.

---

## IVFFlat Index — `lists = 1` (`sql/schema.sql:34`)

**Current state:** `lists = 1` — brute-force exact nearest neighbor search.

**Why it's correct right now:**
- With small chunk counts (< ~2,000), `lists=1` scans all vectors and returns exact results.
- Increasing `lists` with few data points produces poor clusters and with default `probes=1`
  would only search a fraction of the data — meaning it could miss the actual best match.
  Worse accuracy, zero performance gain. `lists=1` is the right choice at small scale.

**When to change it:**
- When you have 5,000+ chunks and notice query latency climbing above 200-300ms.
- Rule of thumb: `lists = ceil(sqrt(total_chunk_count))`
  - 5,000 chunks → lists = 71
  - 10,000 chunks → lists = 100
  - 50,000 chunks → lists = 224

**How to apply the change (against live Supabase):**
```sql
-- 1. Drop the old index
DROP INDEX idx_chunks_embedding;

-- 2. Recreate with tuned lists (replace 100 with your calculated value)
CREATE INDEX idx_chunks_embedding ON chunks
  USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```
Run this in the Supabase SQL editor. No data is lost. Query performance improves immediately.

**Also consider at that point:**
- Tuning `probes` (how many partitions to search at query time). Default is 1.
  Higher probes = better recall, slower queries. `probes = sqrt(lists)` is a good starting point.
  Set via: `SET ivfflat.probes = 10;` before querying.
- Switching from IVFFlat to HNSW (`USING hnsw`) for better recall at high scale.

---

## Similarity Threshold on Retrieval (`cli.py`, `sql/schema.sql`)

**Current state:** `match_chunks_hybrid` returns top-K results with no minimum score cutoff.

**Why it's fine right now:**
- The CLI uses RRF (Reciprocal Rank Fusion) scores, which are relative rankings — not raw
  cosine similarity. A threshold of e.g. 0.6 applied to RRF scores is meaningless without calibration.
- In a small knowledge base, all cosine scores may be low (0.4–0.6) due to specialized content.
  A hard cutoff would break legitimate retrieval.
- gpt-4o-mini reads the returned results and decides relevance itself. The system prompt instructs
  it to say when info isn't in the KB.

**When to revisit:**
- Once you have 50+ documents and can measure what a "bad" similarity score actually looks like
  in your specific corpus. Build a small eval set (20–30 labeled query-document pairs), run queries,
  and inspect the score distribution. Set the threshold at a natural gap between good and bad results.
- For `match_chunks` (non-hybrid), a cosine threshold of ~0.5–0.6 is more intuitive to add since
  cosine scores ARE on a 0–1 scale.

---

## Chunk Insert Performance (`ingestion/ingest.py`)

**Current state:** Chunks inserted one-by-one inside a transaction.

**Fine until:** ~500 chunks per document. Beyond that, consider `executemany()` batch inserts.

---

## Deletion Loop (`ingestion/ingest.py:123-128`)

**Current state:** One DB round-trip per deleted document.

**Fine until:** Hundreds of deletions per run. Beyond that, use `DELETE WHERE source = ANY($1)`.

---

## In-Memory Metadata Load (`ingestion/ingest.py:113-117`)

**Current state:** All document metadata loaded into memory at the start of each run.

**Fine until:** ~10,000+ documents (roughly 10MB RAM). Beyond that, add pagination or DB-side filtering.
