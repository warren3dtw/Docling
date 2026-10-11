# CLAUDE.md

## 專案概述

AI Knowledge Base Builder 是 Python 3.11–3.14、Typer、Pydantic、PyMuPDF 與可選 Docling 組成的本機優先 PDF → Markdown CLI。它以有界批次處理長文件，可續跑，預設不呼叫外部 AI。

## 常用指令

```powershell
npm install
npm run doctor
npm test
npm run build:kb
uv run kb --help
```

所有 Python 指令使用 `uv run`；依賴由 `uv.lock` 固定。

## 關鍵規則

- `data/input` 唯讀；中間產物與結果分別放在 `data/work`、`data/output`。
- PDF 必須以實體有界批次處理，並保留原始 PDF 的 1-based 全域頁碼。
- 續跑、快取指紋、manifest 與原子寫入語意不可意外破壞。
- VLM/LLM 僅在明確啟用後執行；停用時不得產生推測性內容。
- 不提交 PDF、真實 `.env`、憑證、快取或輸出。
- 功能計畫放在 `docs/plans/`，完成後歸檔到 `docs/plans/archive/`。

## 詳細文件

- `docs/README.md` — 專案入口、技術棧與指令
- `docs/ARCHITECTURE.md` — 模組責任、資料流與輸出契約
- `docs/DEVELOPMENT.md` — 開發規範、環境變數與計畫流程
- `docs/FEATURES.md` — 功能狀態與行為
- `docs/TESTING.md` — 9 項測試與新增測試指南
- `docs/CHANGELOG.md` — 變更紀錄
- `docs/plans/README.md` — User Story → Spec → Tasks → Archive 流程

## 完成條件

- 程式變更後執行 `uv run pytest`。
- 檢查 `git diff --check`，並確認沒有敏感檔案或使用者資料進入差異。
- 行為或設定變更要同步相關文件。
- Git push 由使用者明確授權；repo-local `git-commit` agent 只 commit、不 push。
