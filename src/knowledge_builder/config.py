from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProcessingConfig(StrictModel):
    pages_per_batch: int = Field(10, ge=1)
    max_workers: int = Field(1, ge=1)
    continue_on_error: bool = True
    retries: int = Field(2, ge=0)
    resume: bool = True
    preserve_intermediate: bool = True
    image_max_long_edge: int = Field(1600, ge=128)
    image_max_pixels: int = Field(4_000_000, ge=10_000)
    min_image_width: int = Field(80, ge=1)
    min_image_height: int = Field(80, ge=1)
    max_images_per_vlm_batch: int = Field(1, ge=1)
    native_text_min_chars: int = Field(40, ge=1)
    page_image_dpi: int = Field(144, ge=72, le=300)
    preserve_page_images: bool = True


class ParsingConfig(StrictModel):
    engine: Literal["docling", "pymupdf"] = "docling"
    pipeline: str = "standard"
    ocr: str = "auto"
    language_hints: list[str] = ["zh-TW", "en"]
    export_structured_json: bool = True
    preserve_tables: bool = True
    preserve_images: bool = True


class ProviderConfig(StrictModel):
    enabled: bool = False
    provider: Literal["none", "openai_compatible"] = "none"
    model: str | None = None
    timeout_seconds: int = Field(120, ge=1)
    retries: int = Field(2, ge=0)
    describe_diagrams: bool = True
    describe_photos: bool = True
    describe_charts: bool = True
    include_neighbor_text: bool = True


class SummaryConfig(StrictModel):
    enabled: bool = False
    provider: Literal["none", "openai_compatible"] = "none"
    model: str | None = None
    max_input_tokens_per_call: int = Field(6000, ge=256)
    language: str = "zh-TW"
    timeout_seconds: int = Field(120, ge=1)
    retries: int = Field(2, ge=0)


class OutputConfig(StrictModel):
    split_strategy: str = "headings_with_page_fallback"
    fallback_pages_per_file: int = Field(10, ge=1)
    max_markdown_pages_per_file: int = Field(100, ge=1)
    create_document_index: bool = True
    create_chunks_jsonl: bool = True
    markdown_image_links: str = "relative"
    preserve_source_page_numbers: bool = True


class AppConfig(StrictModel):
    input_dir: Path = Path("data/input")
    work_dir: Path = Path("data/work")
    output_dir: Path = Path("data/output")
    processing: ProcessingConfig = ProcessingConfig()
    parsing: ParsingConfig = ParsingConfig()
    vision: ProviderConfig = ProviderConfig()
    summary: SummaryConfig = SummaryConfig()
    output: OutputConfig = OutputConfig()

    def fingerprint(self) -> str:
        # Only values that can change parsing artifacts invalidate successful PDF batches.
        relevant = {
            "pages_per_batch": self.processing.pages_per_batch,
            "native_text_min_chars": self.processing.native_text_min_chars,
            "parsing": self.parsing.model_dump(mode="json"),
        }
        return hashlib.sha256(json.dumps(relevant, sort_keys=True).encode()).hexdigest()


def load_config(path: Path) -> AppConfig:
    with path.open("r", encoding="utf-8") as handle:
        return AppConfig.model_validate(yaml.safe_load(handle) or {})
