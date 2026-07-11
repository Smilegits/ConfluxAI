"""
Confluence Sync Scheduler - Manages periodic sync jobs for near-real-time updates.

Features:
- Background scheduler (APScheduler)
- Near-real-time polling (every 5 minutes)
- Delta sync only (fetch pages modified since last run)
- Non-blocking (runs in background thread)
"""

import logging
from typing import List, Optional, Callable
from datetime import datetime
from threading import Lock

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler not installed. Install with: pip install apscheduler")
    BackgroundScheduler = None
    IntervalTrigger = None

from ingestion.confluence_loader import ConfluenceLoader
from ingestion.confluence_sync import ConfluenceSyncManager, SyncResult

logger = logging.getLogger(__name__)


class SyncScheduler:
    """
    Manages periodic sync jobs for Confluence spaces.

    Runs in background thread, syncs all configured spaces at regular interval.
    """

    def __init__(
        self,
        spaces: List[str],
        interval_minutes: int = 5,
        on_sync_complete: Optional[Callable[[SyncResult], None]] = None
    ):
        """
        Initialize scheduler.

        Args:
            spaces: List of space keys to sync
            interval_minutes: Minutes between sync runs (default 5)
            on_sync_complete: Optional callback function after each sync
        """
        if BackgroundScheduler is None:
            raise RuntimeError("APScheduler not installed. Run: pip install apscheduler")

        self.spaces = spaces
        self.interval_minutes = interval_minutes
        self.on_sync_complete = on_sync_complete
        self.scheduler: Optional[BackgroundScheduler] = None
        self.sync_manager = ConfluenceSyncManager()
        self.loader = ConfluenceLoader(spaces=spaces)
        self._lock = Lock()
        self._is_running = False
        self._last_sync_results: dict = {}

        logger.info(
            f"Initialized SyncScheduler: spaces={spaces}, "
            f"interval={interval_minutes}m"
        )

    def start(self):
        """Start scheduled sync jobs."""
        with self._lock:
            if self._is_running:
                logger.warning("Scheduler already running")
                return

            try:
                self.scheduler = BackgroundScheduler(daemon=True)

                # Add job for each space
                for space_key in self.spaces:
                    job_id = f'confluence_sync_{space_key}'

                    self.scheduler.add_job(
                        func=self._sync_space_job,
                        args=[space_key],
                        trigger=IntervalTrigger(minutes=self.interval_minutes),
                        id=job_id,
                        replace_existing=True,
                        max_instances=1,
                        name=f"Confluence sync: {space_key}"
                    )
                    logger.debug(f"Added job for space: {space_key}")

                self.scheduler.start()
                self._is_running = True

                logger.info(
                    f"Started Confluence sync scheduler "
                    f"[spaces={self.spaces}, interval={self.interval_minutes}m]"
                )

            except Exception as e:
                logger.error(f"Failed to start scheduler: {e}")
                raise

    def stop(self):
        """Stop scheduled sync jobs gracefully."""
        with self._lock:
            if not self._is_running or not self.scheduler:
                return

            try:
                self.scheduler.shutdown(wait=True)
                self._is_running = False
                logger.info("Stopped Confluence sync scheduler")
            except Exception as e:
                logger.error(f"Error stopping scheduler: {e}")

    def _sync_space_job(self, space_key: str):
        """Job that runs at regular interval for each space."""
        logger.debug(f"Starting sync job for space: {space_key}")

        try:
            modified_since = self.sync_manager.get_last_modified_since(space_key)

            if modified_since:
                logger.info(f"Delta sync for {space_key} since {modified_since}")
            else:
                logger.info(f"Full sync for {space_key} (no previous sync)")

            start_time = datetime.utcnow()
            raw_docs = self.loader.load_space(space_key, modified_since=modified_since)

            if not raw_docs:
                logger.info(f"No changes in space {space_key}")
                self.sync_manager.update_sync_state(
                    space_key=space_key,
                    total_pages=0,
                    status='success'
                )
                return

            new_count = 0
            modified_count = 0
            unchanged_count = 0

            for doc in raw_docs:
                page_id = doc.metadata.get('page_id')
                content_hash = doc.metadata.get('source_hash')

                if not page_id or not content_hash:
                    continue

                change_type = self.sync_manager.detect_changes(page_id, content_hash)

                if change_type.value == 'new':
                    new_count += 1
                elif change_type.value == 'modified':
                    modified_count += 1
                else:
                    unchanged_count += 1

            sync_time = (datetime.utcnow() - start_time).total_seconds()

            result = SyncResult(
                space_key=space_key,
                total_pages=len(raw_docs),
                new_pages=new_count,
                modified_pages=modified_count,
                unchanged_pages=unchanged_count,
                deleted_pages=0,
                errors=0,
                sync_time_seconds=sync_time,
                status='success' if new_count + modified_count > 0 else 'partial'
            )

            for doc in raw_docs:
                self.sync_manager.record_page(
                    page_id=doc.metadata.get('page_id'),
                    space_key=space_key,
                    title=doc.metadata.get('title'),
                    last_modified=doc.metadata.get('last_modified'),
                    content_hash=doc.metadata.get('source_hash')
                )

            self.sync_manager.update_sync_state(
                space_key=space_key,
                total_pages=len(raw_docs),
                status=result.status
            )

            self._last_sync_results[space_key] = result

            logger.info(f"Sync job complete: {result}")

            if self.on_sync_complete:
                try:
                    self.on_sync_complete(result)
                except Exception as e:
                    logger.error(f"Error in sync callback: {e}")

        except Exception as e:
            logger.error(f"Sync job failed for {space_key}: {e}", exc_info=True)

            self.sync_manager.update_sync_state(
                space_key=space_key,
                total_pages=0,
                status='failed',
                error=str(e)
            )

    def is_running(self) -> bool:
        """Check if scheduler is running."""
        return self._is_running

    def __del__(self):
        """Ensure scheduler is stopped on deletion."""
        self.stop()
