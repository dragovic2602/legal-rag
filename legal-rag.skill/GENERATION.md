# Generation Metadata

Generated: 2026-03-19

Source files:
- `mcp_server.py` — MCP tool definitions, source_filter logic, diversity reranking
- `retrieval/search.py` — canonical search_knowledge_base implementation
- `storage/schema.sql` — match_chunks_hybrid SQL function, HNSW index config
- `indexing/extraction.py` — document extraction pipeline
- `indexing/pipeline.py` — ingestion orchestrator and CLI arguments
- `CLAUDE.md` — project architecture and commands

Git SHA: 769ebf0d68c317080c82020d2dc77c74993e8c72

Phase 2 files still needing live data:
- `references/advanced-danish-legal-terminology.md` — needs `list_documents()` + `search_knowledge_base()` against production data
- `../../../.claude/skills/legal-search/rules/route-by-document.md` — needs real filenames from `list_documents()`
