# AI Knowledge Base Builder

本機優先、可恢復的 PDF → 結構化 Markdown 處理工具。長文件會先切成真正有界的小 PDF，再逐批解析；輸入 PDF 永遠只讀。預設不呼叫外部 AI，也不會在沒有模型時虛構摘要或圖片說明。

## 快速安裝（npm）

需求：Windows/macOS/Linux、[Node.js 18+](https://nodejs.org/) 與 [uv](https://docs.astral.sh/uv/getting-started/installation/)。不需要預先安裝 Python；`uv` 會自動管理專案使用的 Python 3.12。

```powershell
git clone <你的 GitHub Repo URL>
cd Docling
npm install
npm run doctor
```

`npm install` 會透過 `uv` 建立 `.venv`，並依照已提交的 `uv.lock` 安裝包含 Docling 的完整環境。Docling 首次實際解析時可能另行下載模型權重。

## 使用

將 PDF 放入 `data/input/`，再執行：

```powershell
# 預設離線處理，不呼叫 VLM/LLM
npm run build:kb

# 執行其他 kb 子命令；-- 後方參數會傳給 Python CLI
npm run kb -- resume <document_id>
npm run kb -- validate <document_id>
npm run kb -- index <document_id>
npm run kb -- enrich <document_id>
```

可用 `npm run kb -- --help` 或各子命令的 `--help` 查看選項。預設輸出：

- `data/work/<document_id>/`：小批 PDF、Docling 原始 JSON、逐批結果、可恢復 manifest。
- `data/output/<document_id>/`：章節 Markdown、圖片、`INDEX.md`、`chunks.jsonl`、manifest 與 QA 報告。

`document_id` 由檔名與 PDF SHA-256 前綴組成；輸入內容改變會得到新 ID。重要解析設定也納入快取指紋，避免誤用舊結果。

## 直接使用 uv（開發者）

輕量基礎環境支援 Python 3.11–3.14；Docling 目前請使用 Python 3.11–3.13。

```powershell
# 完整 Docling 環境
uv python install 3.12
uv sync --python 3.12 --extra docling

# 僅安裝可測試的輕量基礎環境
uv sync
uv run kb doctor
```

若暫時不能安裝或下載 Docling，可只執行 `uv sync`，並將 `parsing.engine` 設為 `pymupdf`；此模式可保留文字、嵌入圖片、部分表格與頁碼，但不等同 Docling 的版面辨識品質。

## 設定與資料流

主要設定在 `config/default.yaml`。`processing.pages_per_batch`（預設 10）控制 PDF 解析批次；`max_images_per_vlm_batch`（預設 1）是另一個獨立限制。記憶體不足時先將前者降至 2 或 1。

預設 `vision.enabled: false`、`summary.enabled: false`。離線建置只做可驗證的抽取內容，章節標記為 `pending_enrichment`。OpenAI-compatible 端點（含本機 Ollama 相容端點）透過 `.env` 設定：

```text
OPENAI_COMPATIBLE_BASE_URL=http://localhost:11434/v1
OPENAI_COMPATIBLE_API_KEY=...
VISION_MODEL=實際具視覺能力的模型名稱
SUMMARY_MODEL=模型名稱
```

再將 YAML 的 provider 改為 `openai_compatible` 並啟用。使用遠端端點代表圖片/文字會離開本機；工具只會在使用者明確啟用且配置模型後呼叫。API key 不得提交版控。圖片提示要求只報告可見內容、保留單位並明示不確定性。

## 品質與限制

- QA 報告驗證 frontmatter、圖片連結、JSONL 與批次狀態；它不能替代人工核對技術內容。
- PyMuPDF 表格偵測屬基礎 fallback；複雜版面應使用 Docling 並人工抽驗。
- 圖片過濾會記錄小尺寸與重複原因。向量圖未必是嵌入圖片，第一版不會無限制渲染整頁送給 VLM。
- `chunks.jsonl` 是全文搜尋/embedding 的輸入，不代表已建立向量 RAG。
- 若 Windows 顯示無 Python，仍可由 `uv sync` 下載並管理隔離的 Python。

## 測試

```powershell
npm test
# 或：uv run pytest
```

測試動態建立不含敏感資料的合成 PDF，涵蓋 23 頁分批、全域頁碼、失敗續跑、跨批章節、離線輸出、Markdown/JSONL 驗證與快取失效。合成示例通過不代表任何實際使用者 PDF 已驗證。

亦可執行 `uv run python scripts/create_sample_pdf.py` 建立三頁的 `data/input/sample.pdf`，再用 `parsing.engine: pymupdf` 做手動煙霧測試。

## 授權

本專案採用 [MIT License](LICENSE)，任何人皆可依授權條款使用、修改與散布。
