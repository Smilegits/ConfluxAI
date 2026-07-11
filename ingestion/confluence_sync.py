"""
Confluence Sync Manager - Manages incremental updates for Confluence pages.

Features:
- Tracks last sync timestamp per space
- Detects page modifications via content hashing
- Detects deletions (pages no longer in space)
- Provides sync statistics and status
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of changes detected during sync."""
    NEW = "new"
    MODIFIED = "modified"
    UNCHANGED = "unchanged"
    DELETED = "deleted"


@dataclass
class SyncResult:
    """Result of a sync operation."""
    space_key: str
    total_pages: int
    new_pages: int
    modified_pages: int
    unchanged_pages: int
    deleted_pages: int
    errors: int
    sync_time_seconds: float
    status: str  # "success", "partial", "failed"

    def __str__(self) -> str:
        return (
            f"Sync({self.space_key}): "
            f"new={self.new_pages}, modified={self.modified_pages}, "
            f"unchanged={self.unchanged_pages}, deleted={self.deleted_pages}, "
            f"errors={self.errors} [{self.status}]"
        )


class ConfluenceSyncManager:
    """
    Manages incremental sync state for Confluence spaces.

    Uses SQLite for tracking page metadata and sync state.
    """

    def __init__(self, tracking_db_path: str = "data/confluence_sync.db"):
        """
        Initialize sync manager.

        Args:
            tracking_db_path: Path to SQLite tracking database
        """
        self.db_path = tracking_db_path
        self.conn = sqlite3.connect(tracking_db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
        logger.info(f"Initialized Confluence sync manager with DB: {tracking_db_path}")

    def _init_schema(self):
        """Initialize database schema if not exists."""
        cursor = self.conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS confluence_pages (
                page_id TEXT PRIMARY KEY,
                space_key TEXT NOT NULL,
                title TEXT NOT NULL,
                last_modified TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                last_synced TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                chunks_count INTEGER DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS confluence_sync_state (
                space_key TEXT PRIMARY KEY,
                last_sync_time TEXT,
                total_pages INTEGER DEFAULT 0,
                last_sync_status TEXT,
                last_error TEXT
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_space_modified
            ON confluence_pages(space_key, last_modified)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status
            ON confluence_pages(status)
        ''')

        self.conn.commit()
        logger.debug("Database schema initialized")

    def get_sync_state(self, space_key: str) -> Optional[Dict]:
        """Get last sync state for a space."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT * FROM confluence_sync_state WHERE space_key = ?',
            (space_key,)
        )
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def update_sync_state(
        self,
        space_key: str,
        total_pages: int,
        status: str,
        error: Optional[str] = None
    ):
        """Update sync state for a space."""
        cursor = self.conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            '''
            INSERT OR REPLACE INTO confluence_sync_state
            (space_key, last_sync_time, total_pages, last_sync_status, last_error)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (space_key, now, total_pages, status, error)
        )
        self.conn.commit()
        logger.debug(f"Updated sync state for {space_key}: {status}")

    def get_last_modified_since(self, space_key: str) -> Optional[datetime]:
        """Get timestamp to use for incremental sync."""
        state = self.get_sync_state(space_key)

        if state and state.get('last_sync_time'):
            try:
                return datetime.fromisoformat(state['last_sync_time'])
            except ValueError:
                logger.warning(f"Invalid sync time for {space_key}, forcing full sync")
                return None

        return None

    def record_page(
        self,
        page_id: str,
        space_key: str,
        title: str,
        last_modified: str,
        content_hash: str,
        chunks_count: int = 0
    ):
        """Record a page in the tracking database."""
        cursor = self.conn.cursor()
        now = datetime.utcnow().isoformat()

        cursor.execute(
            '''
            INSERT OR REPLACE INTO confluence_pages
            (page_id, space_key, title, last_modified, content_hash, last_synced, status, chunks_count)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
            ''',
            (page_id, space_key, title, last_modified, content_hash, now, chunks_count)
        )
        self.conn.commit()

    def detect_changes(
        self,
        page_id: str,
        content_hash: str
    ) -> ChangeType:
        """Determine if a page needs re-ingestion."""
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT content_hash FROM confluence_pages WHERE page_id = ?',
            (page_id,)
        )
        row = cursor.fetchone()

        if row is None:
            return ChangeType.NEW

        if row['content_hash'] != content_hash:
            return ChangeType.MODIFIED

        return ChangeType.UNCHANGED

    def get_stats(self, space_key: Optional[str] = None) -> Dict:
        """Get statistics about tracked pages."""
        cursor = self.conn.cursor()

        if space_key:
            cursor.execute(
                '''
                SELECT status, COUNT(*) as count FROM confluence_pages
                WHERE space_key = ?
                GROUP BY status
                ''',
                (space_key,)
            )
        else:
            cursor.execute(
                '''
                SELECT status, COUNT(*) as count FROM confluence_pages
                GROUP BY status
                '''
            )

        rows = cursor.fetchall()
        stats = {'total': 0, 'active': 0, 'deleted': 0}

        for row in rows:
            status = row['status']
            count = row['count']
            stats[status] = count
            stats['total'] += count

        return stats

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Ensure connection is closed on deletion."""
        self.close()
