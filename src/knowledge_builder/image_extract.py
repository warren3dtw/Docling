from __future__ import annotations

import hashlib
from pathlib import Path

import pymupdf as fitz
from PIL import Image

from .config import ProcessingConfig


def extract_images(pdf: Path, output_dir: Path, processing: ProcessingConfig) -> tuple[list[dict], list[dict]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    filtered: list[dict] = []
    seen: set[str] = set()
    with fitz.open(pdf) as doc:
        for page_index, page in enumerate(doc):
            for figure_index, info in enumerate(page.get_images(full=True), start=1):
                xref = info[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                data = pix.tobytes("png")
                digest = hashlib.sha256(data).hexdigest()
                image_id = f"p{page_index + 1:04d}_fig{figure_index:03d}"
                reason = None
                if pix.width < processing.min_image_width or pix.height < processing.min_image_height:
                    reason = "below_minimum_dimensions"
                elif digest in seen:
                    reason = "duplicate_binary"
                if reason:
                    filtered.append({"image_id": image_id, "source_page": page_index + 1, "reason": reason})
                    continue
                seen.add(digest)
                path = output_dir / f"{image_id}.png"
                path.write_bytes(data)
                with Image.open(path) as image:
                    image.thumbnail((processing.image_max_long_edge, processing.image_max_long_edge))
                    if image.width * image.height > processing.image_max_pixels:
                        scale = (processing.image_max_pixels / (image.width * image.height)) ** 0.5
                        image.thumbnail((int(image.width * scale), int(image.height * scale)))
                    image.convert("RGB").save(path, "PNG", optimize=True)
                records.append({
                    "image_id": image_id, "source_document": pdf.name, "source_page": page_index + 1,
                    "image_path": f"../images/{path.name}", "image_type": "unknown",
                    "caption_original": "", "caption_vlm": None, "visible_text": [],
                    "nearby_section": "", "search_terms": [],
                    "confidence_note": "尚未執行視覺模型。", "processing_status": "pending_enrichment",
                })
    return records, filtered
