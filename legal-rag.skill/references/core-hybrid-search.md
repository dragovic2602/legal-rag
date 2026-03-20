# Core Hybrid Search — How It Works

Understanding this helps you interpret search results correctly and know when to trust them.

---

## Two Search Signals

`match_chunks_hybrid()` combines two independent ranking signals using Reciprocal Rank Fusion (RRF):

### 1. Vector Search (Semantic)
- Generates cosine similarity between the query embedding and each chunk embedding
- Embedding model: OpenAI `text-embedding-3-small` (1536 dimensions)
- Index: HNSW (`vector_cosine_ops`, m=16, ef_construction=64) — accurate recall without training
- Catches semantic matches: "udlejer" matches "landlord", paraphrases, synonyms

### 2. Full-Text Search (Lexical)
- Uses PostgreSQL `tsvector` + `websearch_to_tsquery('english', query_text)`
- Scored with `ts_rank_cd(..., 1)` — length-normalised (BM25-like, divides by document length)
- GIN index on `search_vector` column (auto-populated by trigger on insert/update)
- Catches exact term matches: §-numbers, law references, specific legal phrases

---

## Reciprocal Rank Fusion (RRF)

The two ranked lists are fused into a single score:

```
RRF_score = 1/(k + rank_vector) + 1/(k + rank_fulltext)
```

Where `k = 60` (default). Chunks that appear high in both lists score highest. Chunks that only match one signal still score, but lower.

**Full SQL** (from `storage/schema.sql`):

```sql
WITH vector_ranked AS (
    SELECT c.id, ROW_NUMBER() OVER (ORDER BY c.embedding <=> query_embedding) AS rank
    FROM chunks c WHERE c.embedding IS NOT NULL
),
text_ranked AS (
    SELECT c.id, ROW_NUMBER() OVER (
        ORDER BY ts_rank_cd(c.search_vector, websearch_to_tsquery('english', query_text), 1) DESC
    ) AS rank
    FROM chunks c WHERE c.search_vector @@ websearch_to_tsquery('english', query_text)
),
rrf AS (
    SELECT
        COALESCE(v.id, t.id) AS id,
        COALESCE(1.0/(rrf_k + v.rank), 0) + COALESCE(1.0/(rrf_k + t.rank), 0) AS score
    FROM vector_ranked v FULL OUTER JOIN text_ranked t ON v.id = t.id
)
```

---

## In-Python Diversity Reranking

After SQL search, a Python step applies a diversity penalty (in `mcp_server.py` and `retrieval/search.py`):

```python
seen_docs: dict[str, float] = {}
for row in rows:
    doc_id = str(row["document_id"])
    penalty = seen_docs.get(doc_id, 0.0)
    seen_docs[doc_id] = penalty + 0.1
    reranked.append((dict(row), float(row["similarity"]) - penalty))
```

Effect: each additional chunk from the same document is penalised by −0.1. This prevents one long law from dominating all top results.

See `references/features-diversity-reranking.md` for full details.

---

## What the `similarity` Score Means

The `similarity` value returned is the **RRF score**, not a cosine similarity percentage:
- Typical range: 0.01 – 0.04 (before diversity penalty)
- Higher = more relevant to the query
- After diversity penalty, scores of chunks from frequently-appearing documents decrease
- Do not interpret as a confidence percentage — use it only for relative ranking

---

## Why Hybrid Beats Pure Vector

Pure vector search fails when:
- The query uses exact legal terms (§ numbers, law citations) that don't appear in training embeddings
- Danish terms have no close English analogues in the embedding space
- Short queries ("§ 12 stk. 2") have poor embedding representations

Pure full-text fails when:
- User paraphrases or uses informal language
- Query uses synonyms not in the document
- Cross-language queries (Danish question, English document)

Hybrid with RRF captures both: precise legal term recall + semantic understanding.
