"""
OneDrive sync orchestrator.

Detects new/changed/deleted files via the Graph delta API and
incrementally updates Supabase (documents + chunks + synced_files).
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .client import OneDriveClient

load_dotenv()

logger = logging.getLogger(__name__)


class OneDriveSyncService:
    """Orchestrates incremental OneDrive → Supabase sync."""

    def __init__(self, db_pool):
        """
        Args:
            db_pool: asyncpg connection pool (already initialised).
        """
        self.db_pool = db_pool
        self.client = OneDriveClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_sync(self):
        """Run one full sync cycle (delta check → ingest / delete)."""
        logger.info("Starting OneDrive sync cycle...")

        delta_link = await self._load_delta_link()
        changes, new_delta_link = await self.client.get_delta(delta_link)

        logger.info(f"Delta returned {len(changes)} item(s)")

        ingested = deleted = skipped = 0

        for item in changes:
            item_id = item.get("id")
            name = item.get("name", "")

            # Deleted items carry a 'deleted' key
            if "deleted" in item:
                await self._delete_file(item_id)
                deleted += 1
                continue

            # Skip folders and unsupported file types
            if "folder" in item:
                continue
            if not self.client.is_supported(name):
                logger.debug(f"Skipping unsupported file: {name}")
                skipped += 1
                continue

            etag = item.get("eTag", "")
            onedrive_path = item.get("parentReference", {}).get("path", "") + "/" + name

            # Skip if etag unchanged (belt-and-suspenders — delta should only
            # return changed items, but Guard against re-delivery)
            if await self._is_unchanged(item_id, etag):
                skipped += 1
                continue

            local_path = None
            try:
                local_path = await self.client.download_file(item_id, name)
                doc_id = await self._ingest_file(item_id, name, local_path)
                await self._upsert_synced_file(item_id, doc_id, name, etag, onedrive_path)
                ingested += 1
            except Exception as e:
                logger.error(f"Failed to sync {name} ({item_id}): {e}")
            finally:
                if local_path:
                    _cleanup_temp(local_path)

        await self._save_delta_link(new_delta_link)

        logger.info(
            f"Sync cycle complete — ingested: {ingested}, deleted: {deleted}, skipped: {skipped}"
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ingest_file(self, item_id: str, item_name: str, local_path: str) -> str:
        """Ingest a single file and return the new document_id."""
        # Import here to avoid circular imports at module load time
        from indexing.pipeline import DocumentIngestionPipeline
        from storage.models import IngestionConfig

        config = IngestionConfig()
        # clean_before_ingest=False so we never wipe the whole DB;
        # ingest_single_document deletes only the matching source row.
        pipeline = DocumentIngestionPipeline(config=config, clean_before_ingest=False)
        pipeline._initialized = True  # db pool already initialised by sync_service.py

        # source_label = item_name so the per-document dedupe key is stable
        result = await pipeline.ingest_single_document(
            file_path=local_path,
            source_label=item_name,
        )
        if result.errors:
            raise RuntimeError(f"Ingestion errors: {result.errors}")
        return result.document_id

    async def _delete_file(self, item_id: str):
        """Remove a document (and its chunks) from Supabase by OneDrive item ID."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT document_id FROM synced_files WHERE onedrive_item_id = $1",
                item_id,
            )
            if not row or not row["document_id"]:
                # Nothing tracked — nothing to delete
                logger.debug(f"No tracked document for item_id={item_id}, skipping delete")
                await conn.execute(
                    "DELETE FROM synced_files WHERE onedrive_item_id = $1", item_id
                )
                return

            doc_id = row["document_id"]
            # chunks are deleted via ON DELETE CASCADE on documents
            await conn.execute("DELETE FROM documents WHERE id = $1", doc_id)
            await conn.execute(
                "DELETE FROM synced_files WHERE onedrive_item_id = $1", item_id
            )
            logger.info(f"Deleted document {doc_id} for OneDrive item {item_id}")

    async def _upsert_synced_file(
        self, item_id: str, doc_id: str, filename: str, etag: str, path: str
    ):
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO synced_files (onedrive_item_id, document_id, filename, etag, onedrive_path)
                VALUES ($1, $2::uuid, $3, $4, $5)
                ON CONFLICT (onedrive_item_id) DO UPDATE SET
                    document_id   = EXCLUDED.document_id,
                    filename      = EXCLUDED.filename,
                    etag          = EXCLUDED.etag,
                    onedrive_path = EXCLUDED.onedrive_path,
                    last_synced_at = CURRENT_TIMESTAMP
                """,
                item_id,
                doc_id,
                filename,
                etag,
                path,
            )

    async def _is_unchanged(self, item_id: str, etag: str) -> bool:
        """Return True if the item's etag matches what we last synced."""
        if not etag:
            return False
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT etag FROM synced_files WHERE onedrive_item_id = $1", item_id
            )
        return row is not None and row["etag"] == etag

    async def _load_delta_link(self) -> Optional[str]:
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT value FROM sync_state WHERE key = 'delta_link'"
            )
        return row["value"] if row else None

    async def _save_delta_link(self, delta_link: Optional[str]):
        if not delta_link:
            return
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sync_state (key, value)
                VALUES ('delta_link', $1)
                ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
                """,
                delta_link,
            )


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _cleanup_temp(local_path: str):
    """Delete the temporary directory created for the downloaded file."""
    try:
        tmp_dir = os.path.dirname(local_path)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"Could not clean up temp dir for {local_path}: {e}")
