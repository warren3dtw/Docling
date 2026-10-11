import json

from knowledge_builder.pipeline import build_pdf


def test_second_batch_uses_global_page_numbers(synthetic_pdf, config):
    manifest, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    path = config.work_dir / manifest["document_id"] / "batches" / "batch-00011-00020.json"
    pages = json.loads(path.read_text(encoding="utf-8"))["pages"]
    assert pages[0]["page_number"] == 11
    assert "global page 11" in pages[0]["text"]
