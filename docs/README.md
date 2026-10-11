# AI Knowledge Base Builder 文件

本專案把 PDF 以有界批次解析成可追溯的 Markdown、圖片、全文 chunks、manifest 與 QA 報告。預設流程完全離線；VLM/LLM enrichment 必須由使用者明確啟用。

## 技術棧

| 類別 | 技術 |
|---|---|
| 執行環境 | Python 3.11–3.14；Docling 建議 Python 3.12 |
| CLI / 設定 | Typer、Pydantic、PyYAML、python-dotenv |
| PDF | Docling（可選完整解析）、PyMuPDF（fallback 與分批）、Pillow |
| AI provider | OpenAI-compatible HTTP API，預設停用 |
| 測試 / 套件 | pytest、uv、npm scripts |

## 快速開始

```powershell
npm install
npm run doctor
npm test

# 將 PDF 放入 data/input 後執行離線建置
npm run build:kb
```

若只需輕量環境：

```powershell
uv sync
uv run kb doctor
```

## 常用指令

| 指令 | 用途 |
|---|---|
| `npm run doctor` | 檢查 Python、硬體、Docling 與 provider 設定，不呼叫模型 |
| `npm run build:kb` | 從 `data/input` 離線批次建置知識庫 |
| `npm run kb -- resume <id>` | 續跑失敗或缺漏批次 |
| `npm run kb -- validate <id>` | 驗證輸出與批次完整性 |
| `npm run kb -- index <id>` | 從既有解析結果重建輸出與索引 |
| `npm run kb -- enrich <id>` | 執行已明確啟用的 enrichment |
| `npm test` | 執行 pytest 測試套件 |

## 文件索引

| 文件 | 內容 |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 模組責任、資料流、狀態與輸出契約 |
| [DEVELOPMENT.md](DEVELOPMENT.md) | 開發流程、命名、環境變數與安全規範 |
| [FEATURES.md](FEATURES.md) | 已完成能力、限制與行為 |
| [TESTING.md](TESTING.md) | 9 項測試、fixtures 與新增測試方式 |
| [CHANGELOG.md](CHANGELOG.md) | 專案變更紀錄 |
| [plans/README.md](plans/README.md) | 計畫建立與歸檔流程 |

AI 開發入口為根目錄 `AGENTS.md`（Codex）與 `CLAUDE.md` / `.claude/`（Claude Code）。
