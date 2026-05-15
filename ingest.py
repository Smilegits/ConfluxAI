"""
CLI ingestion script.
Reads data/web_urls.txt and all supported files in data/ → embeds → stores in ChromaDB.
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".csv", ".txt", ".xlsx", ".xls"}
DATA_DIR = Path("data")
URLS_FILE = DATA_DIR / "web_urls.txt"


def load_urls() -> list[str]:
    if not URLS_FILE.exists():
        return []
    urls = []
    for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def load_files() -> list[Path]:
    if not DATA_DIR.exists():
        return []
    return [
        f for f in DATA_DIR.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]


def run(urls: list[str], files: list[Path]) -> None:
    from ingestion.pipeline import IngestionPipeline

    if not urls and not files:
        logger.warning("Nothing to ingest. Add URLs to data/web_urls.txt or drop files in data/")
        sys.exit(0)

    pipeline = IngestionPipeline()
    results = []

    for url in urls:
        logger.info("Ingesting URL: %s", url)
        try:
            r = pipeline.ingest_url(url)
            results.append(r)
            logger.info("  ✓ %s  [%d chunks]", r.get("title", url), r["chunks"])
        except Exception as e:
            logger.error("  ✗ %s — %s", url, e)

    for path in files:
        logger.info("Ingesting file: %s", path.name)
        try:
            r = pipeline.ingest_file(str(path))
            results.append(r)
            logger.info("  ✓ %s  [%d chunks]", path.name, r["chunks"])
        except Exception as e:
            logger.error("  ✗ %s — %s", path.name, e)

    ok = sum(1 for r in results if r.get("status") == "ok")
    total_chunks = sum(r.get("chunks", 0) for r in results)
    print(f"\nDone. {ok}/{len(results)} sources ingested — {total_chunks} chunks stored in ChromaDB.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest data into RAG ChromaDB store")
    parser.add_argument("--url", metavar="URL", nargs="*", help="Extra URLs to ingest (in addition to web_urls.txt)")
    parser.add_argument("--file", metavar="FILE", nargs="*", help="Extra files to ingest (in addition to data/ folder)")
    parser.add_argument("--urls-only", action="store_true", help="Skip files, only process URLs")
    parser.add_argument("--files-only", action="store_true", help="Skip URLs, only process files")
    args = parser.parse_args()

    urls = ([] if args.files_only else load_urls()) + (args.url or [])
    files = ([] if args.urls_only else load_files()) + [Path(f) for f in (args.file or [])]

    run(urls, files)


if __name__ == "__main__":
    main()
