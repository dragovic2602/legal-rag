# Commands

## Setup

```bash
cd "C:\Users\nikol\OneDrive\Skrivebord\AI\Github\Docling RAG Agent"
```

## Ingestion

| Command | What it does |
|---|---|
| `.venv/Scripts/python -m ingestion.ingest` | Normal run — skips unchanged, removes deleted, ingests new/changed |
| `.venv/Scripts/python -m ingestion.ingest --force` | Wipes DB and re-ingests everything from scratch |
| `.venv/Scripts/python -m ingestion.ingest --verbose` | Normal run with detailed debug logging |
| `.venv/Scripts/python -m ingestion.ingest --documents <path>` | Run against a different documents folder |
| `.venv/Scripts/python -m ingestion.ingest --chunk-size 500 --chunk-overlap 100` | Override chunking settings |

## Query

```bash
.venv/Scripts/python -m cli
```

## Watch Service (Local)

```bash
# Run locally (watches documents/ folder, triggers ingestion on changes)
.venv/Scripts/python watch_service.py

# Run in Docker (keeps running in background)
docker-compose up -d watch-service
```
