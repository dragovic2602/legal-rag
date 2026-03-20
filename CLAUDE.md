# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Legal knowledge base RAG system for a lawyer. Automatically ingests documents (local + OneDrive), chunks and embeds them via Docling + OpenAI, stores in Supabase/PGVector. **Primary interface: Claude Code with the `legal-rag` MCP server** — Claude IS the agent.

## Tilgængelige MCPs

Se `.claude/skills/mcp-guide/SKILL.md` for komplet oversigt, workflows og beslutningsguide.

| MCP | Hvad | Konfiguration |
| --- | --- | --- |
| `legal-rag` | Juridisk vidensbase (love, domme, cirkulærer) | stdio, `.mcp.json` |
| `ois` | OIS.dk — samlet ejendomsdata, vurdering, BBR-PDF, plandata | HTTP, `.mcp.json` |
| `supabase` | Supabase DB administration | stdio, `.mcp.json` |
| `BBR` | Datafordeler BBR GraphQL — struktureret bygningsdata | HTTP, global config |
| `Matriklen` | Datafordeler Matriklen WFS — matrikelnr, noteringer, strandbeskyttelse | HTTP, global config |
| `Ejendomsvurdering` | Datafordeler VUR — officielle ejendomsvurderinger | HTTP, global config |
| `Browser` | Web-browser til åbne API'er og JavaScript-sider | HTTP, global config |

**Adresse → BFE:** `get_bbr_by_address(adresse)` → BFE → `ois_property_info(bfe)`

---

## Legal Knowledge Base — How to Use the MCP Tools

Two MCP tools are available: `search_knowledge_base` and `list_documents`.

> **MCP troubleshooting:** If the `legal-rag` server is not connected (tools unavailable), use Command Palette → **"Developer: Reload Window"** (not "Claude: Restart MCP Server" — that command does not exist in the VSCode extension). The server auto-starts via `.mcp.json` but may not connect in all sessions. Do NOT fall back to Bash/Python to query Supabase — wait for the MCP connection.
>
> **First tool call latency:** The first call per session takes ~6s (DB connection pool init + OpenAI embedding). Subsequent calls are ~1–2s. This is normal — not a hang.
>
> **OpenAI embeddings cost:** `text-embedding-3-small` costs ~$0.0000004 per query. Running 100.000 searches costs ~$2. Do not attempt to bypass embeddings to save cost.

**Before answering any legal question:**

1. Call `list_documents()` to see what laws/documents are in the knowledge base
2. If the question is about a specific law, use `search_knowledge_base(query, source_filter="exact_filename.pdf")`
3. For complex or ambiguous questions, run 2–3 searches with different phrasings before answering
4. Evaluate whether the returned chunks actually answer the question — if not, search again with different terms or a broader query
5. Always cite the source document and section (§ number if visible) in your answer
6. If the answer is not in the knowledge base, say so explicitly — do not guess or hallucinate legal content

**Search strategies (use Claude's own reasoning — no extra API cost):**

- **Routing:** Call `list_documents()` first, identify the relevant law, pass it as `source_filter`
- **Multi-query:** Run 2–3 searches with different phrasings (e.g. "depositum", "sikkerhedsstillelse", "deposit") and combine results
- **Broad → narrow:** If a specific search returns nothing, try a broader query then filter the results yourself
- **Relevance check:** Read the chunks critically — if they don't actually answer the question, search again rather than forcing an answer

## Commands

All Python code lives in `rag/`. Set `PYTHONPATH` to `rag/` when running modules, or `cd rag/` first.

> **Note on `.mcp.json` PYTHONPATH:** The MCP server requires multiple paths because packages are nested one level deeper (e.g. `rag/storage/storage/`). The `.mcp.json` already has all required paths set: `rag`, `rag/storage`, `rag/indexing`, `rag/retrieval`, `rag/generation`. Do not simplify this to just `rag/` — imports will break.

```bash
# Ingestion — smart incremental (skips unchanged files)
PYTHONPATH=rag .venv/Scripts/python -m indexing.pipeline

# Ingestion — force full wipe + re-ingest
PYTHONPATH=rag .venv/Scripts/python -m indexing.pipeline --force

# Ingestion — disable HybridChunker (faster, no Docling tokenizer startup)
PYTHONPATH=rag .venv/Scripts/python -m indexing.pipeline --no-semantic

# RAG CLI agent (hybrid search, streaming)
PYTHONPATH=rag .venv/Scripts/python -m cli

# File watcher — auto-ingests on any change in documents/ folder
PYTHONPATH=rag .venv/Scripts/python rag/watch_service.py

# FastAPI server — OpenAI-compatible API (Open WebUI / Ollama frontend)
PYTHONPATH=rag .venv/Scripts/python -m uvicorn main:app --reload

# MCP server (Claude Code auto-starts this via .mcp.json)
PYTHONPATH=rag .venv/Scripts/python rag/mcp_server.py

# Linting / formatting
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m black .
```

## Required Environment Variables (`.env`)

```env
DATABASE_URL=          # Supabase PostgreSQL connection string
OPENAI_API_KEY=        # Used for embeddings (always) and LLM (default)
LLM_CHOICE=            # e.g. gpt-4o-mini (default), overridable per request
AGENT_NAME=            # Display name shown in /v1/models
OLLAMA_BASE_URL=       # e.g. http://172.17.0.1:11435 (optional)
OLLAMA_MODELS=         # Comma-separated Ollama model IDs (optional)
```

## Architecture

### Data Flow

```text
documents/ → DocumentIngestionPipeline → Docling converter → HybridChunker
           → OpenAI text-embedding-3-small (1536 dims) → Supabase PGVector
```

### Agent Architecture

Single canonical agent used by both `cli.py` and `main.py`:

- **`generation/agent.py`** — PydanticAI agent factory (`build_agent`, `get_agent`). Supports OpenAI and Ollama LLMs.
- **`retrieval/search.py`** — `search_knowledge_base()` tool, shared by CLI and API. Uses `match_chunks_hybrid()` + in-Python diversity reranking (−0.1 per additional chunk from the same document).
- **`agent.py`** (root) — thin shim re-exporting from `generation.agent`; keeps `main.py` imports stable.

### Two Search Functions in Schema (`storage/schema.sql`)

- **`match_chunks(query_embedding, match_count)`** — pure vector cosine similarity
- **`match_chunks_hybrid(query_embedding, query_text, match_count, rrf_k)`** — Reciprocal Rank Fusion combining vector search and PostgreSQL full-text (`tsvector`, `ts_rank_cd` with length normalisation). `retrieval/search.py` applies an in-Python diversity penalty (−0.1 per additional chunk from the same document). Embedding index uses HNSW for accurate recall without training. **Full-text uses `danish` language config** — both the `chunks_search_vector_update` trigger and `match_chunks_hybrid` are configured for Danish stemming and stop words.

### Ingestion: Change Detection

- `source` column = `os.path.relpath(file_path, documents_folder)` — unique key per document
- `file_mtime` is stored as a string in the `metadata` JSONB column
- On each run: deleted files → `DELETE FROM documents WHERE source = $1`; changed files → delete old + re-ingest; unchanged files → skipped
- `--force` wipes all `chunks` + `documents` rows before re-ingesting everything

### Chunking Strategy

- **Primary**: `DoclingHybridChunker` — requires a `DoclingDocument` object (returned by Docling's `DocumentConverter.convert()`). Uses `sentence-transformers/all-MiniLM-L6-v2` tokenizer, max 512 tokens, chunks include heading hierarchy context. Falls back to simple sliding window when no `DoclingDocument` is available (e.g. plain text/markdown files).
- **Fallback**: `SimpleChunker` — paragraph-based, used when `--no-semantic` flag is passed.
- The `DocumentConverter` is singleton-initialized once per pipeline run and reused across all files (initialization takes ~30s on first run).

### Document Extraction Pipeline (`indexing/extraction.py`)

1. **Docling** — primary for PDF/DOCX/PPTX/XLSX/HTML (returns `DoclingDocument` for HybridChunker)
2. **PyMuPDF + RapidOCR** — fallback for PDFs when Docling fails (scanned pages use OCR)
3. **Whisper ASR (via Docling)** — for audio files (`.mp3`, `.wav`, `.m4a`, `.flac`)
4. **Stub record** — last resort; file is still searchable by name, marked `extraction_failed: true` in metadata

### FastAPI Server (`main.py` + `agent.py`)

- Exposes OpenAI-compatible endpoints: `GET /v1/models`, `POST /v1/chat/completions`
- Supports both OpenAI models (via `OPENAI_API_KEY`) and Ollama models (via `OLLAMA_BASE_URL`/`OLLAMA_MODELS`)
- Embeddings always use OpenAI regardless of LLM choice
- Streaming responses via SSE

## Key Files

All source files live under `rag/`. Python packages are nested one level deeper (e.g. `rag/indexing/indexing/`).

| File | Purpose |
| --- | --- |
| `rag/mcp_server.py` | MCP server — exposes `search_knowledge_base` + `list_documents` to Claude Code |
| `rag/indexing/indexing/pipeline.py` | Smart incremental ingestion pipeline (orchestrator) |
| `rag/indexing/indexing/extraction.py` | Document format extraction (Docling, PyMuPDF, Whisper) |
| `rag/indexing/indexing/chunker.py` | DoclingHybridChunker + SimpleChunker fallback |
| `rag/indexing/indexing/embedder.py` | OpenAI embeddings with caching |
| `rag/retrieval/retrieval/search.py` | Canonical `search_knowledge_base()` — shared by CLI and API |
| `rag/generation/generation/agent.py` | PydanticAI agent factory with hybrid search + diversity reranking |
| `rag/generation/generation/prompts.py` | `SYSTEM_PROMPT` — single source of truth for CLI and API |
| `rag/generation/generation/providers.py` | LLM + embedding provider factories |
| `rag/agent.py` | Root shim — re-exports from `generation.agent` for `main.py` |
| `rag/main.py` | FastAPI OpenAI-compatible API server |
| `rag/cli.py` | Interactive RAG CLI with streaming |
| `rag/storage/storage/db_utils.py` | asyncpg connection pool (`DatabasePool`) |
| `rag/storage/storage/models/` | Pydantic models: `db_models`, `ingestion_models`, `api_models` |
| `rag/storage/schema.sql` | PostgreSQL schema: `documents`, `chunks`, `match_chunks()`, `match_chunks_hybrid()` |
| `rag/sync_service.py` | OneDrive sync service entry point |
| `rag/onedrive/` | MS Graph API client + sync logic |
| `.mcp.json` | Konfigurerer 3 lokale MCP-servere: `legal-rag` (stdio), `ois` (HTTP), `supabase` (stdio). BBR/Matriklen/Vurdering/Browser MCPs konfigureres globalt i claude.ai. |

## Skills Available

### koberbrev — Købersbrevs-workflow

Full 7-phase workflow for generating Danish buyer's letters (køberbrev) including document extraction, 9-agent parallel legal analysis, and Word document filling.
Skill file: `.claude/skills/koberbrev/SKILL.md`

**MCP-first workflow**: Koberbrev bruger FASE 0 der pre-fetcher ejendomsdata via MCPs (OIS, BBR, Matriklen) inden agenter spawnes. Agent E bruger Browser MCP til varmeplan, spildevandsplan og CVR — kun mod godkendte sider i `references/approved-sites.md`. Agent E tilgår IKKE planinfo.dk eller ois.dk — det dækkes af MCPs i FASE 0.

**WSL required** for the fill script:

```bash
wsl pip install docxtpl
wsl python3 .claude/skills/koberbrev/scripts/fill_document.py <template.docx> values.json
```

### mcp-guide — MCP Oversigt og Workflows

Komplet guide til alle tilgængelige MCPs, hvornår bruges hvad, og adresse→BFE workflow.
Skill file: `.claude/skills/mcp-guide/SKILL.md`

### mcp-builder-information-site-noapi — Byg Informations-MCP

Metodologi til at kortlægge og bygge MCP til sites uden offentlig API (Playwright network interception, PDF-håndtering, dynamiske parametre). Brugt til OIS MCP.
Skill file: `.claude/skills/mcp-builder-information-site-noapi/SKILL.md`

### legal-rag.skill — Legal RAG System Oversigt

Oversigt over RAG-systemet, indeksering, søgestrategier og MCP-tools.
Skill file: `.claude/skills/legal-rag.skill/SKILL.md`

### legal-search — Legal Search Protocol

Enforces always-search-first + citation discipline for all legal queries. Auto-loaded.
Skill file: `.claude/skills/legal-search/SKILL.md`

### word-template-converter — Konvertér Word-skabelon

Omdanner et Word-dokument med inkonsistente placeholders (`XXXXX`, `[X]`, `{X}`, `(du/I)`) til standardiseret `{{ PLACEHOLDER_NAVN }}` format klar til brug med `fill_document.py`. Manipulerer docx XML direkte — ingen Python-script nødvendigt.
Skill file: `.claude/skills/word-template-converter/SKILL.md`

### skills-creator — Build New Skills

6-step framework for creating new Claude Code skills from scratch.
Skill file: `.claude/skills/skills-creator/SKILL.md`

---

## Available Sub-Agents

Stored in `agents/` — use when delegating specialized tasks:

| File | Agent | Use for |
| --- | --- | --- |
| `Agents/agents-orchestrator.md` | Agents Orchestrator | Full autonomous dev pipeline: PM → Architect → Dev↔QA loop → integration |
| `Agents/engineering-ai-engineer.md` | AI Engineer | ML models, RAG architecture, LLM integration, embeddings, vector DBs |
| `Agents/engineering-backend-architect.md` | Backend Architect | Scalable system design, database architecture, API development |
| `Agents/engineering-senior-developer.md` | Senior Developer | Premium implementations, code quality, complex features |
| `Agents/engineering-devops-automator.md` | DevOps Automator | Infrastructure, CI/CD, cloud operations |
| `Agents/testing-reality-checker.md` | Reality Checker | Evidence-based QA, integration testing, production readiness |
