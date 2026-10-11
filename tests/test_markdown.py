import json

import yaml

from knowledge_builder.pipeline import build_pdf


def test_offline_markdown_and_jsonl_are_valid(synthetic_pdf, config):
    manifest, report = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    output = config.output_dir / manifest["document_id"]
    markdown_path = output / "DOCUMENT.md"
    markdown = markdown_path.read_text(encoding="utf-8")
    metadata = yaml.safe_load(markdown.split("---", 2)[1])
    assert metadata["processing_status"] == "pending_enrichment"
    assert metadata["summary"] is None
    assert "global page 10" in markdown and "global page 11" in markdown
    assert "p0011_fig001" in markdown
    assert "pages/page_0011.webp" in markdown
    assert report["markdown_documents"] == 1
    assert (output / "images" / "p0011_fig001.png").exists()
    assert (output / "pages" / "page_0011.webp").exists()
    assert (output / "extracted" / "page_0011.json").exists()
    assert report["images_extracted"] == 1
    assert report["images_pending"] == 1
    assert (output / "INDEX.md").exists()
    assert "DOCUMENT.md#ch-" in (output / "INDEX.md").read_text(encoding="utf-8")
    for line in (output / "chunks.jsonl").read_text(encoding="utf-8").splitlines():
        assert json.loads(line)["page_numbers"]
    assert report["valid"]
