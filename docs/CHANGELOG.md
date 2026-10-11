# Changelog

本文件採用 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 的分類概念；版本仍由 `pyproject.toml` 管理。

## [Unreleased]

### Added

- 新增根目錄與 scoped `AGENTS.md`，提供 Codex 專案及目錄層級規範。
- 新增 `CLAUDE.md`、六組 Claude rules、低干擾安全 hooks 與七個 repo-local subagents。
- 新增繁體中文架構、開發、功能、測試、計畫流程與變更紀錄文件。
- 歸檔初始 AI 開發文件計畫。

### Changed

- README 增加 AI 開發文件與 Claude Code 入口。

### Compatibility

- PDF 管線、公開 CLI、manifest、Markdown 與 JSONL 格式沒有變更。

## [0.1.0]

### Added

- 本機優先、可恢復的 PDF → Markdown 管線。
- Docling/PyMuPDF 解析、圖片抽取、可選 OpenAI-compatible enrichment、索引與 QA。
- 九項離線 pytest 測試。
