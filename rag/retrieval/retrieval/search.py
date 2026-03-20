"""
Retrieval — hybrid search with diversity reranking.

Single canonical implementation shared by the CLI agent and FastAPI agent.
Uses storage.db_utils for the connection pool and indexing.embedder for query embeddings.
"""

import logging
from pydantic_ai import RunContext
from storage.db_utils import db_pool

logger = logging.getLogger(__name__)


async def search_knowledge_base(ctx: RunContext[None], query: str, limit: int = 5) -> str:
    """
    Search the knowledge base using hybrid semantic + full-text search with diversity reranking.

    Args:
        query: The search query to find relevant information
        limit: Maximum number of results to return (default: 5)

    Returns:
        Formatted search results with source citations
    """
    try:
        from indexing.embedder import create_embedder
        embedder = create_embedder()
        query_embedding = await embedder.embed_query(query)

        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        candidates = limit * 3

        async with db_pool.acquire() as conn:
            results = await conn.fetch(
                "SELECT * FROM match_chunks_hybrid($1::vector, $2, $3)",
                embedding_str, query, candidates,
            )

        # Rerank: apply -0.1 diversity penalty per additional chunk from the same document
        seen_docs: dict = {}
        reranked = []
        for row in results:
            doc_id = str(row["document_id"])
            base_score = float(row["similarity"])
            penalty = 0.1 * seen_docs.get(doc_id, 0)
            seen_docs[doc_id] = seen_docs.get(doc_id, 0) + 1
            reranked.append((base_score - penalty, row))

        reranked.sort(key=lambda x: x[0], reverse=True)
        results = [row for _, row in reranked[:limit]]

        if not results:
            return "No relevant information found in the knowledge base for your query."

        response_parts = [
            f"[Source: {row['document_title']}]\n{row['content']}\n" for row in results
        ]
        return f"Found {len(response_parts)} relevant results:\n\n" + "\n---\n".join(response_parts)

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}", exc_info=True)
        return f"I encountered an error searching the knowledge base: {str(e)}"
