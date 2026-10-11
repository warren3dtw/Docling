# Changelog

本文件採用 [Keep a Changelog](https://keepachangelog.com/zh-TW/1.1.0/) 的分類概念；版本仍由 `pyproject.toml` 管理。

## [Unreleased]

### PDF pipeline grounding

- 新增逐頁 PDF preflight profile、路由建議與四態品質記錄。
- 新增雜湊驗證的本機來源 PDF 副本、bounded 全頁 WebP 與逐頁結構化 JSON。
- 新增 Markdown 來源頁面連結、逐頁資產／狀態 QA 與 PDF pipeline audit。
- PDF 流程改為在章節 Markdown 前先保存逐頁來源與抽取記錄；失敗 batch 不再只留下 batch 層級錯誤。
- 設定新增 `native_text_min_chars`、`page_image_dpi` 與 `preserve_page_images`；既有 frontmatter、manifest 與 `chunks.jsonl` 欄位保持相容。

### Documentation workflow

- 新增規則：規則、流程、功能、內容與 App 操作變更必須同步維護 Markdown 與 HTML。
- 新增 `PROJECT_STATUS.md`／`.html`，集中呈現目前階段、進度、操作方式、驗證與限制。
- 新增 `DOCUMENTATION_POLICY.md`／`.html`，定義雙格式文件的內容與驗證要求。
- 新增 86 頁實際 PDF 的 Markdown／HTML 驗證報告，記錄 QA、resume、效能與 Windows console 編碼問題。
- 閱讀用 Markdown 預設整併為單一 `DOCUMENT.md`；超過設定頁數上限才輸出 `PART-*.md`，`chunks.jsonl` 保持語意章節粒度。

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
