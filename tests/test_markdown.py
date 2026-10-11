import json

import yaml

from knowledge_builder.pipeline import build_pdf


def test_offline_markdown_and_jsonl_are_valid(synthetic_pdf, config):
    manifest, report = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    output = config.output_dir / manifest["document_id"]
    markdown = next((output / "chapters").glob("*.md")).read_text(encoding="utf-8")
    metadata = yaml.safe_load(markdown.split("---", 2)[1])
    assert metadata["processing_status"] == "pending_enrichment"
    assert metadata["summary"] is None
    assert "global page 10" in markdown and "global page 11" in markdown
    assert "p0011_fig001" in markdown
    assert (output / "images" / "p0011_fig001.png").exists()
    assert report["images_extracted"] == 1
    assert report["images_pending"] == 1
    assert (output / "INDEX.md").exists()
    for line in (output / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
        assert json.loads(line)["page_numbers"]
    assert report["valid"]
