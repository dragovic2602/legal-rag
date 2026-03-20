"""
Local file watcher service.
Watches a local folder and triggers smart incremental ingestion on any change.

Setup: Local (no cloud auth needed)
For OneDrive Business sync, use sync_service.py instead.
"""

import asyncio
import logging
import os
import signal

from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

WATCH_FOLDER = os.getenv("WATCH_FOLDER", "documents")
DEBOUNCE_SECONDS = float(os.getenv("WATCH_DEBOUNCE_SECONDS", "3"))


class _ChangeHandler(FileSystemEventHandler):
    """Bridges watchdog thread events into the asyncio event loop."""

    def __init__(self, loop: asyncio.AbstractEventLoop, trigger: asyncio.Event):
        self._loop = loop
        self._trigger = trigger

    def on_any_event(self, event):
        if event.is_directory:
            return
        logger.debug(f"File event: {event.event_type} {event.src_path}")
        self._loop.call_soon_threadsafe(self._trigger.set)


async def main():
    from storage.db_utils import initialize_database, close_database, db_pool
    from indexing.pipeline import DocumentIngestionPipeline
    from storage.models import IngestionConfig

    logger.info(f"Initialising database connection pool...")
    await initialize_database()
    logger.info(f"Watching folder: {os.path.abspath(WATCH_FOLDER)}")

    config = IngestionConfig()
    pipeline = DocumentIngestionPipeline(
        config=config,
        documents_folder=WATCH_FOLDER,
        clean_before_ingest=False,
    )
    await pipeline.initialize()

    loop = asyncio.get_running_loop()
    trigger = asyncio.Event()
    shutdown_event = asyncio.Event()

    def _handle_signal(*_):
        logger.info("Shutdown signal received")
        shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _handle_signal)
        except (NotImplementedError, OSError):
            signal.signal(sig, _handle_signal)

    handler = _ChangeHandler(loop, trigger)
    observer = Observer()
    observer.schedule(handler, path=WATCH_FOLDER, recursive=True)
    observer.start()
    logger.info("File watcher started — waiting for changes...")

    # Run initial sync on startup so DB is up to date
    await pipeline.ingest_documents()

    try:
        while not shutdown_event.is_set():
            # Block until a file event fires or shutdown
            done, _ = await asyncio.wait(
                [
                    asyncio.create_task(trigger.wait()),
                    asyncio.create_task(shutdown_event.wait()),
                ],
                return_when=asyncio.FIRST_COMPLETED,
            )
            if shutdown_event.is_set():
                break

            # Debounce: wait for rapid follow-up events to settle
            trigger.clear()
            await asyncio.sleep(DEBOUNCE_SECONDS)
            trigger.clear()

            logger.info("Change detected — running ingestion...")
            try:
                await pipeline.ingest_documents()
            except Exception as e:
                logger.error(f"Ingestion failed: {e}", exc_info=True)
    finally:
        observer.stop()
        observer.join()
        await close_database()
        logger.info("Watch service stopped")


if __name__ == "__main__":
    asyncio.run(main())
