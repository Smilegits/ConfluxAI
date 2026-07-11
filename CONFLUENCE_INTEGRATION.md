# Confluence RAG Integration - POC Implementation

This document describes the Confluence integration for the RAG chatbot, implemented as Phase 1 of the billion-scale architecture plan.

## Overview

The system now supports ingesting Confluence pages as a data source alongside URLs, PDFs, and other documents. Features include:

- **Auto-sync**: Pages are automatically synced every 5 minutes (configurable)
- **Delta sync**: Only new/modified pages are re-ingested (change detection via content hashing)
- **Incremental updates**: Near real-time reflection of Confluence changes in RAG
- **Tracking database**: SQLite tracks page metadata and sync state
- **Rate limiting**: Adaptive backoff prevents API throttling
- **CLI commands**: Manual sync, status checking, and admin utilities

## Architecture

```
Confluence API
    ↓
ConfluenceLoader (MCP tools) → RawDocument objects
    ↓
ConfluenceSyncManager (SQLite) → Change detection
    ↓
IngestionPipeline → Chunking → Embedding → ChromaDB
    ↓
Retrieval Engine (Hybrid search + reranking)
```

## Configuration

### Environment Variables

Add these to your `.env` file:

```bash
# Enable/disable Confluence integration
CONFLUENCE_ENABLED=true

# Comma-separated space keys to sync
CONFLUENCE_SPACES=ENG,PRODUCT,DOCS

# Sync interval (minutes between sync runs)
CONFLUENCE_SYNC_INTERVAL=5

# SQLite tracking database path
CONFLUENCE_TRACKING_DB=data/confluence_sync.db

# API rate limiting (calls per second)
CONFLUENCE_RATE_LIMIT=10
```

## Usage

### Command-Line Interface

```bash
# Delta sync (only fetch new/modified pages)
python cli.py sync --space ENG

# Full sync (re-fetch and detect all changes)
python cli.py sync --space ENG --full

# Sync and ingest into RAG
python cli.py sync --space ENG --ingest

# Check sync status
python cli.py status --space ENG

# List all configured spaces
python cli.py list-spaces

# Show statistics
python cli.py stats

# Show space statistics
python cli.py stats --space ENG
```

### Programmatic Usage

```python
from ingestion.confluence_loader import ConfluenceLoader
from ingestion.confluence_sync import ConfluenceSyncManager
from ingestion.pipeline import IngestionPipeline

# Load pages from Confluence
loader = ConfluenceLoader(spaces=['ENG', 'PRODUCT'])
raw_docs = loader.load_space('ENG')

# Detect changes
sync_manager = ConfluenceSyncManager()
for doc in raw_docs:
    change_type = sync_manager.detect_changes(
        doc.metadata['page_id'],
        doc.metadata['source_hash']
    )
    print(f"Page {doc.metadata['title']}: {change_type}")

# Ingest into RAG
pipeline = IngestionPipeline()
results = pipeline.ingest_confluence_pages(raw_docs)
print(f"Processed: {results['processed']}, Chunks created: {results['chunks_created']}")
```

## Components

### 1. ConfluenceLoader (`ingestion/confluence_loader.py`)

Loads Confluence pages using MCP tools with:
- CQL-based search with pagination (50 results/call)
- Automatic rate limiting with exponential backoff
- Metadata extraction (space, title, author, labels, etc.)
- Content conversion to Markdown
- Content hashing for change detection

### 2. ConfluenceSyncManager (`ingestion/confluence_sync.py`)

Tracks sync state and detects changes using SQLite:
- Change detection via content hashing
- Deletion detection
- Per-space sync state tracking
- Database schema with 2 tables: `confluence_pages` and `confluence_sync_state`

### 3. SyncScheduler (`ingestion/sync_scheduler.py`)

Background scheduler for periodic syncs:
- APScheduler integration
- Configurable interval (default 5 minutes)
- Non-blocking background thread
- Graceful error handling

### 4. CLI (`cli.py`)

Command-line interface for admin operations:
- `sync` - Manual delta/full sync
- `status` - Check sync state
- `list-spaces` - Show configured spaces
- `stats` - Show statistics

### 5. Vector Store Factory (`core/vector_store_factory.py`)

Abstraction layer for future scaling:
- ChromaDB implementation (current)
- Weaviate stub (future migration)
- Factory pattern for easy swapping

## Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Pages supported | 1-100K | Current limit before performance degrades |
| Sync latency | <5 minutes | Delta sync typically <30s for 1000-page space |
| Retrieval latency | <1s (p95) | Vector search + BM25 + reranking |

## Cost Breakdown

| Component | Cost | Notes |
|-----------|------|-------|
| Confluence API | $0 | MCP tools, no additional cost |
| OpenAI embeddings | $100-300/month | Depends on page count |
| Storage | $0 | <1GB for 100K pages |
| **Total** | **~$100-300/month** | Dominated by embedding costs |

## Troubleshooting

### Sync failing with rate limit errors

**Solution**:
```bash
# More conservative settings
CONFLUENCE_RATE_LIMIT=5      # 5 requests/second
CONFLUENCE_SYNC_INTERVAL=10  # Sync every 10 minutes
```

### Pages not appearing in RAG

**Steps**:
1. Check sync status: `python cli.py status --space ENG`
2. Verify pages are in tracking DB
3. Check ChromaDB for Confluence sources

### Stale data after modifying Confluence page

**Solution**:
1. Default sync interval is 5 minutes
2. Force immediate sync: `python cli.py sync --space ENG --ingest`

## Future Enhancements

### Phase 2: Production Readiness (Weeks 3-4)
- Azure Service Bus for async queue
- Worker processes for parallel ingestion
- PostgreSQL migration from SQLite
- Monitoring and metrics dashboard
- Admin UI in Streamlit sidebar

### Phase 3: Scale Preparation (Months 2-3)
- Weaviate deployment on Azure
- Elasticsearch for distributed BM25
- Kubernetes deployment manifests
- Multi-tenancy support

### Phase 4: Billion-Scale (Months 4-6)
- Milvus or Elasticsearch distributed cluster
- Multi-region replication
- Advanced retrieval (ranking, cross-doc reasoning)
- GraphQL API

## References

- **Configuration**: `config.py`
- **Vector Store Abstraction**: `core/vector_store_factory.py`
- **CLI Help**: `python cli.py --help`
