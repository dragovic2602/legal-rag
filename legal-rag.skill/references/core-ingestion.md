# Core Ingestion — How Documents Enter the System

Use this reference when the user reports missing documents, asks why a document isn't searchable, or wants to add/update files.

---

## Supported Document Formats

| Format | Extractor |
|--------|-----------|
| PDF | Docling (primary) → PyMuPDF + RapidOCR fallback (scanned pages) |
| DOCX, PPTX, XLSX | Docling |
| HTML | Docling |
| MP3, WAV, M4A, FLAC | Docling Whisper ASR (audio transcription) |
| Any other format | Stub record — file indexed by name, `extraction_failed: true` in metadata |

---

## Extraction Chain

```
File on disk
  ↓
1. Docling DocumentConverter
   → Returns DoclingDocument (rich structure, heading hierarchy, tables)
   → Used by DoclingHybridChunker for semantically-aware chunking

2. If Docling fails → PyMuPDF
   → Page-by-page text extraction
   → RapidOCR for scanned/image pages

3. If both fail → Stub record
   → Document stored with title = filename, content = empty
   → metadata.extraction_failed = true
   → Still searchable by filename via full-text index
```

---

## Docling Parse Cache

First-time parsing a large PDF (e.g. a 300-page law compendium) takes **3–5 minutes**.

Subsequent re-ingests are **instant** because the `DoclingDocument` is cached to disk:
- Cache directory: `indexing_cache/` (in project root, excluded from git)
- Cache key: `file_mtime` (modification timestamp) — cache is automatically invalidated when the file changes
- Cache format: JSON (DoclingDocument serialised via Pydantic `.model_dump()`)

**When cache helps**: re-running ingestion after a failed embedding, re-indexing after schema changes, adding more chunks from an already-parsed document.

**When cache is bypassed**: use `--no-cache` flag or when `file_mtime` changes (file was modified).

---

## Change Detection

The ingestion pipeline compares the current `file_mtime` against what's stored in `documents.metadata` (JSONB):

| Situation | Action |
|-----------|--------|
| File unchanged (`mtime` matches) | Skipped — no re-ingestion |
| File modified (`mtime` differs) | Old document + chunks deleted, re-ingested |
| File deleted from disk | `DELETE FROM documents WHERE source = $1` |
| New file | Ingested fresh |

The `source` column = `os.path.relpath(file_path, documents_folder)` — unique key per document (e.g. `Tinglysningsloven.pdf`).

---

## Ingestion Commands

All commands use the project venv (Windows):

```bash
# Smart incremental — skips unchanged, removes deleted, re-ingests changed
.venv/Scripts/python -m indexing.pipeline

# Force full wipe + re-ingest everything (ignores cache)
.venv/Scripts/python -m indexing.pipeline --force

# Disable DoclingHybridChunker — uses SimpleChunker (faster startup, lower quality)
.venv/Scripts/python -m indexing.pipeline --no-semantic

# Skip Docling parse cache — always re-parse with Docling
.venv/Scripts/python -m indexing.pipeline --no-cache

# Combine flags
.venv/Scripts/python -m indexing.pipeline --force --no-cache

# File watcher — auto-ingests when any file in documents/ changes
.venv/Scripts/python watch_service.py
```

---

## Chunking

- **Primary**: `DoclingHybridChunker` — requires a `DoclingDocument` (Docling output). Max 512 tokens per chunk, chunks include heading hierarchy for context. Uses `sentence-transformers/all-MiniLM-L6-v2` tokenizer.
- **Fallback**: `SimpleChunker` — paragraph-based sliding window. Used when `--no-semantic` is passed or when Docling fails.

---

## Where to Put Documents

Place files in the `documents/` folder. The ingestion pipeline watches this folder (or scan it on demand). Subfolders are supported; `source` will include the relative path (e.g. `subfolder/Tinglysningsloven.pdf`).

OneDrive sync (Phase 2) will auto-download files to `documents/` and trigger ingestion.
