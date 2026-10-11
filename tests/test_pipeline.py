import pymupdf as fitz

from knowledge_builder.pipeline import build_pdf


def test_repeat_skips_and_changed_source_gets_new_id(synthetic_pdf, config):
    first, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    attempts = {key: value["attempts"] for key, value in first["batches"].items()}
    second, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    assert {key: value["attempts"] for key, value in second["batches"].items()} == attempts
    changed = synthetic_pdf.with_name("changed.pdf")
    with fitz.open(synthetic_pdf) as doc:
        doc[0].insert_text((72, 200), "changed")
        doc.save(changed)
    third, _ = build_pdf(changed, config, skip_vlm=True, skip_llm=True)
    assert third["document_id"] != first["document_id"]


def test_config_change_invalidates_cache(synthetic_pdf, config):
    first, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    config.parsing.preserve_tables = False
    second, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    assert second["batches"]["batch-00001-00010"]["attempts"] == 1
    assert first["config_fingerprint"] != second["config_fingerprint"]
