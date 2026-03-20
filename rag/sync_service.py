"""
OneDrive → Supabase sync service entry point.

Runs an initial sync on startup, then repeats every 15 minutes.
Handles SIGTERM and KeyboardInterrupt gracefully.
"""

import asyncio
import logging
import os
import signal
import sys

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

SYNC_INTERVAL_SECONDS = 15 * 60  # 15 minutes


async def main():
    from storage.db_utils import initialize_database, close_database, db_pool
    from onedrive.sync import OneDriveSyncService

    logger.info("Initialising database connection pool...")
    await initialize_database()
    logger.info("Database pool ready")

    sync_service = OneDriveSyncService(db_pool=db_pool)

    shutdown_event = asyncio.Event()

    def _handle_signal(*_):
        logger.info("Shutdown signal received — stopping after current cycle")
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, OSError):
            # Windows does not support add_signal_handler for all signals
            signal.signal(sig, _handle_signal)

    try:
        while not shutdown_event.is_set():
            try:
                await sync_service.run_sync()
            except Exception as e:
                logger.error(f"Sync cycle failed: {e}", exc_info=True)

            logger.info(f"Next sync in {SYNC_INTERVAL_SECONDS // 60} minutes")
            try:
                await asyncio.wait_for(
                    shutdown_event.wait(), timeout=SYNC_INTERVAL_SECONDS
                )
            except asyncio.TimeoutError:
                pass  # Normal — time to run the next cycle
    finally:
        logger.info("Closing database connection pool...")
        await close_database()
        logger.info("Sync service stopped")


if __name__ == "__main__":
    asyncio.run(main())
