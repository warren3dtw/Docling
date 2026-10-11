from pathlib import Path
from io import BytesIO

import pymupdf as fitz
import pytest
from PIL import Image, ImageDraw

from knowledge_builder.config import AppConfig


@pytest.fixture
def synthetic_pdf(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.pdf"
    doc = fitz.open()
    for number in range(1, 24):
        page = doc.new_page()
        if number == 1:
            page.insert_text((72, 72), "Chapter One", fontsize=20)
        page.insert_text((72, 110), f"Synthetic content global page {number}", fontsize=11)
        if number == 11:
            page.insert_text((72, 150), "Table: A | B", fontsize=11)
            for x in (72, 172, 272):
                page.draw_line((x, 170), (x, 230))
            for y in (170, 200, 230):
                page.draw_line((72, y), (272, y))
            page.insert_text((82, 190), "A1", fontsize=9)
            page.insert_text((182, 190), "B1", fontsize=9)
            image = Image.new("RGB", (120, 120), "white")
            ImageDraw.Draw(image).rectangle((15, 15, 105, 105), outline="blue", width=5)
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            page.insert_image(fitz.Rect(320, 150, 440, 270), stream=buffer.getvalue())
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def config(tmp_path: Path) -> AppConfig:
    value = AppConfig()
    value.input_dir = tmp_path / "input"
    value.work_dir = tmp_path / "work"
    value.output_dir = tmp_path / "output"
    value.parsing.engine = "pymupdf"
    value.processing.pages_per_batch = 10
    value.processing.retries = 0
    value.processing.page_image_dpi = 72
    value.processing.image_max_long_edge = 800
    value.processing.image_max_pixels = 640_000
    value.output.fallback_pages_per_file = 100
    return value
