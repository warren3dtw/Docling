import json
from io import BytesIO

import pymupdf as fitz
from PIL import Image

from knowledge_builder.pipeline import build_pdf
from knowledge_builder.parse_docling import batch_requires_ocr
from knowledge_builder.state import sha256_file


def test_page_profiles_records_and_source_are_grounded(tmp_path, config):
    pdf = tmp_path / "mixed.pdf"
    document = fitz.open()
    text_page = document.new_page()
    text_page.insert_text((72, 72), "Native technical specification with a reviewed dimension of 125 mm.")

    image_page = document.new_page()
    image = Image.new("RGB", (600, 800), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    image_page.insert_image(image_page.rect, stream=buffer.getvalue())
    document.new_page()
    document.save(pdf)
    document.close()

    assert batch_requires_ocr(pdf, native_text_min_chars=40)

    config.processing.pages_per_batch = 2
    manifest, report = build_pdf(pdf, config, skip_vlm=True, skip_llm=True)
    output = config.output_dir / manifest["document_id"]
    work = config.work_dir / manifest["document_id"]

    assert len(manifest["pages"]) == 3
    assert manifest["pages"][0]["status"] == "success"
    assert "native_text" in manifest["pages"][0]["page_profile"]
    assert manifest["pages"][1]["status"] == "partial"
    assert "image_only" in manifest["pages"][1]["page_profile"]
    assert manifest["pages"][2]["status"] == "skipped_with_reason"

    first_record = json.loads((output / "extracted" / "page_0001.json").read_text(encoding="utf-8"))
    second_record = json.loads((output / "extracted" / "page_0002.json").read_text(encoding="utf-8"))
    assert "numeric_spec_requires_review" in first_record["quality"]["warnings"]
    assert "ocr_unavailable_with_pymupdf" in second_record["quality"]["warnings"]
    assert first_record["source_sha256"] == sha256_file(pdf)
    assert sha256_file(work / "source" / "original.pdf") == sha256_file(pdf)
    assert all((output / f"pages/page_{page:04d}.webp").exists() for page in range(1, 4))
    assert report["page_statuses"] == {
        "failed": 0,
        "partial": 1,
        "skipped_with_reason": 1,
        "success": 1,
    }
    assert report["valid"]


def test_native_text_batch_does_not_request_ocr(tmp_path):
    pdf = tmp_path / "native.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "This page contains enough selectable native text for direct extraction.")
    document.save(pdf)
    document.close()

    assert not batch_requires_ocr(pdf, native_text_min_chars=40)
