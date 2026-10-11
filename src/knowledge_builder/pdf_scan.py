from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import pymupdf as fitz


@dataclass(frozen=True)
class PdfInfo:
    path: str
    filename: str
    sha256: str
    document_id: str
    page_count: int
    metadata: dict
    toc: list

    def to_dict(self) -> dict:
        return asdict(self)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_pdf(path: Path) -> PdfInfo:
    sha = file_sha256(path)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", path.stem).strip("-").lower() or "document"
    with fitz.open(path) as doc:
        return PdfInfo(str(path.resolve()), path.name, sha, f"{slug}-{sha[:12]}", doc.page_count, dict(doc.metadata or {}), doc.get_toc(simple=True))


def split_pdf(source: Path, destination: Path, start_page: int, end_page: int) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".tmp")
    with fitz.open(source) as src, fitz.open() as out:
        out.insert_pdf(src, from_page=start_page - 1, to_page=end_page - 1)
        out.save(temp)
    temp.replace(destination)
