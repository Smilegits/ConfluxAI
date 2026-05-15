"""
Source loaders — extract structured text from web pages, PDFs, DOCX, and plain text.
Each returns a RawDocument with text, sections, and metadata.
"""
from __future__ import annotations
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

import fitz  # PyMuPDF
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from docx import Document as DocxDocument

logger = logging.getLogger(__name__)


@dataclass
class RawDocument:
    text: str
    metadata: dict = field(default_factory=dict)
    sections: list[dict] = field(default_factory=list)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode()).hexdigest()[:16]


class WebLoader:
    STRIP_TAGS = {"nav", "footer", "header", "aside", "script", "style", "noscript", "form"}

    def load(self, url: str) -> RawDocument:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "RAGBot/1.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup.find_all(self.STRIP_TAGS):
            tag.decompose()

        main = soup.find("main") or soup.find("article") or soup.find("body") or soup
        sections = self._extract_sections(main)
        full_text = "\n\n".join(
            (f"## {s['heading']}\n{s['text']}" if s["heading"] else s["text"]) for s in sections
        )
        return RawDocument(
            text=full_text,
            metadata={
                "source_type": "web",
                "source": url,
                "title": (soup.title.string.strip() if soup.title and soup.title.string else urlparse(url).netloc),
                "ingested_at": datetime.now(timezone.utc).isoformat(),
            },
            sections=sections,
        )

    def _extract_sections(self, el) -> list[dict]:
        sections, heading, parts = [], "", []
        for child in el.descendants:
            if child.name and child.name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                if parts:
                    sections.append({"heading": heading, "text": " ".join(parts).strip()})
                    parts = []
                heading = child.get_text(strip=True)
            elif isinstance(child, NavigableString):
                t = child.strip()
                if t and child.parent.name not in ("h1", "h2", "h3", "h4", "h5", "h6"):
                    parts.append(t)
        if parts:
            sections.append({"heading": heading, "text": " ".join(parts).strip()})
        return sections


class PDFLoader:
    def load(self, path: str) -> RawDocument:
        doc = fitz.open(path)
        sections, parts = [], []
        for i, page in enumerate(doc, 1):
            text = page.get_text("text").strip()
            if text:
                sections.append({"heading": f"Page {i}", "text": text})
                parts.append(text)
        doc.close()
        return RawDocument(
            text="\n\n".join(parts),
            metadata={"source_type": "pdf", "source": path, "title": path.split("/")[-1],
                       "pages": len(sections), "ingested_at": datetime.now(timezone.utc).isoformat()},
            sections=sections,
        )


class DocxLoader:
    def load(self, path: str) -> RawDocument:
        doc = DocxDocument(path)
        sections, heading, parts = [], "", []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style and para.style.name.startswith("Heading"):
                if parts:
                    sections.append({"heading": heading, "text": "\n".join(parts)})
                    parts = []
                heading = text
            else:
                parts.append(text)
        if parts:
            sections.append({"heading": heading, "text": "\n".join(parts)})

        for i, table in enumerate(doc.tables):
            rows = []
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells]
                rows.append("| " + " | ".join(cells) + " |")
            if rows:
                sep = "| " + " | ".join(["---"] * len(table.rows[0].cells)) + " |"
                sections.append({"heading": f"Table {i+1}", "text": rows[0]+"\n"+sep+"\n"+"\n".join(rows[1:])})

        full = "\n\n".join((f"## {s['heading']}\n{s['text']}" if s["heading"] else s["text"]) for s in sections)
        return RawDocument(
            text=full,
            metadata={"source_type": "docx", "source": path, "title": path.split("/")[-1],
                       "ingested_at": datetime.now(timezone.utc).isoformat()},
            sections=sections,
        )


class TextLoader:
    """For raw pasted text."""
    def load(self, text: str, title: str = "Pasted Text") -> RawDocument:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        sections = [{"heading": "", "text": p} for p in paragraphs]
        return RawDocument(
            text=text,
            metadata={"source_type": "text", "source": "manual", "title": title,
                       "ingested_at": datetime.now(timezone.utc).isoformat()},
            sections=sections,
        )


def get_loader(source: str):
    if source.startswith(("http://", "https://")):
        return WebLoader(), "url"
    elif source.lower().endswith(".pdf"):
        return PDFLoader(), "file"
    elif source.lower().endswith(".docx"):
        return DocxLoader(), "file"
    else:
        raise ValueError(f"Unsupported: {source}. Use URL, .pdf, or .docx")
