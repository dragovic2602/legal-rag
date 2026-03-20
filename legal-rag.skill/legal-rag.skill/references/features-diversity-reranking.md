# Feature: Diversity Reranking

After the SQL search (`match_chunks_hybrid`), a Python reranking step adjusts scores to prevent any single document from monopolising the top results.

---

## The Algorithm

```python
# In mcp_server.py (also mirrored in retrieval/search.py)

seen_docs: dict[str, float] = {}
reranked: list[tuple[dict, float]] = []

for row in rows:
    doc_id = str(row["document_id"])
    penalty = seen_docs.get(doc_id, 0.0)      # 0.0 for first chunk, 0.1 for second, 0.2 for third...
    seen_docs[doc_id] = penalty + 0.1          # increment for next chunk from same doc
    reranked.append((dict(row), float(row["similarity"]) - penalty))

reranked.sort(key=lambda x: x[1], reverse=True)
```

- **First chunk** from a document: no penalty (0.0)
- **Second chunk** from same document: −0.1 penalty
- **Third chunk**: −0.2 penalty
- And so on

---

## Why This Exists

Without diversity reranking, a long law that matches the query well could fill all top-N results with its own chunks, burying relevant information from other laws.

Example: searching for "ejendom" could return 10 chunks all from `Tinglysningsloven.pdf`, even though `Planloven.pdf` and `Ejerlejlighedsloven.pdf` also have highly relevant sections.

Diversity reranking ensures cross-document coverage at a slight per-document precision cost.

---

## Effect on Results

- The `similarity` score you see in raw SQL output will be higher than the post-reranking score for documents with multiple matching chunks
- If `source_filter` is active, diversity reranking still runs but has less effect (all results are from the same document anyway)
- With `limit=5`, you typically get results from at least 3–4 different documents unless the query is extremely specific to one law

---

## Interaction with `limit` and Candidates

The search fetches `limit * 3` candidates from SQL before reranking:

```python
candidates = limit * 3  # fetch extra for diversity reranking + filtering
```

With `limit=5`, it fetches 15 candidates from SQL, reranks them, then returns top 5. This gives the diversity algorithm enough material to redistribute across documents.

Increasing `limit` gives better cross-document coverage when the query spans multiple laws.
