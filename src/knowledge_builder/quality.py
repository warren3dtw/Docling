from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from .state import atomic_write_json


def validate_output(output_dir: Path, manifest: dict, write_report: bool = True) -> dict:
    broken: list[str] = []
    warnings: list[str] = list(manifest.get("warnings", []))
    markdown_documents = sorted(output_dir.glob("DOCUMENT.md")) + sorted(output_dir.glob("PART-*.md"))
    legacy_chapters = list((output_dir / "chapters").glob("*.md")) if (output_dir / "chapters").exists() else []
    chapters = markdown_documents or legacy_chapters
    for path in chapters:
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            broken.append(f"frontmatter missing: {path.name}")
            continue
        try:
            yaml.safe_load(text.split("---", 2)[1])
        except yaml.YAMLError as exc:
            broken.append(f"frontmatter invalid: {path.name}: {exc}")
        for target in re.findall(r"!\[[^]]*\]\(([^)]+)\)", text):
            if not (path.parent / target.split("#", 1)[0]).resolve().exists():
                broken.append(f"image link: {path.name} -> {target}")
        for target in re.findall(r"(?<!!)\[[^]]*\]\(([^)]+)\)", text):
            if "://" not in target and not target.startswith("#") and not (path.parent / target.split("#", 1)[0]).resolve().exists():
                broken.append(f"relative link: {path.name} -> {target}")
    chunk_path = output_dir / "chunks.jsonl"
    if chunk_path.exists():
        for line_number, line in enumerate(chunk_path.read_text(encoding="utf-8").splitlines(), start=1):
            try:
                json.loads(line)
            except json.JSONDecodeError:
                broken.append(f"chunks.jsonl line {line_number}")
    batches = list(manifest.get("batches", {}).values())
    images = manifest.get("images", [])
    pages = manifest.get("pages", [])
    page_numbers = [page.get("page_number") for page in pages]
    expected_page_numbers = list(range(1, manifest.get("page_count", 0) + 1))
    if sorted(number for number in page_numbers if isinstance(number, int)) != expected_page_numbers:
        broken.append("page records missing, duplicated, or outside the source page range")
    allowed_page_statuses = {"success", "partial", "failed", "skipped_with_reason"}
    for page in pages:
        page_number = page.get("page_number")
        if page.get("status") not in allowed_page_statuses:
            broken.append(f"page {page_number}: invalid status {page.get('status')}")
        record_path = page.get("page_record")
        if not record_path or not (output_dir / record_path).exists():
            broken.append(f"page {page_number}: missing page record")
        page_image = page.get("page_image")
        if page_image and not (output_dir / page_image).exists():
            broken.append(f"page {page_number}: missing page image")
    report = {
        "pages_total": manifest.get("page_count", 0),
        "pages_parsed": sum(b.get("page_count", 0) for b in batches if b.get("status") == "succeeded"),
        "batches_succeeded": sum(b.get("status") == "succeeded" for b in batches),
        "batches_failed": sum(b.get("status") == "failed" for b in batches),
        "images_extracted": len(images),
        "images_described": sum(i.get("processing_status") == "succeeded" for i in images),
        "images_pending": sum(i.get("processing_status") != "succeeded" for i in images),
        "page_statuses": {
            status: sum(page.get("status") == status for page in pages)
            for status in sorted(allowed_page_statuses)
        },
        "chapters_created": len(manifest.get("chapters", chapters)), "broken_links": broken, "warnings": warnings,
        "markdown_documents": len(markdown_documents),
        "manual_review": ["抽驗每批至少一頁文字與原 PDF 一致", "抽驗表格欄列與單位", "抽驗圖片頁碼與圖說"],
        "valid": not broken and not any(b.get("status") == "failed" for b in batches),
    }
    if write_report:
        atomic_write_json(output_dir / "qa_report.json", report)
    return report
