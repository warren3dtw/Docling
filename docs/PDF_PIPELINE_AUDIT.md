# PDF Pipeline Audit

## Environment and inspected files

Audit date: 2026-10-11.

Inspected the repository guidance, `README.md`, `pyproject.toml`, `config/default.yaml`, all modules under `src/knowledge_builder/`, the test suite, and the target design in `pdf-knowledge-ingestion/`. No user PDF contents, credentials, or environment secrets were read. `data/output` contained no prior sample output at the start of this audit, so quality claims are limited to generated test fixtures.

## Current workflow (observed)

The implemented flow is:

`input PDF -> SHA-256/source copy -> per-page preflight -> bounded page rendering -> physical PDF batches -> Docling/PyMuPDF -> batch checkpoints -> per-page JSON/quality state -> chapter assembly -> Markdown/source-page links -> indexes/QA`

Evidence:

- `src/knowledge_builder/pipeline.py:23` orchestrates the flow; source preservation and preflight occur at lines 29-30, page rendering near line 57, and per-page records before Markdown at line 128.
- `src/knowledge_builder/pdf_scan.py:40` creates bounded physical PDFs with 1-based inclusive page ranges.
- `src/knowledge_builder/state.py:40` only reuses a completed batch when its result hash matches.
- `src/knowledge_builder/page_grounding.py:22` preserves a hash-checked source copy; line 37 profiles pages; line 105 renders one page at a time; line 173 writes page records.
- `src/knowledge_builder/markdown_export.py:46` adds links from curated Markdown to the original page image.
- `src/knowledge_builder/quality.py:45` enforces the allowed page statuses and validates records/assets.

## Gap matrix

| ID | Status | Evidence / observed behavior | Severity and next action |
|---|---|---|---|
| P0-01 page/file profiling | partial | `page_grounding.py:37` measures native text, embedded images, vector drawings and image coverage, then recommends a route. Docling `ocr: auto` only enables OCR for a batch containing an image-backed low-text page; independent per-page queues are not implemented. | P0: introduce route-specific batch queues after representative evaluation. |
| P0-02 source + SHA provenance | implemented | `pipeline.py:29`, `page_grounding.py:22`; copied source hash is verified. | Keep source local and ignored by Git. |
| P0-03 stable identifiers | implemented | `pdf_scan.py` derives document ID from filename plus source hash; all page records use 1-based page numbers. | Add migration only if the ID algorithm changes. |
| P0-04 page image preservation | implemented | `page_grounding.py:105` renders every page one at a time with edge/pixel bounds. | Validate DPI on real diagrams. |
| P0-05 OCR for image-only pages | partial | `parse_docling.py` enables Docling OCR selectively for image-backed low-text batches; PyMuPDF records `ocr_unavailable_with_pymupdf`. No real scanned fixture establishes OCR quality. | P0: add a labeled scan fixture/evaluation. |
| P0-06 per-page JSON | implemented | `page_grounding.py:173`; records are written atomically to work and output before Markdown. | Schema is additive under manifest v1. |
| P0-07 failed/partial tracking | implemented | Every source page receives `success`, `partial`, `failed`, or `skipped_with_reason`; covered by `tests/test_resume.py:23`. | Keep failures visible in QA. |
| P0-08 checkpoints/retries | implemented | Physical batches, attempts, atomic manifest writes, output hashes and selective retry are present; tested in `tests/test_resume.py:23`. | Process-level interruption during an individual parser call remains engine-dependent. |
| P0-09 low-quality detection | partial | Empty visual pages, very short text, replacement characters and extreme repeated characters are flagged. | Tune thresholds against 10-30 representative pages. |
| P0-10 exact number/unit policy | partial | Numeric values with common units receive `numeric_spec_requires_review`; no facts are promoted as verified automatically. | Expand units/locales and add human approval workflow. |
| P0-11 source page citations | implemented | Chapter Markdown links each included page to `pages/page_NNNN.webp`; links are checked by QA. | Consider optional PDF deep links in a viewer. |
| P1-01 diagram VLM escalation | partial | Embedded images can be enriched through opt-in VLM, and diagram-like pages are profiled. Full-page targeted VLM routing is not implemented. | Benchmark local/authorized providers first. |
| P1-02 table checks | partial | Docling tables and PyMuPDF `find_tables` are preserved, but header/value verification is absent. | Add labeled table assertions. |
| P1-03 topic synthesis | partial | `chapter_assembly.py:6` joins across batch boundaries by headings/fallback windows. This is not semantic topic curation. | Add source-grounded topic synthesis only after evaluation. |
| P1-04 model/settings log | partial | Per-page JSON records parser, OCR setting and VLM model. Prompt/version hashes are absent. | Record provider and prompt revision when providers are used. |
| P1-05 hardware/memory limits | partial | Physical batching and one-page-at-a-time bounded rendering prevent full-document rasterization. There is no live memory guard; `max_workers` is not used. | Add measured memory/runtime reporting. |
| P1-06 broken-link checks | implemented | `quality.py:12` checks image and ordinary relative Markdown links plus page assets. | Retain as a release gate. |
| P1-07 duplicate detection | partial | Embedded-image binary deduplication exists; chapter parts use exact text deduplication. Cross-page boilerplate detection is absent. | Add evidence-preserving duplicate annotations. |
| P1-08 prompt injection isolation | not_found | No explicit document-instruction boundary exists in provider prompts. | Required before remote or local generative synthesis is trusted. |
| P1-09 config-driven routing | partial | Thresholds and route recommendations are configurable, and Docling auto-OCR is selected per physical batch; independent OCR/VLM page queues are absent. | Convert recommendations to explicit queues after baseline evaluation. |
| P2-01 retrieval evaluation | partial | `chunks.jsonl` includes document/chapter/page provenance, but no vector store or retrieval evaluation exists. | Evaluate keyword search first, then embeddings. |
| P2-02 image similarity | not_found | No image embedding/search implementation. | Add only if measured benefit justifies it. |
| P2-03 review interface | not_found | Warnings are machine-readable, but there is no approve/edit/reject UI. | Add after page records stabilize. |

## Sample failures and root causes

- Image-only pages under the PyMuPDF fallback cannot be OCRed. They are now preserved and marked `partial` instead of silently becoming empty Markdown.
- A failed parser batch previously existed only at batch level. It now creates a `failed` record for every affected global page so pages cannot silently disappear.
- Raw Markdown previously cited page numbers only as text. It now links to preserved page images, and QA fails on broken relative links.
- Numeric-looking technical content is not automatically considered verified; it is flagged for review. This is a conservative heuristic, not numeric validation.

## P0/P1/P2 roadmap

1. P0: run a privacy-safe, labeled 10-30 page evaluation containing native text, scan, diagram and table pages; tune profile and quality thresholds.
2. P0: turn the recorded route recommendation into true page/batch dispatch, especially OCR-only and visual-review queues.
3. P1: add table alignment verification, prompt-injection boundaries, model/prompt version logging, and runtime/peak-memory metrics.
4. P1: add source-grounded topic curation while retaining raw per-page records.
5. P2: evaluate keyword retrieval with page citations before adding text or image embeddings and a review UI.

## Proposed minimal change

The first P0 increment is implemented in:

- `src/knowledge_builder/page_grounding.py`
- `src/knowledge_builder/pipeline.py`
- `src/knowledge_builder/markdown_export.py`
- `src/knowledge_builder/quality.py`
- `src/knowledge_builder/config.py`
- `config/default.yaml`
- `tests/test_page_grounding.py`

It preserves existing frontmatter and `chunks.jsonl` fields. Manifest additions (`page_profiles`, `page_images`, and `pages`) are backward-compatible fields under schema version 1.

## Tests performed / not performed

- `uv run pytest`: 11 tests passed after implementation.
- Synthetic tests cover 23-page physical batching, 1-based global page mapping, resume/retry, source hashing, native/image-only/blank profiles, page images, per-page states, numeric-review flags, Markdown links and JSONL validity.
- Not performed: accuracy evaluation against a real OCR scan, a dense engineering table, a technical exploded view, or a 200+ page document; no external AI provider was enabled.

## Risks, privacy and open questions

- Page-type rules are deterministic heuristics and need calibration on representative, non-confidential samples.
- Enabling a remote OCR/VLM/LLM provider can send page images and text off the machine. It must remain an explicit user choice after a privacy review.
- Page WebP files add disk usage. DPI and pixel bounds should be benchmarked against readability and storage.
- Technical numbers remain unverified until a human or a purpose-built verification stage approves them.
