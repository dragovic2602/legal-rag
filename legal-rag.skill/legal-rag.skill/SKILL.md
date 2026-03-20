# Legal RAG — Agent Skill Overview

## What This System Is

A legal knowledge base for a Danish lawyer. Documents (law books, court decisions, legal commentaries) are ingested via a Docling/OpenAI pipeline and stored in Supabase (PostgreSQL + PGVector). Claude Code is the primary interface — it queries the knowledge base through MCP tools and reasons over results.

**This is not a chatbot demo. Legal accuracy is critical. Never synthesise legal conclusions from general knowledge — always search first.**

## MCP Tools Available

Two tools are exposed via the `legal-rag` MCP server:

### `search_knowledge_base(query, limit, source_filter)`

Hybrid vector + full-text search over all ingested law documents. Returns ranked chunks with source citations.

- `query` (str) — natural language query
- `limit` (int, default 5) — number of results (1–10)
- `source_filter` (str, optional) — restrict to a specific document, e.g. `"Tinglysningsloven.pdf"`

### `list_documents()`

Returns all documents currently in the knowledge base with their source filenames. Call this at the start of a session to know what's available and to get exact filenames for `source_filter`.

## Tech Stack

| Layer | Technology |
| ----- | ---------- |
| Document parsing | Docling (PDF/DOCX/PPTX/HTML), PyMuPDF fallback, Whisper for audio |
| Chunking | DoclingHybridChunker — max 512 tokens, preserves heading hierarchy |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
| Storage | Supabase PostgreSQL + PGVector |
| Search | `match_chunks_hybrid()` — RRF fusion of vector cosine + `tsvector` full-text |
| Reranking | Python-level diversity penalty (−0.1 per extra chunk from same doc) |
| Interface | Claude Code via MCP (stdio transport, auto-started via `.mcp.json`) |

## Reference Files

| File | When to read it |
| ---- | --------------- |
| `references/core-mcp-tools.md` | Full API reference for both MCP tools — parameters, return format, example calls |
| `references/core-hybrid-search.md` | How `match_chunks_hybrid()` works — RRF formula, scoring, what similarity scores mean |
| `references/core-ingestion.md` | How documents enter the system — formats, commands, cache, change detection |
| `references/features-source-filtering.md` | How to use `source_filter` to scope search to one law document |
| `references/features-diversity-reranking.md` | The in-Python reranking step — why results may differ from raw similarity order |
| `references/schema-and-performance.md` | Index inventory, column types, known anti-patterns, transaction patterns, diagnostic SQL |
| `references/advanced-danish-legal-terminology.md` | Danish legal synonyms and law name mappings (**Phase 2 — placeholder**) |

## Workflow

1. **Start of session**: Call `list_documents()` to see what's in the knowledge base
2. **Legal question**: Identify the relevant law(s) from document names → call `search_knowledge_base()` with `source_filter` if applicable
3. **Weak results**: Try 2–3 rephrased queries (Danish + English terms, formal + informal phrasing)
4. **Answer**: Cite every claim with `[Kilde: <filename>, § <section>]` — never assert without a retrieved chunk
5. **Not found**: If multiple search strategies return nothing, say it's not in the knowledge base

## What NOT to Do

- Do not answer legal questions from training knowledge — always search
- Do not cite a source you did not retrieve in this session
- Do not combine results from searches without checking for contradictions
- Do not assume a law applies — check if the specific version is in the knowledge base
