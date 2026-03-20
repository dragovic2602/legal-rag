"""
Document ingestion pipeline — orchestrates extraction, chunking, embedding, and DB persistence.
Smart incremental ingestion: skips unchanged files, removes deleted, re-ingests changed.
"""

import os
import asyncio
import logging
import json
import glob
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import argparse

from dotenv import load_dotenv

from indexing.chunker import ChunkingConfig, create_chunker, DocumentChunk
from indexing.embedder import create_embedder
from indexing.extraction import DocumentExtractor, extract_title, extract_document_metadata
from storage.db_utils import initialize_database, close_database, db_pool
from storage.models import IngestionConfig, IngestionResult

load_dotenv()
logger = logging.getLogger(__name__)


class DocumentIngestionPipeline:
    """Pipeline for ingesting documents into vector DB."""

    def __init__(
        self,
        config: IngestionConfig,
        documents_folder: str = "documents",
        clean_before_ingest: bool = False
    ):
        self.config = config
        self.documents_folder = documents_folder
        self.clean_before_ingest = clean_before_ingest

        self.chunker_config = ChunkingConfig(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            max_chunk_size=config.max_chunk_size,
            use_semantic_splitting=config.use_semantic_chunking
        )

        self.chunker = create_chunker(self.chunker_config)
        self.embedder = create_embedder()
        self.extractor = DocumentExtractor(
            cache_dir=config.cache_dir,
            skip_cache=config.skip_cache,
        )
        self._initialized = False

    async def initialize(self):
        """Initialise database connections."""
        if self._initialized:
            return
        logger.info("Initialising ingestion pipeline...")
        await initialize_database()
        self._initialized = True
        logger.info("Ingestion pipeline initialised")

    async def close(self):
        """Close database connections."""
        if self._initialized:
            await close_database()
            self._initialized = False

    async def ingest_documents(
        self,
        progress_callback: Optional[callable] = None
    ) -> List[IngestionResult]:
        """Ingest all documents from the documents folder (smart incremental)."""
        if not self._initialized:
            await self.initialize()

        if self.clean_before_ingest:
            await self._clean_databases()

        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT source, metadata->>'file_mtime' AS mtime FROM documents"
            )
        existing = {row['source']: row['mtime'] for row in rows}

        document_files = self._find_document_files()
        current_sources = {os.path.relpath(f, self.documents_folder) for f in document_files}

        for source in list(existing.keys()):
            if source not in current_sources:
                async with db_pool.acquire() as conn:
                    await conn.execute("DELETE FROM documents WHERE source = $1", source)
                logger.info(f"Removed deleted document: {source}")

        files_to_process = []
        for file_path in document_files:
            source = os.path.relpath(file_path, self.documents_folder)
            current_mtime = str(os.path.getmtime(file_path))
            if source in existing and existing[source] == current_mtime:
                logger.info(f"Skipping unchanged: {source}")
                continue
            if source in existing:
                async with db_pool.acquire() as conn:
                    await conn.execute("DELETE FROM documents WHERE source = $1", source)
            files_to_process.append(file_path)

        document_files = files_to_process

        if not document_files:
            logger.warning(f"No supported document files found in {self.documents_folder}")
            return []

        logger.info(f"Found {len(document_files)} document files to process")
        results = []

        for i, file_path in enumerate(document_files):
            try:
                logger.info(f"Processing file {i+1}/{len(document_files)}: {file_path}")
                result = await self._ingest_single_document(file_path)
                results.append(result)
                if progress_callback:
                    progress_callback(i + 1, len(document_files))
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append(IngestionResult(
                    document_id="",
                    title=os.path.basename(file_path),
                    chunks_created=0,
                    processing_time_ms=0,
                    errors=[str(e)]
                ))

        total_chunks = sum(r.chunks_created for r in results)
        total_errors = sum(len(r.errors) for r in results)
        logger.info(f"Ingestion complete: {len(results)} documents, {total_chunks} chunks, {total_errors} errors")
        return results

    async def _ingest_single_document(self, file_path: str) -> IngestionResult:
        """Ingest a single document."""
        start_time = datetime.now()

        document_content, docling_doc = self.extractor.read_document(file_path)
        document_title = extract_title(document_content, file_path)
        document_source = os.path.relpath(file_path, self.documents_folder)
        document_metadata = extract_document_metadata(document_content, file_path)

        logger.info(f"Processing document: {document_title}")

        chunks = await self.chunker.chunk_document(
            content=document_content,
            title=document_title,
            source=document_source,
            metadata=document_metadata,
            docling_doc=docling_doc
        )

        if not chunks:
            logger.warning(f"No chunks created for {document_title}")
            return IngestionResult(
                document_id="",
                title=document_title,
                chunks_created=0,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                errors=["No chunks created"]
            )

        logger.info(f"Created {len(chunks)} chunks")

        embedded_chunks = await self.embedder.embed_chunks(chunks)
        logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")

        document_id = await self._save_to_postgres(
            document_title,
            document_source,
            document_content,
            embedded_chunks,
            document_metadata
        )

        logger.info(f"Saved document to PostgreSQL with ID: {document_id}")

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return IngestionResult(
            document_id=document_id,
            title=document_title,
            chunks_created=len(chunks),
            processing_time_ms=processing_time,
            errors=[]
        )

    def _find_document_files(self) -> List[str]:
        """Find all supported document files in the documents folder."""
        if not os.path.exists(self.documents_folder):
            logger.error(f"Documents folder not found: {self.documents_folder}")
            return []

        patterns = [
            "*.md", "*.markdown", "*.txt",
            "*.pdf",
            "*.docx", "*.doc",
            "*.pptx", "*.ppt",
            "*.xlsx", "*.xls",
            "*.html", "*.htm",
            "*.mp3", "*.wav", "*.m4a", "*.flac",
        ]
        files = []
        for pattern in patterns:
            files.extend(glob.glob(os.path.join(self.documents_folder, "**", pattern), recursive=True))
        return sorted(files)

    async def _save_to_postgres(
        self,
        title: str,
        source: str,
        content: str,
        chunks: List[DocumentChunk],
        metadata: Dict[str, Any]
    ) -> str:
        """Save document and chunks to PostgreSQL."""
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                document_result = await conn.fetchrow(
                    """
                    INSERT INTO documents (title, source, content, metadata)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id::text
                    """,
                    title, source, content, json.dumps(metadata)
                )
                document_id = document_result["id"]

                for chunk in chunks:
                    embedding_data = None
                    if hasattr(chunk, 'embedding') and chunk.embedding:
                        embedding_data = '[' + ','.join(map(str, chunk.embedding)) + ']'

                    await conn.execute(
                        """
                        INSERT INTO chunks (document_id, content, embedding, chunk_index, metadata, token_count)
                        VALUES ($1::uuid, $2, $3::vector, $4, $5, $6)
                        """,
                        document_id, chunk.content, embedding_data,
                        chunk.index, json.dumps(chunk.metadata), chunk.token_count
                    )

                return document_id

    async def ingest_single_document(
        self, file_path: str, title: Optional[str] = None, source_label: Optional[str] = None
    ) -> IngestionResult:
        """
        Ingest one file without wiping the database.

        Deletes the existing document with a matching source value before
        re-inserting, so re-running on an updated file produces a clean result.
        """
        if not self._initialized:
            await self.initialize()

        if source_label is None:
            source_label = os.path.basename(file_path)

        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM documents WHERE source = $1", source_label)

        abs_path = os.path.abspath(file_path)
        original_folder = self.documents_folder
        self.documents_folder = os.path.dirname(abs_path) or "."
        try:
            result = await self._ingest_single_document(abs_path)
        finally:
            self.documents_folder = original_folder

        if title and result.document_id:
            async with db_pool.acquire() as conn:
                await conn.execute(
                    "UPDATE documents SET title = $1 WHERE id = $2::uuid",
                    title, result.document_id,
                )
            result = IngestionResult(
                document_id=result.document_id,
                title=title,
                chunks_created=result.chunks_created,
                processing_time_ms=result.processing_time_ms,
                errors=result.errors,
            )

        return result

    async def _clean_databases(self):
        """Wipe all chunks and documents (used with --force flag)."""
        logger.warning("Cleaning existing data from databases...")
        async with db_pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM chunks")
                await conn.execute("DELETE FROM documents")
        logger.info("Cleaned PostgreSQL database")


async def main():
    """Entry point for running ingestion from the command line."""
    parser = argparse.ArgumentParser(description="Ingest documents into vector DB")
    parser.add_argument("--documents", "-d", default="documents", help="Documents folder path")
    parser.add_argument("--force", action="store_true", help="Wipe all existing data before ingestion")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Chunk overlap")
    parser.add_argument("--no-semantic", action="store_true", help="Disable semantic chunking")
    parser.add_argument("--no-cache", action="store_true", help="Bypass extraction cache; always re-run Docling")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    print("Starting ingestion pipeline...", flush=True)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    config = IngestionConfig(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        use_semantic_chunking=not args.no_semantic,
        skip_cache=args.no_cache,
    )

    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=args.documents,
        clean_before_ingest=args.force
    )

    def progress_callback(current: int, total: int):
        print(f"Progress: {current}/{total} documents processed")

    try:
        start_time = datetime.now()
        results = await pipeline.ingest_documents(progress_callback)
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        print("\n" + "="*50)
        print("INGESTION SUMMARY")
        print("="*50)
        print(f"Documents processed: {len(results)}")
        print(f"Total chunks created: {sum(r.chunks_created for r in results)}")
        print(f"Total errors: {sum(len(r.errors) for r in results)}")
        print(f"Total processing time: {total_time:.2f} seconds")
        print()

        for result in results:
            status = "+" if not result.errors else "x"
            print(f"{status} {result.title}: {result.chunks_created} chunks")
            for error in result.errors:
                print(f"  Error: {error}")

    except KeyboardInterrupt:
        print("\nIngestion interrupted by user")
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise
    finally:
        await pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())
