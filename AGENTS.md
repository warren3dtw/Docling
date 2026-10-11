# Project conventions

- Run commands with `uv run` and keep `uv.lock` committed.
- Treat `data/input` as read-only. Write intermediates to `data/work` and results to `data/output`.
- Never commit credentials or user PDFs.
- Long PDFs must be processed as bounded page batches. Preserve global 1-based page numbers.
- AI enrichment is opt-in. Never invent summaries or image descriptions when providers are disabled.
- Run `uv run pytest` after code changes.
