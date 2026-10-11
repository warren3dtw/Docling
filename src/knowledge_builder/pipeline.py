from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from .batching import make_batches
from .chapter_assembly import assemble_chapters
from .config import AppConfig
from .image_extract import extract_images
from .index_build import build_indexes
from .markdown_export import export_chapters
from .page_grounding import preserve_source_pdf, profile_pdf, render_page_images, write_page_records
from .llm import provider_from_env as summary_provider_from_env
from .parse_docling import BatchParser, make_parser
from .pdf_scan import scan_pdf, split_pdf
from .quality import validate_output
from .state import atomic_write_json, load_json, reusable_batch, sha256_file, utc_now
from .vlm import provider_from_env as vision_provider_from_env


def build_pdf(pdf: Path, config: AppConfig, parser: BatchParser | None = None, force: bool = False, skip_vlm: bool = False, skip_llm: bool = False) -> tuple[dict, dict]:
    info = scan_pdf(pdf)
    work_dir = config.work_dir / info.document_id
    output_dir = config.output_dir / info.document_id
    work_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    preserve_source_pdf(pdf, work_dir, info.sha256)
    profiles = profile_pdf(pdf, config.processing.native_text_min_chars)
    manifest_path = work_dir / "manifest.json"
    previous = load_json(manifest_path, {})
    fingerprint = config.fingerprint()
    cache_valid = previous.get("source_sha256") == info.sha256 and previous.get("config_fingerprint") == fingerprint
    manifest = previous if cache_valid else {}
    manifest.update({
        "schema_version": 1, "document_id": info.document_id, "source_file": info.filename,
        "source_path": info.path, "source_sha256": info.sha256, "config_fingerprint": fingerprint,
        "page_count": info.page_count, "parser": config.parsing.engine, "updated_at": utc_now(),
        "preserved_source": "source/original.pdf", "page_profiles": profiles,
    })
    if not cache_valid:
        manifest["batches"] = {}
    manifest.setdefault("batches", {})
    manifest.setdefault("warnings", [])
    page_asset_fingerprint = ":".join(
        str(value)
        for value in (
            info.sha256,
            config.processing.page_image_dpi,
            config.processing.image_max_long_edge,
            config.processing.image_max_pixels,
        )
    )
    regenerate_page_images = force or previous.get("page_asset_fingerprint") != page_asset_fingerprint
    page_images = (
        render_page_images(
            pdf,
            output_dir / "pages",
            config.processing.page_image_dpi,
            config.processing.image_max_long_edge,
            config.processing.image_max_pixels,
            regenerate=regenerate_page_images,
        )
        if config.processing.preserve_page_images
        else []
    )
    manifest["page_asset_fingerprint"] = page_asset_fingerprint
    manifest["page_images"] = page_images
    atomic_write_json(manifest_path, manifest)
    parser = parser or make_parser(config)

    for batch in make_batches(info.page_count, config.processing.pages_per_batch):
        result_path = work_dir / "batches" / f"{batch.batch_id}.json"
        batch_pdf = work_dir / "batch_pdfs" / f"{batch.batch_id}.pdf"
        raw_path = work_dir / "docling" / f"{batch.batch_id}.json"
        old = manifest["batches"].get(batch.batch_id)
        if not force and cache_valid and reusable_batch(old, result_path):
            continue
        record = {**batch.to_dict(), "page_count": batch.page_count, "status": "running", "started_at": utc_now(), "attempts": int((old or {}).get("attempts", 0))}
        manifest["batches"][batch.batch_id] = record
        atomic_write_json(manifest_path, manifest)
        started = time.monotonic()
        for retry_index in range(config.processing.retries + 1):
            record["attempts"] += 1
            try:
                if retry_index == 0 or not batch_pdf.exists():
                    split_pdf(pdf, batch_pdf, batch.start_page, batch.end_page)
                parsed = parser.parse(batch_pdf, batch.start_page, raw_path)
                result_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write_json(result_path, parsed)
                record.update({"status": "succeeded", "finished_at": utc_now(), "elapsed_seconds": round(time.monotonic() - started, 3), "output_path": str(result_path), "output_sha256": sha256_file(result_path), "error": None})
                break
            except Exception as exc:
                record.update({"status": "failed", "finished_at": utc_now(), "elapsed_seconds": round(time.monotonic() - started, 3), "error": f"{type(exc).__name__}: {exc}"})
                atomic_write_json(manifest_path, manifest)
                if retry_index == config.processing.retries and not config.processing.continue_on_error:
                    raise
        atomic_write_json(manifest_path, manifest)

    pages: list[dict] = []
    for batch in make_batches(info.page_count, config.processing.pages_per_batch):
        record = manifest["batches"].get(batch.batch_id, {})
        result_path = work_dir / "batches" / f"{batch.batch_id}.json"
        if record.get("status") == "succeeded" and result_path.exists():
            pages.extend(load_json(result_path, {}).get("pages", []))
    images, filtered = extract_images(pdf, output_dir / "images", config.processing) if config.parsing.preserve_images else ([], [])
    page_text = {page["page_number"]: page.get("text", "") for page in pages}
    if config.vision.enabled and not skip_vlm:
        if config.vision.provider != "openai_compatible":
            raise RuntimeError(f"不支援的 VLM provider：{config.vision.provider}")
        provider = vision_provider_from_env(config.vision.model, config.vision.timeout_seconds, config.vision.retries)
        for image in images:
            cache_path = work_dir / "images" / f"{image['image_id']}.json"
            cached = load_json(cache_path, {})
            if cached.get("processing_status") == "succeeded" and cached.get("provider_model") == config.vision.model:
                image.update(cached)
                continue
            try:
                result = provider.describe(output_dir / "images" / f"{image['image_id']}.png", page_text.get(image["source_page"], ""))
                image.update(result.model_dump(), processing_status="succeeded", provider_model=config.vision.model)
            except Exception as exc:
                image.update(processing_status="failed", provider_model=config.vision.model, confidence_note=f"VLM 失敗：{type(exc).__name__}: {exc}")
            atomic_write_json(cache_path, image)
    manifest["images"] = images
    manifest["filtered_images"] = filtered
    manifest["warnings"] = sorted(set(manifest.get("warnings", []) + (["VLM 未啟用；圖片描述保持 pending_enrichment。"] if images and (skip_vlm or not config.vision.enabled) else []) + (["LLM 未啟用；摘要與搜尋問題保持 pending_enrichment。"] if skip_llm or not config.summary.enabled else [])))
    manifest["pages"] = write_page_records(work_dir, output_dir, info, config, manifest, profiles, pages, page_images, images)
    atomic_write_json(manifest_path, manifest)
    chapters = assemble_chapters(
        pages,
        config.output.fallback_pages_per_file,
        config.output.max_markdown_pages_per_file,
    )
    if config.summary.enabled and not skip_llm:
        if config.summary.provider != "openai_compatible":
            raise RuntimeError(f"不支援的 LLM provider：{config.summary.provider}")
        provider = summary_provider_from_env(config.summary.model, config.summary.timeout_seconds, config.summary.retries)
        for chapter in chapters:
            cache_path = work_dir / "summaries" / f"{chapter['chapter_id']}.json"
            cached = load_json(cache_path, {})
            if cached.get("processing_status") == "enriched" and cached.get("provider_model") == config.summary.model:
                chapter.update({key: cached[key] for key in ("summary", "keywords", "search_questions", "processing_status")})
                continue
            try:
                # A conservative character approximation keeps requests bounded even without a tokenizer.
                limit = config.summary.max_input_tokens_per_call * 3
                result = provider.summarize(chapter["title"], chapter["text"][:limit])
                chapter.update(result.model_dump(), processing_status="enriched", provider_model=config.summary.model)
            except Exception as exc:
                chapter["processing_status"] = "enrichment_failed"
                chapter["provider_model"] = config.summary.model
                manifest["warnings"].append(f"{chapter['chapter_id']} 摘要失敗：{type(exc).__name__}: {exc}")
            atomic_write_json(cache_path, {key: chapter.get(key) for key in ("chapter_id", "summary", "keywords", "search_questions", "processing_status", "provider_model")})
    document = info.to_dict()
    export_chapters(output_dir, document, chapters, images, page_images, config.output.max_markdown_pages_per_file)
    build_indexes(output_dir, document, chapters, manifest["warnings"])
    manifest["chapters"] = [{key: chapter[key] for key in ("chapter_id", "title", "source_pages", "processing_status")} for chapter in chapters]
    manifest["status"] = (
        "partial"
        if any(value.get("status") == "failed" for value in manifest["batches"].values())
        or any(page.get("status") in {"partial", "failed"} for page in manifest["pages"])
        else "succeeded"
    )
    manifest["updated_at"] = utc_now()
    atomic_write_json(manifest_path, manifest)
    shutil.copy2(manifest_path, output_dir / "manifest.json")
    report = validate_output(output_dir, manifest)
    return manifest, report


def build_directory(input_dir: Path, config: AppConfig, force: bool = False, skip_vlm: bool = False, skip_llm: bool = False) -> list[tuple[dict, dict]]:
    if not input_dir.exists():
        raise FileNotFoundError(f"輸入目錄不存在：{input_dir}")
    pdfs = sorted(input_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"輸入目錄沒有 PDF：{input_dir}")
    return [build_pdf(pdf, config, force=force, skip_vlm=skip_vlm, skip_llm=skip_llm) for pdf in pdfs]
