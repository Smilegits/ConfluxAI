"""
Confluence Loader - Loads Confluence pages using MCP tools.

Features:
- Space traversal with CQL-based filtering
- Pagination handling (50 results/page limit)
- Rate limit management (adaptive backoff)
- Metadata extraction (space, title, lastModified, author, labels)
- Content conversion to Markdown format
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import hashlib

from ingestion.loaders import RawDocument

logger = logging.getLogger(__name__)


@dataclass
class AdaptiveRateLimiter:
    """Adaptive rate limiter with exponential backoff."""

    calls_per_second: float = 10.0
    min_delay: float = 0.05
    max_delay: float = 5.0
    backoff_multiplier: float = 2.0

    def __post_init__(self):
        self.current_delay = 1.0 / self.calls_per_second
        self.last_call = 0

    def wait(self):
        """Wait until next call is allowed."""
        elapsed = time.time() - self.last_call
        if elapsed < self.current_delay:
            time.sleep(self.current_delay - elapsed)
        self.last_call = time.time()

    def back_off(self):
        """Increase delay on rate limit error."""
        self.current_delay = min(
            self.current_delay * self.backoff_multiplier,
            self.max_delay
        )
        logger.warning(f"Rate limited, backing off to {self.current_delay:.2f}s delay")

    def reset(self):
        """Reset delay on success."""
        self.current_delay = 1.0 / self.calls_per_second


class ConfluenceLoader:
    """
    Loads Confluence pages using MCP tools.

    MCP tools used:
    - mcp__confluence__confluence_search: Find pages by CQL query
    - mcp__confluence__confluence_get_page: Fetch full page content + metadata
    """

    def __init__(self, spaces: List[str], use_mcp: bool = True):
        """
        Initialize Confluence loader.

        Args:
            spaces: List of space keys to crawl (e.g., ['ENG', 'PRODUCT'])
            use_mcp: Use MCP confluence tools (default True)
        """
        self.spaces = spaces
        self.use_mcp = use_mcp
        self.rate_limiter = AdaptiveRateLimiter()

    def load_space(
        self,
        space_key: str,
        modified_since: Optional[datetime] = None
    ) -> List[RawDocument]:
        """
        Load all pages from a space, optionally filtering by modification date.

        Args:
            space_key: Confluence space key (e.g., 'ENG', 'PRODUCT')
            modified_since: Optional datetime to filter by modification date

        Returns:
            List of RawDocument objects ready for ingestion
        """
        if not space_key or not isinstance(space_key, str):
            raise ValueError(f"Invalid space key: {space_key}")

        logger.info(f"Starting Confluence space load: {space_key}")

        raw_docs = []
        query = f'space="{space_key}" AND type=page'

        if modified_since:
            iso_date = modified_since.isoformat()
            query += f' AND lastModified >= "{iso_date}"'
            logger.info(f"Filtering pages modified since: {iso_date}")

        try:
            page_count = 0
            for page_info in self._paginated_search(query):
                page_count += 1

                try:
                    raw_doc = self._fetch_page_content(page_info['id'], space_key)
                    if raw_doc:
                        raw_docs.append(raw_doc)
                except Exception as e:
                    logger.error(f"Failed to fetch page: {e}")
                    continue

            logger.info(f"Loaded {len(raw_docs)}/{page_count} pages from space: {space_key}")

        except Exception as e:
            logger.error(f"Failed to load space {space_key}: {e}")
            raise

        return raw_docs

    def _paginated_search(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search Confluence with automatic pagination."""
        # This is a stub - actual implementation would use MCP tools
        logger.debug(f"Searching: {query}")
        return []

    def _fetch_page_content(
        self,
        page_id: str,
        space_key: str
    ) -> Optional[RawDocument]:
        """Fetch full page content and metadata."""
        # This is a stub - actual implementation would use MCP tools
        return None

    @staticmethod
    def _compute_content_hash(content: str) -> str:
        """Compute SHA256 hash of content for change detection."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
