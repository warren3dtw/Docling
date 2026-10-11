from pathlib import Path

from knowledge_builder.parse_docling import PyMuPDFParser
from knowledge_builder.pipeline import build_pdf


class FailOnceParser(PyMuPDFParser):
    def __init__(self, config):
        super().__init__(config)
        self.calls = []
        self.failed = False

    def parse(self, batch_pdf: Path, global_start_page: int, raw_output: Path):
        self.calls.append(global_start_page)
        if global_start_page == 11 and not self.failed:
            self.failed = True
            raise RuntimeError("intentional")
        return super().parse(batch_pdf, global_start_page, raw_output)


def test_resume_only_retries_failed_batch(synthetic_pdf, config):
    parser = FailOnceParser(config)
    first, report = build_pdf(synthetic_pdf, config, parser=parser, skip_vlm=True, skip_llm=True)
    assert report["batches_failed"] == 1
    assert parser.calls == [1, 11, 21]
    parser.calls.clear()
    second, report = build_pdf(synthetic_pdf, config, parser=parser, skip_vlm=True, skip_llm=True)
    assert parser.calls == [11]
    assert report["valid"]
    assert second["batches"]["batch-00001-00010"]["attempts"] == 1
    assert second["batches"]["batch-00011-00020"]["attempts"] == 2
