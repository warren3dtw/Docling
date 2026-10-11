from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Protocol

import pymupdf as fitz

from .config import AppConfig


class BatchParser(Protocol):
    name: str

    def parse(self, batch_pdf: Path, global_start_page: int, raw_output: Path) -> dict[str, Any]: ...


def _page_content(doc: fitz.Document, local_index: int, global_page: int, preserve_tables: bool) -> dict:
    page = doc[local_index]
    text = page.get_text("text", sort=True).strip()
    blocks = page.get_text("dict", sort=True).get("blocks", [])
    headings: list[str] = []
    spans = [span for block in blocks if "lines" in block for line in block["lines"] for span in line["spans"] if span.get("text", "").strip()]
    if spans:
        body_size = sorted(float(s.get("size", 0)) for s in spans)[len(spans) // 2]
        headings = [s["text"].strip() for s in spans if float(s.get("size", 0)) >= body_size * 1.25 and len(s["text"].strip()) < 160]
    tables: list[str] = []
    if preserve_tables and hasattr(page, "find_tables"):
        try:
            for table in page.find_tables().tables:
                rows = table.extract()
                if rows:
                    width = max(len(row) for row in rows)
                    clean = [[str(cell or "").replace("|", "\\|").replace("\n", " ") for cell in row] + [""] * (width - len(row)) for row in rows]
                    tables.append("| " + " | ".join(clean[0]) + " |\n| " + " | ".join(["---"] * width) + " |\n" + "\n".join("| " + " | ".join(row) + " |" for row in clean[1:]))
        except Exception:
            tables = []
    return {"page_number": global_page, "text": text, "headings": headings, "tables": tables}


class PyMuPDFParser:
    name = "pymupdf"

    def __init__(self, config: AppConfig):
        self.config = config

    def parse(self, batch_pdf: Path, global_start_page: int, raw_output: Path) -> dict[str, Any]:
        with fitz.open(batch_pdf) as doc:
            pages = [_page_content(doc, i, global_start_page + i, self.config.parsing.preserve_tables) for i in range(doc.page_count)]
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        raw_output.write_text(json.dumps({"engine": self.name, "pages": pages}, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"engine": self.name, "pages": pages, "warnings": ["使用 PyMuPDF 基礎解析器；未執行 Docling 版面模型。"]}


class DoclingParser:
    name = "docling"

    def __init__(self, config: AppConfig):
        self.config = config

    def parse(self, batch_pdf: Path, global_start_page: int, raw_output: Path) -> dict[str, Any]:
        try:
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as exc:
            raise RuntimeError("Docling 未安裝；請執行 `uv sync --extra docling`，或將 parsing.engine 設為 pymupdf。") from exc

        options = PdfPipelineOptions()
        options.do_ocr = self.config.parsing.ocr != "never"
        options.do_table_structure = self.config.parsing.preserve_tables
        options.generate_picture_images = self.config.parsing.preserve_images
        options.generate_page_images = False
        converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})
        result = converter.convert(batch_pdf, raises_on_error=True)
        raw = result.document.export_to_dict()
        raw_output.parent.mkdir(parents=True, exist_ok=True)
        raw_output.write_text(json.dumps(raw, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

        # Docling's page-scoped serializer preserves reading order and tables. PyMuPDF
        # supplies an explicit, auditable local→global page map and fallback text.
        with fitz.open(batch_pdf) as doc:
            pages = []
            for i in range(doc.page_count):
                page = _page_content(doc, i, global_start_page + i, self.config.parsing.preserve_tables)
                markdown = result.document.export_to_markdown(page_no=i + 1, traverse_pictures=True).strip()
                if markdown:
                    page["text"] = markdown
                    page["headings"] = [match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+)$", markdown, re.MULTILINE)]
                    page["tables"] = []  # Tables are already serialized in Docling Markdown.
                pages.append(page)
        return {"engine": self.name, "pages": pages, "docling_status": str(result.status), "warnings": []}


def make_parser(config: AppConfig) -> BatchParser:
    return DoclingParser(config) if config.parsing.engine == "docling" else PyMuPDFParser(config)
