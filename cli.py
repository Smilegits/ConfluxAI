"""
CLI for Confluence RAG management.

Commands:
- sync: Run manual sync for a Confluence space
- status: Show sync status for a space
- list-spaces: List configured spaces
- cleanup: Clean up old deleted pages
"""

import click
import logging

try:
    from config import settings
except ImportError:
    settings = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Confluence RAG CLI - Manage Confluence integration."""
    if settings is None:
        click.secho("Error: Could not load config", fg='red')
        return

    if not settings.confluence_enabled:
        click.secho("⚠ Confluence integration is disabled", fg='yellow')


@cli.command()
@click.option(
    '--space',
    required=True,
    help='Confluence space key (e.g., ENG)'
)
@click.option(
    '--full',
    is_flag=True,
    help='Full sync (ignore last sync time, re-ingest all pages)'
)
@click.option(
    '--ingest',
    is_flag=True,
    help='Ingest modified pages into ChromaDB'
)
def sync(space: str, full: bool, ingest: bool):
    """
    Sync Confluence space.

    Fetches pages from Confluence and tracks changes.
    Optionally ingests modified/new pages into ChromaDB.
    """
    click.echo(f"Syncing space: {space.upper()}")

    try:
        from ingestion.confluence_loader import ConfluenceLoader
        from ingestion.confluence_sync import ConfluenceSyncManager

        sync_manager = ConfluenceSyncManager()
        loader = ConfluenceLoader(spaces=[space])

        if full:
            click.echo("Resetting sync state (full sync)")
            sync_manager.reset_sync_state(space)

        modified_since = None if full else sync_manager.get_last_modified_since(space)

        if modified_since:
            click.echo(f"Delta sync since: {modified_since}")
        else:
            click.echo("Full sync mode")

        raw_docs = loader.load_space(space, modified_since=modified_since)

        if not raw_docs:
            click.secho("No pages found", fg='yellow')
            return

        click.echo(f"Found {len(raw_docs)} pages")

        # Detect changes
        new_count = 0
        modified_count = 0
        unchanged_count = 0

        for doc in raw_docs:
            page_id = doc.metadata.get('page_id')
            content_hash = doc.metadata.get('source_hash')

            if not page_id or not content_hash:
                continue

            change_type = sync_manager.detect_changes(page_id, content_hash)

            if change_type.value == 'new':
                new_count += 1
            elif change_type.value == 'modified':
                modified_count += 1
            else:
                unchanged_count += 1

        click.echo()
        click.secho("Change Detection:", fg='bold')
        click.echo(f"  New:       {new_count:5d}")
        click.echo(f"  Modified:  {modified_count:5d}")
        click.echo(f"  Unchanged: {unchanged_count:5d}")
        click.echo(f"  Total:     {len(raw_docs):5d}")

        # Update tracking DB
        for doc in raw_docs:
            sync_manager.record_page(
                page_id=doc.metadata.get('page_id'),
                space_key=space,
                title=doc.metadata.get('title'),
                last_modified=doc.metadata.get('last_modified'),
                content_hash=doc.metadata.get('source_hash')
            )

        sync_manager.update_sync_state(
            space_key=space,
            total_pages=len(raw_docs),
            status='success'
        )

        if ingest and (new_count + modified_count) > 0:
            click.echo()
            click.secho("Ingesting into RAG...", fg='bold')

            from ingestion.pipeline import IngestionPipeline
            pipeline = IngestionPipeline()
            result = pipeline.ingest_confluence_pages(raw_docs)

            click.secho("Ingestion complete:", fg='bold')
            click.echo(f"  Processed: {result.get('processed', 0)}")
            click.echo(f"  Skipped:   {result.get('skipped', 0)}")
            click.echo(f"  Chunks:    {result.get('chunks_created', 0)}")
            click.echo(f"  Errors:    {result.get('errors', 0)}")

        click.secho("\n✓ Sync complete", fg='green')

    except Exception as e:
        click.secho(f"✗ Sync failed: {e}", fg='red')
        logger.error(f"Sync error: {e}", exc_info=True)


@cli.command()
@click.option(
    '--space',
    required=True,
    help='Confluence space key'
)
def status(space: str):
    """
    Show sync status for a space.

    Displays sync state and statistics.
    """
    click.secho(f"Status for space: {space.upper()}", fg='bold')

    try:
        from ingestion.confluence_sync import ConfluenceSyncManager

        sync_manager = ConfluenceSyncManager()
        state = sync_manager.get_sync_state(space)
        stats = sync_manager.get_stats(space)

        click.echo()

        if state:
            click.echo(f"Last sync:   {state.get('last_sync_time', 'Never')}")
            click.echo(f"Total pages: {state.get('total_pages', 0)}")
            click.echo(f"Status:      {state.get('last_sync_status', 'Unknown')}")

            if state.get('last_error'):
                click.secho(f"Last error:  {state['last_error']}", fg='red')
        else:
            click.secho("No sync state found (run sync first)", fg='yellow')

        click.echo()
        click.secho("Page Statistics:", fg='bold')
        click.echo(f"  Active:   {stats.get('active', 0)}")
        click.echo(f"  Deleted:  {stats.get('deleted', 0)}")
        click.echo(f"  Total:    {stats.get('total', 0)}")

    except Exception as e:
        click.secho(f"✗ Error: {e}", fg='red')


@cli.command()
def list_spaces():
    """
    List configured Confluence spaces.

    Shows which spaces are monitored by the sync system.
    """
    if settings is None or not settings.confluence_spaces:
        click.secho("No spaces configured", fg='yellow')
        click.echo("Set CONFLUENCE_SPACES in .env file")
        return

    click.secho("Configured Confluence spaces:", fg='bold')

    try:
        from ingestion.confluence_sync import ConfluenceSyncManager

        sync_manager = ConfluenceSyncManager()

        for space in settings.confluence_spaces:
            state = sync_manager.get_sync_state(space)
            stats = sync_manager.get_stats(space)

            if state and state.get('last_sync_time'):
                last_sync = state['last_sync_time']
                total = state.get('total_pages', 0)
                status = state.get('last_sync_status', 'unknown')

                click.echo(
                    f"  {space:15s} | "
                    f"Pages: {total:5d} | "
                    f"Last sync: {last_sync} | "
                    f"Status: {status}"
                )
            else:
                total = stats.get('total', 0)
                click.echo(
                    f"  {space:15s} | "
                    f"Pages: {total:5d} | "
                    f"Last sync: Never"
                )

    except Exception as e:
        click.secho(f"✗ Error: {e}", fg='red')


@cli.command()
@click.option(
    '--space',
    required=False,
    help='Filter by space key (optional)'
)
def stats(space: str = None):
    """
    Show overall statistics.

    Displays total tracked pages and their status.
    """
    try:
        from ingestion.confluence_sync import ConfluenceSyncManager

        sync_manager = ConfluenceSyncManager()

        if space:
            stats_data = sync_manager.get_stats(space)
            click.secho(f"Statistics for space: {space.upper()}", fg='bold')
        else:
            stats_data = sync_manager.get_stats()
            click.secho("Overall Statistics", fg='bold')

        click.echo(f"  Active pages:  {stats_data.get('active', 0)}")
        click.echo(f"  Deleted pages: {stats_data.get('deleted', 0)}")
        click.echo(f"  Total tracked: {stats_data.get('total', 0)}")

    except Exception as e:
        click.secho(f"✗ Error: {e}", fg='red')


if __name__ == '__main__':
    cli()
