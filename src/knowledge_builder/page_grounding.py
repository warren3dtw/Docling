from __future__ import annotations

import math
import os
import re
import shutil
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from .config import AppConfig
from .state import atomic_write_json, sha256_file


_NUMBER_WITH_UNIT = re.compile(
    r"\b\d+(?:[.,]\d+)?\s*(?:mm|cm|m|kg|kn|mpa|gpa|n|lb|ft|in|%|°c|°f)\b",
    re.IGNORECASE,
)


def preserve_source_pdf(source: Path, work_dir: Path, expected_sha256: str) -> Path:
    """Keep an immutable local source copy without ever modifying data/input."""
    destination = work_dir / "source" / "original.pdf"
    if destination.exists() and sha256_file(destination) == expected_sha256:
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    shutil.copyfile(source, temporary)
    if sha256_file(temporary) != expected_sha256:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("Preserved source PDF hash does not match the input PDF")
    temporary.replace(destination)
    return destination


def profile_pdf(pdf: Path, native_text_min_chars: int) -> list[dict]:
    profiles: list[dict] = []
    with fitz.open(pdf) as document:
        for page_index, page in enumerate(document):
            text = page.get_text("text", sort=True)
            text_chars = len(re.sub(r"\s+", "", text))
            try:
                drawings = len(page.get_drawings())
            except Exception:
                drawings = 0
            image_infos = page.get_image_info()
            page_area = max(page.rect.width * page.rect.height, 1)
            image_area = 0.0
            for image in image_infos:
                try:
                    box = fitz.Rect(image["bbox"]) & page.rect
                    image_area += max(box.width, 0) * max(box.height, 0)
                except (KeyError, TypeError, ValueError):
                    continue
            image_coverage = min(image_area / page_area, 1.0)

            labels: list[str] = []
            if text_chars == 0 and not image_infos and drawings == 0:
                labels.append("blank")
            else:
                if text_chars >= native_text_min_chars:
                    labels.append("native_text")
                elif image_infos:
                    labels.append("scan_or_image")
                elif text_chars:
                    labels.append("sparse_text")
                if image_infos and text_chars:
                    labels.append("text_and_figures")
                elif image_infos:
                    labels.append("image_only")
                if drawings >= 10:
                    labels.append("technical_diagram")
                if image_coverage >= 0.5 and text_chars < native_text_min_chars:
                    labels.append("scan")
                if not labels:
                    labels.append("uncertain")

            if "blank" in labels:
                route = "skip_blank"
            elif "native_text" in labels and "text_and_figures" not in labels:
                route = "native_text"
            elif "scan" in labels or "image_only" in labels:
                route = "ocr_then_visual_review"
            elif "text_and_figures" in labels or "technical_diagram" in labels:
                route = "hybrid_text_and_visual"
            else:
                route = "inspect"
            profiles.append(
                {
                    "page_number": page_index + 1,
                    "labels": labels,
                    "recommended_route": route,
                    "native_text_chars": text_chars,
                    "embedded_images": len(image_infos),
                    "vector_drawings": drawings,
                    "image_coverage": round(image_coverage, 4),
                    "width_points": round(page.rect.width, 2),
                    "height_points": round(page.rect.height, 2),
                }
            )
    return profiles


def render_page_images(
    pdf: Path,
    output_dir: Path,
    dpi: int,
    max_long_edge: int,
    max_pixels: int,
    regenerate: bool = False,
) -> list[dict]:
    """Render one page at a time with a pre-render pixel bound."""
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    with fitz.open(pdf) as document:
        for page_index, page in enumerate(document):
            destination = output_dir / f"page_{page_index + 1:04d}.webp"
            target_width = page.rect.width * dpi / 72
            target_height = page.rect.height * dpi / 72
            scale = min(
                1.0,
                max_long_edge / max(target_width, target_height, 1),
                math.sqrt(max_pixels / max(target_width * target_height, 1)),
            )
            effective_dpi = max(36.0, dpi * scale)
            if regenerate or not destination.exists():
                pixmap = page.get_pixmap(matrix=fitz.Matrix(effective_dpi / 72, effective_dpi / 72), alpha=False)
                image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
                temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
                image.save(temporary, format="WEBP", quality=88, method=4)
                temporary.replace(destination)
            with Image.open(destination) as saved:
                width, height = saved.size
            records.append(
                {
                    "page_number": page_index + 1,
                    "path": f"pages/{destination.name}",
                    "width": width,
                    "height": height,
                    "sha256": sha256_file(destination),
                }
            )
    return records


def _quality_warnings(text: str, profile: dict) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    warnings: list[str] = []
    labels = set(profile.get("labels", []))
    if not compact and labels - {"blank"}:
        warnings.append("visual_or_nonblank_page_without_extracted_text")
    elif 0 < len(compact) < 20:
        warnings.append("very_short_extracted_text")
    if "\ufffd" in text:
        warnings.append("replacement_characters_detected")
    if len(compact) >= 40:
        most_common = max((compact.count(character) for character in set(compact)), default=0)
        if most_common / len(compact) > 0.35:
            warnings.append("suspected_repeated_or_garbled_text")
    if _NUMBER_WITH_UNIT.search(text):
        warnings.append("numeric_spec_requires_review")
    return warnings


def _batch_for_page(manifest: dict, page_number: int) -> tuple[str | None, dict]:
    for batch_id, batch in manifest.get("batches", {}).items():
        if batch.get("start_page", 0) <= page_number <= batch.get("end_page", -1):
            return batch_id, batch
    return None, {}


def write_page_records(
    work_dir: Path,
    output_dir: Path,
    info: object,
    config: AppConfig,
    manifest: dict,
    profiles: list[dict],
    parsed_pages: list[dict],
    page_images: list[dict],
    figures: list[dict],
) -> list[dict]:
    parsed_by_page = {page["page_number"]: page for page in parsed_pages}
    images_by_page = {image["page_number"]: image for image in page_images}
    figures_by_page: dict[int, list[dict]] = {}
    for figure in figures:
        figures_by_page.setdefault(figure["source_page"], []).append(figure)
    summaries: list[dict] = []

    for profile in profiles:
        page_number = profile["page_number"]
        parsed = parsed_by_page.get(page_number, {})
        batch_id, batch = _batch_for_page(manifest, page_number)
        text = parsed.get("text", "")
        warnings = _quality_warnings(text, profile)
        labels = set(profile.get("labels", []))
        if batch.get("status") == "failed" or not batch:
            status = "failed"
            warnings.append("batch_failed_or_missing")
        elif "blank" in labels and not text.strip():
            status = "skipped_with_reason"
            warnings.append("blank_page")
        elif any(
            warning in warnings
            for warning in (
                "visual_or_nonblank_page_without_extracted_text",
                "very_short_extracted_text",
                "replacement_characters_detected",
                "suspected_repeated_or_garbled_text",
            )
        ):
            status = "partial"
        else:
            status = "success"

        routes: list[str] = []
        if config.parsing.engine == "docling":
            routes.append("docling_standard")
            if profile["recommended_route"] == "ocr_then_visual_review":
                if config.parsing.ocr == "never":
                    warnings.append("ocr_route_disabled")
                else:
                    routes.append("ocr")
        else:
            routes.append("pymupdf_native_text")
            if profile["recommended_route"] == "ocr_then_visual_review":
                warnings.append("ocr_unavailable_with_pymupdf")

        page_figures = [
            {
                "figure_id": figure["image_id"],
                "image_path": f"images/{figure['image_id']}.png",
                "description": figure.get("caption_vlm"),
                "region": None,
                "processing_status": figure.get("processing_status"),
            }
            for figure in figures_by_page.get(page_number, [])
        ]
        image = images_by_page.get(page_number)
        record = {
            "document_id": info.document_id,
            "source_sha256": info.sha256,
            "source_file": "source/original.pdf",
            "page_number": page_number,
            "page_image": image["path"] if image else None,
            "status": status,
            "page_profile": profile["labels"],
            "profile_metrics": {key: value for key, value in profile.items() if key not in {"page_number", "labels"}},
            "routes_attempted": routes,
            "extracted_text": text,
            "tables": parsed.get("tables", []),
            "figures": page_figures,
            "facts": [],
            "quality": {"warnings": sorted(set(warnings))},
            "processing": {
                "pipeline_version": "v1",
                "parser": config.parsing.engine,
                "ocr_setting": config.parsing.ocr,
                "vlm_model": config.vision.model if config.vision.enabled else None,
                "batch_id": batch_id,
            },
        }
        record_path = work_dir / "extracted" / f"page_{page_number:04d}.json"
        atomic_write_json(record_path, record)
        atomic_write_json(output_dir / "extracted" / record_path.name, record)
        summaries.append(
            {
                "page_number": page_number,
                "status": status,
                "page_profile": profile["labels"],
                "page_record": f"extracted/{record_path.name}",
                "page_image": record["page_image"],
                "quality_warnings": record["quality"]["warnings"],
            }
        )
    return summaries
