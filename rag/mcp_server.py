"""
Legal RAG MCP Server — exposes the knowledge base to Claude Code as native tools.

Tools:
  search_knowledge_base(query, limit, source_filter) — hybrid vector + full-text search
  list_documents()                                   — list all ingested documents

Claude Code auto-starts this server via .mcp.json (stdio transport).
"""

import logging
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

logging.basicConfig(level=logging.WARNING)

mcp = FastMCP("legal-rag")

# ─── DB initialisation (done once on first tool call) ────────────────────────

_db_ready = False


async def _ensure_db():
    global _db_ready
    if not _db_ready:
        from storage.db_utils import initialize_database
        await initialize_database()
        _db_ready = True


# ─── Tools ───────────────────────────────────────────────────────────────────


@mcp.tool()
async def search_knowledge_base(
    query: str,
    limit: int = 5,
    source_filter: Optional[str] = None,
) -> str:
    """Search the legal knowledge base using hybrid vector + full-text search.

    Returns the most relevant chunks with neighboring chunks (±1) for context,
    so legal paragraphs are never cut off mid-section.
    Call list_documents first to see available sources you can filter by.

    Args:
        query: Search query in natural language.
        limit: Number of results to return (1–10). Default 5.
        source_filter: Optional document filename to restrict search to a specific
            law or document, e.g. 'Tinglysningsloven.pdf' or 'Lov om leje.pdf'.
            Partial matches work (case-insensitive).
    """
    await _ensure_db()

    limit = max(1, min(int(limit), 10))
    candidates = limit * 3

    from indexing.embedder import create_embedder
    from storage.db_utils import db_pool

    embedder = create_embedder()
    query_embedding = await embedder.embed_query(query)
    embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT chunk_id, document_id, content, similarity, document_title, document_source"
            " FROM match_chunks_hybrid($1::vector, $2, $3)",
            embedding_str,
            query,
            candidates,
        )

    # Diversity reranking: -0.1 penalty per extra chunk from same document
    seen_docs: dict[str, float] = {}
    reranked: list[tuple[dict, float]] = []
    for row in rows:
        doc_id = str(row["document_id"])
        penalty = seen_docs.get(doc_id, 0.0)
        seen_docs[doc_id] = penalty + 0.1
        reranked.append((dict(row), float(row["similarity"]) - penalty))
    reranked.sort(key=lambda x: x[1], reverse=True)

    if source_filter:
        reranked = [
            (r, s) for r, s in reranked
            if source_filter.lower() in r.get("document_source", "").lower()
        ]

    top = reranked[:limit]

    if not top:
        if source_filter:
            return f"No results found for '{query}' in documents matching '{source_filter}'."
        return "No relevant results found in the knowledge base."

    # ── Fetch chunk_index + neighbors for each top result ─────────────────────
    async with db_pool.acquire() as conn:
        # Get chunk_index for all top chunks in one query
        top_ids = [r["chunk_id"] for r, _ in top]
        index_rows = await conn.fetch(
            "SELECT id, chunk_index FROM chunks WHERE id = ANY($1)",
            top_ids,
        )
    index_by_id = {str(r["id"]): r["chunk_index"] for r in index_rows}

    # Fetch neighbors: for each top chunk, get chunk_index ±1 from same document
    async with db_pool.acquire() as conn:
        neighbor_rows = await conn.fetch(
            """
            SELECT c.id::text AS chunk_id, c.document_id::text, c.chunk_index, c.content
            FROM chunks c
            WHERE (c.document_id::text, c.chunk_index) IN (
                SELECT vals.doc_id, vals.idx
                FROM unnest($1::text[], $2::int[]) AS vals(doc_id, idx)
            )
            AND c.id != ALL($3)
            """,
            # doc_ids repeated for ±1
            [str(r["document_id"]) for r, _ in top for _ in range(2)],
            # ±1 indexes
            [
                index_by_id.get(str(r["chunk_id"]), -999) + delta
                for r, _ in top
                for delta in (-1, 1)
            ],
            top_ids,
        )

    # Group neighbors by document_id + chunk_index for quick lookup
    neighbors_by_doc_idx: dict[tuple, str] = {}
    for n in neighbor_rows:
        neighbors_by_doc_idx[(n["document_id"], n["chunk_index"])] = n["content"]

    # ── Format output ──────────────────────────────────────────────────────────
    parts = []
    for row, score in top:
        title  = row.get("document_title", "Unknown")
        source = row.get("document_source", "")
        content = row.get("content", "")
        chunk_id = str(row["chunk_id"])
        doc_id   = str(row["document_id"])
        idx = index_by_id.get(chunk_id)

        block = f"[Kilde: {title} | {source} | relevans: {score:.4f}]\n"

        if idx is not None:
            before = neighbors_by_doc_idx.get((doc_id, idx - 1))
            after  = neighbors_by_doc_idx.get((doc_id, idx + 1))
            if before:
                block += f"[kontekst før §]\n{before}\n\n"
            block += f"[RELEVANT AFSNIT]\n{content}"
            if after:
                block += f"\n\n[kontekst efter §]\n{after}"
        else:
            block += content

        parts.append(block)

    warning = ""
    if len(parts) < 3:
        warning = (
            f"\n⚠️ Kun {len(parts)} resultat(er) fundet — "
            "KB-dækning kan være lav for dette spørgsmål. Verificer manuelt.\n"
        )

    return (
        f"Fandt {len(parts)} relevante resultater (inkl. nabochunks til kontekst):{warning}\n\n"
        + "\n---\n".join(parts)
    )


@mcp.tool()
async def list_documents() -> str:
    """List all documents currently in the legal knowledge base.

    Returns document titles and their source filenames. Use source filenames
    to filter searches with the source_filter parameter in search_knowledge_base.
    """
    await _ensure_db()

    from storage.db_utils import db_pool

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT title, source FROM documents ORDER BY title"
        )

    if not rows:
        return "The knowledge base is empty. Run the ingestion pipeline to add documents."

    lines = [f"- {r['title']}  →  {r['source']}" for r in rows]
    return f"{len(rows)} documents in knowledge base:\n\n" + "\n".join(lines)


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="stdio")
