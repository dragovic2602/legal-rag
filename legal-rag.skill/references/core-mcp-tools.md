# Core MCP Tools — API Reference

Both tools are exposed by the `legal-rag` MCP server (`mcp_server.py`), auto-started by Claude Code via `.mcp.json` (stdio transport).

---

## `search_knowledge_base`

Search the legal knowledge base using hybrid vector + full-text search.

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Natural language search query |
| `limit` | int | 5 | Number of results to return. Clamped to 1–10. |
| `source_filter` | str \| None | None | Optional: restrict to documents whose `source` field contains this string (case-insensitive, partial match). E.g. `"Tinglysningsloven.pdf"` or `"leje"`. |

### How It Works (internally)

1. Generates a 1536-dim OpenAI embedding for `query`
2. Calls `match_chunks_hybrid(embedding, query_text, candidates)` in Supabase — returns `limit * 3` candidates via RRF scoring
3. Applies Python-level diversity reranking (−0.1 penalty per extra chunk from same document)
4. Filters by `source_filter` if provided
5. Returns top `limit` results

### Return Format

```
Found N relevant results:

[Source: <document_title> | <source_filename>]
<chunk_content>
---
[Source: ...]
<chunk_content>
```

### Example Call

```python
# Search all documents
search_knowledge_base("hvad er fristen for at klage over en ejendomsvurdering")

# Search with source filter
search_knowledge_base(
    query="depositum lejer",
    limit=8,
    source_filter="Lov om leje.pdf"
)
```

### Error Responses

```
No results found for '<query>' in documents matching '<source_filter>'.
# → filter too narrow; retry without source_filter

No relevant results found in the knowledge base.
# → query returned nothing; try rephrasing or broader terms
```

---

## `list_documents`

List all documents currently ingested in the legal knowledge base.

### Parameters

None.

### Return Format

```
N documents in knowledge base:

- <Document Title>  →  <source_filename>
- <Document Title>  →  <source_filename>
...
```

The `source_filename` values are what you pass as `source_filter` in `search_knowledge_base`.

### Example Call

```python
list_documents()
```

### Example Response

```
42 documents in knowledge base:

- Tinglysningsloven  →  Tinglysningsloven.pdf
- Lov om leje  →  Lov om leje.pdf
- Andelsboligforeningsloven  →  Andelsboligforeningsloven.pdf
...
```

### When the Knowledge Base is Empty

```
The knowledge base is empty. Run the ingestion pipeline to add documents.
# → User needs to run: .venv/Scripts/python -m indexing.pipeline
```

---

## When to Use Each Tool

| Situation | Action |
|-----------|--------|
| Start of session | Call `list_documents()` first |
| Question about a specific law | Call `list_documents()` → match law → `search_knowledge_base()` with `source_filter` |
| Comparative question across laws | `search_knowledge_base()` without filter |
| Uncertain which law applies | `search_knowledge_base()` without filter, then check sources in results |
| Filtered search returns nothing | Retry without `source_filter` |
| Results feel incomplete | Try 2–3 rephrased queries and combine results |
