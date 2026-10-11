# AI Knowledge Base Builder — Codex CLI 開發任務書

> 本文件為可執行工程規格。請 Codex CLI 在目前專案目錄實作、執行測試並報告結果，不要只產出建議或虛擬程式碼。
>
> 使用語言：繁體中文（程式碼、CLI 與必要技術名稱可使用英文）。

## 0. Codex 任務與完成定義

你是一位 Python 文件工程與 AI/RAG 系統開發者。請建立一個**本機優先、可重複執行**的 PDF → 結構化 Markdown 知識庫處理工具。使用者會將一份或多份 PDF 放到 `data/input/`。PDF 可能包含大量頁面、繁體中文/英文混合文字、表格、照片、流程圖、工程技術圖與複雜版面。

你必須：

1. 偵測目前 OS、Python、可用 GPU/VRAM/RAM、系統工具與權限；避免假設一定有 NVIDIA GPU。
2. 建立以 `uv` 管理的 Python 專案與 `.venv`，安裝必需依賴並鎖定版本。
3. 實作 Docling 解析、分批處理、圖片匯出、VLM 描述、LLM 摘要與索引生成。
4. **所有長 PDF 必須以有界頁數批次處理，不得一次將整份 PDF 載入成高解析圖片送入 VLM。**
5. 每一階段有持久化產物、進度紀錄、可恢復執行與錯誤日誌；單一批次失敗不得使其他成功批次的結果消失。
6. 提供可運作的 CLI、配置檔、README、測試與一組小型示例測試資料；不得只寫空的函式或 TODO。
7. 如果 `data/input/` 沒有真實 PDF，建立不包含敏感資料的合成測試 PDF 驗證核心管線；清楚報告「示例通過」不等於「實際 PDF 已驗證」。
8. 若 VLM/LLM API key 不存在，不可捏造圖片內容或摘要；允許以 `--skip-vlm`、`--skip-llm` 或明確標示的待處理狀態完成可驗證的離線基礎流程。
9. 最終回報已建立的檔案、安裝與測試結果、實際處理頁數、失敗項目、未配置服務及後續使用指令。

### 不在第一階段範圍內

- 不需先製作 Web UI、聊天介面或雲端部署。
- 不需先安裝向量資料庫；先完成高品質 Markdown 與可搜尋索引，之後再加入 RAG。
- 不可自行上傳使用者 PDF 到外部服務。預設 VLM/LLM 為停用或本地模式；若要啟用雲端 provider，先以文件明確揭露資料流與設定方法，僅在使用者已配置並啟用時呼叫。

## 1. 系統架構

```text
data/input/*.pdf
       │
       ▼
[PDF 掃描 / 頁數、雜湊、書籤、原始文字檢查]
       │
       ▼
[頁面分批：預設 10 頁/批；保留全域頁碼映射]
       │
       ▼
[Docling 標準解析 → 結構化中間資料、文字、表格、圖片]
       │                         │
       │                         ▼
       │                [圖片分類 / VLM 圖片描述]
       │                         │
       └───────────┬─────────────┘
                   ▼
        [段落/標題/圖文關聯重建]
                   ▼
        [LLM 摘要與搜尋中繼資料]
                   ▼
        [依章節輸出 Markdown + images/]
                   ▼
        [INDEX.md + manifest + 搜尋用 chunks.jsonl]
                   ▼
        [QA 驗證與來源追蹤]
```

**原則：Docling 是解析工具，不是完整的知識庫品質保證。** LLM/VLM 負責增強內容；程式必須保留 Docling 原始中間結果，讓不正確的 AI 描述可以被重新產生，不必重跑 PDF 解析。

## 2. 建議工具與職責

| 工具 | 作用 | 重要程度 |
|---|---|---|
| Python 3.11+（依相容版本選擇）+ uv | 執行、安裝與鎖定依賴 | 必要 |
| Docling | PDF 解析、版面/表格/圖片提取，結構化輸出 | 必要 |
| PyMuPDF (`pymupdf`) 或 `pypdf` | 頁數檢查、頁碼映射、按頁拆分/讀取 | 必要（擇一並說明） |
| Pydantic + PyYAML | 配置與 metadata 結構驗證 | 必要 |
| Typer | CLI 命令 | 建議 |
| Pillow | 圖片檢查、尺寸/格式轉換與預處理 | 建議 |
| VLM provider adapter | 圖片描述，支援 local / remote 的可替換介面 | 必要介面；模型可選 |
| LLM provider adapter | 章節摘要、關鍵字、搜尋問題與交叉參照 | 必要介面；模型可選 |
| Docling HybridChunker | 索引/向量檢索用切塊 | 第二階段或可選 |
| pytest | 單元、整合、恢復執行測試 | 必要 |
| SQLite（標準庫）或可原子寫入 JSON manifest | 執行狀態與失敗恢復 | 必要（擇一） |
| Chroma / SQLite FTS5 / BM25 | 後續檢索引擎 | 第二階段 |

安裝時核對官方最新 API，使用實際可用的 Docling 選項，不得根據過時範例硬編 API。尤其 VLM 全頁解析管線與「只對圖片生成描述」是兩個不同用途：**先採標準 Docling PDF pipeline，再針對提取出的圖片呼叫 VLM**，除非實測證明整頁 VLM 對特定頁型有優勢。

官方參考：
- Docling：https://github.com/docling-project/docling
- Docling CLI：https://docling-project.github.io/docling/reference/cli/
- Docling Pipeline Options：https://docling-project.github.io/docling/reference/pipeline_options/
- Docling 文件切塊：https://docling-project.github.io/docling/concepts/chunking/
- uv：https://docs.astral.sh/uv/

## 3. 專案結構（目標）

```text
ai-knowledge-base/
├── AGENTS.md                  # Codex 專案執行約定
├── README.md                  # 安裝、設定、範例、故障排除
├── pyproject.toml
├── uv.lock
├── .env.example               # 僅放變數名稱，不放密鑰
├── .gitignore
├── config/
│   └── default.yaml
├── data/
│   ├── input/                 # 使用者自行放入 PDF
│   ├── work/                  # 批次 PDF、Docling JSON、中間資料、manifest
│   └── output/
│       └── <document_id>/
│           ├── README.md     # 文件級摘要、目錄與概念導覽
│           ├── INDEX.md      # 可搜尋章節清單、關鍵字與定位
│           ├── chapters/     # 依章節輸出的 Markdown
│           ├── images/       # 圖片檔，Markdown 使用相對路徑
│           ├── chunks.jsonl  # 未來全文檢索 / embedding 的輸入
│           ├── manifest.json # 處理版本、頁碼、來源、狀態
│           └── qa_report.json
├── src/knowledge_builder/
│   ├── cli.py
│   ├── config.py
│   ├── pdf_scan.py
│   ├── batching.py
│   ├── parse_docling.py
│   ├── image_extract.py
│   ├── vlm.py
│   ├── llm.py
│   ├── chapter_assembly.py
│   ├── markdown_export.py
│   ├── index_build.py
│   ├── state.py
│   └── quality.py
└── tests/
    ├── test_batching.py
    ├── test_resume.py
    ├── test_page_mapping.py
    ├── test_markdown.py
    └── test_pipeline.py
```

如 repo 已存在其他檔案，請在不覆寫使用者原始文件的情況下調整結構。忽略 `.env`、`data/input/`、`data/work/` 等敏感或大型產物；是否追蹤 `data/output/` 交由使用者設定。

## 4. 設定檔與預設值

建立 `config/default.yaml`，至少支援以下語意（可依實際 SDK 調整欄位名稱並在 README 解釋）：

```yaml
input_dir: data/input
work_dir: data/work
output_dir: data/output
processing:
  pages_per_batch: 10
  max_workers: 1
  continue_on_error: true
  retries: 2
  resume: true
  preserve_intermediate: true
  image_max_long_edge: 1600
  image_max_pixels: 4000000
  min_image_width: 80
  min_image_height: 80
  max_images_per_vlm_batch: 1
parsing:
  engine: docling
  pipeline: standard
  ocr: auto
  language_hints: [zh-TW, en]
  export_structured_json: true
  preserve_tables: true
  preserve_images: true
vision:
  enabled: false
  provider: none               # 可擴充為 local_ollama / openai_compatible 等
  model: null
  timeout_seconds: 120
  retries: 2
  describe_diagrams: true
  describe_photos: true
  describe_charts: true
  include_neighbor_text: true
summary:
  enabled: false
  provider: none
  model: null
  max_input_tokens_per_call: 6000
  language: zh-TW
output:
  split_strategy: headings_with_page_fallback
  fallback_pages_per_file: 10
  create_document_index: true
  create_chunks_jsonl: true
  markdown_image_links: relative
  preserve_source_page_numbers: true
```

**重要**：頁面批量與 VLM 圖片批量是兩個獨立參數。預設逐批解析 PDF、逐張描述圖片，避免 CPU/GPU/VRAM 峰值疊加。若記憶體不足，允許使用者把 `pages_per_batch` 改為 2、甚至 1，或改用低解析度。

## 5. 大型 PDF 批次處理（必做）

### 5.1 切分與頁碼

1. 取得 PDF 頁數與檔案 SHA-256，生成穩定 `document_id`。
2. 使用全域 **1-based 頁碼**；例如 83 頁，10 頁/批 → 1–10、11–20、…、81–83。
3. 可選擇將每批存為暫存 PDF 再交給 Docling，或在確認 Docling SDK 支援的情況下直接傳入頁面範圍；實作必須確保每批是真正的有界轉換。
4. 各批中 Docling 的局部頁碼，必須轉換成原始文件的全域頁碼；圖片、表格、段落與章節也要正確映射。
5. **章節可能跨越批次**，不可把批次邊界誤認成章節邊界。先保存逐批結構結果，再依標題層級、書籤與頁面上下文合併章節。
6. 對跨批段落/表格採去重與接續判斷；資訊不足時標示需 QA，不要無聲合併或刪除。

### 5.2 續跑、重試、交易性寫入

- 每批記錄 `pending/running/succeeded/failed`、頁數範圍、耗時、解析版本、輸出檔雜湊、錯誤資訊。
- 每成功批次即安全落盤（先寫暫存檔、校驗後原子替換），不要等全部 PDF 處理完才寫入。
- 程式重啟時檢查 PDF hash、設定指紋、工具版本與中間結果，只有**可重用且完整**的成功批次可以略過。
- 能單獨重試失敗批次、失敗圖片與失敗摘要；支援 `--force` 重跑。
- 任何失敗批次不得被默默當成成功；最後輸出應能反映完整/部分成功狀態。
- 不要把整個 PDF 的全部頁面影像長期保存在 RAM。
- 限制暫存檔/日誌成長；不得在未驗證輸出前刪除原始中間結果。

## 6. VLM 圖片處理（必做）

### 6.1 擷取策略

- 優先擷取 Docling 辨識的插圖、照片、圖表、示意圖，保留**圖片本體與來源區域**。
- 一些工程圖並非獨立嵌入圖片，而是 PDF 向量圖形；若 Docling 無法抽出可用圖片，允許以定位框裁切/渲染原始 PDF 區域；必要時使用低/中解析度頁面視覺 fallback。
- 允許過濾過小裝飾圖、重複 Logo；不要誤把重要的小型技術符號過濾掉。過濾記錄需可稽核。
- 圖檔以穩定 ID 儲存：`p0023_fig003.png`，不要只用非唯一的序號。
- 圖片數量多時，VLM 以單張或小批次、有限並行處理，完成即儲存描述；不得對失敗圖片輸出虛構描述。

### 6.2 圖片描述輸出結構

每張圖片至少紀錄：

```yaml
image_id: p0023_fig003
source_document: example.pdf
source_page: 23
image_path: ../images/p0023_fig003.png
image_type: engineering_diagram
caption_original: "原始 PDF 若有圖說，保留原文"
caption_vlm: "VLM 所描述的可見內容；不得推測不可辨識尺寸"
visible_text: ["OCR/VLM 辨識出的標註文字"]
nearby_section: "3.2 Connection Details"
search_terms: ["連接件", "節點", "CLT"]
confidence_note: "圖上尺寸不清楚，需人工核對"
processing_status: succeeded
```

VLM 提示必須強調：**區分觀察與推論**、只描述看得見的圖面、保留技術文字與單位、不要捏造構件型號/長度/受力/數量；若為表格或圖表，優先提取標籤、單位與可辨識數據，無法判讀則說明限制。將圖片前後文字作為上下文，但不能拿上下文替代對圖片的實際觀察。

### 6.3 Provider 設計

實作 `VisionProvider` 介面（至少 `describe(image, context) -> structured_result`），支援無模型時的 `disabled` provider 與至少一種**可實際配置、可測試**的本機或 OpenAI-compatible provider。切勿把模型名稱、API key 或端點寫死。

- 本機模式可考慮 Ollama 的視覺模型；需先檢查選定模型是否真有 vision 能力。
- 使用雲端時由 `.env` 注入認證、端點及模型，遵守速率限制、逾時、重試與成本限制。
- 不得把整頁高解析度圖直接無上限送入模型；支持縮圖及必要時局部裁切。

## 7. AI 摘要與 AI 可搜尋 Markdown（必做）

**AI 摘要不可改寫或覆蓋原始技術內容。** 每份章節 Markdown 最上面要有 YAML frontmatter；正文仍保留忠實的 PDF 內容、表格、圖片連結與來源位置。

建議格式：

```markdown
---
document_id: example-sha256prefix
chapter_id: ch-003
source_file: example.pdf
source_pages: [21, 22, 23, 24]
title: "3. Connections"
summary: "本章介紹連接件配置、安裝條件及對應圖示。"
keywords: ["CLT", "連接件", "節點"]
search_questions:
  - "如何找到連接件的安裝方式？"
  - "哪個章節包含節點圖？"
related_chapters: ["ch-002", "ch-004"]
images: ["p0023_fig003"]
processing_status: verified
---

# 3. Connections

> 來源：example.pdf，原始 PDF 第 21–24 頁。

## 本章摘要

...

## 原始內容

保留從 PDF 忠實轉錄、經結構整理的內文。

![原圖說或替代文字](../images/p0023_fig003.png)

**圖片 AI 描述**：...（明確標記為 AI 產生）

## 相關章節

- [上一章](ch-002.md)
```

如果 LLM 未設定，不得偽造 `summary`、`search_questions` 或 `verified` 狀態；改用可驗證的抽取式標題、索引詞，並標註 `pending_enrichment`。摘要應可重新生成，並保留模型版本/提示版本以供追蹤。

### 索引策略

- 每份 PDF 產生 `README.md`：文件簡介、章節目錄、已知問題與資料完整性。
- 產生 `INDEX.md`：每章標題、真實摘要（若存在）、關鍵字、可回答問題、頁數範圍與 Markdown 相對連結。
- 產生 `chunks.jsonl`：每行一個區塊，欄位至少包含 `chunk_id`、`document_id`、`chapter_id`、`text`、`headings`、`page_numbers`、`image_ids` 和 `source_path`。將來用於全文搜尋或 embedding。
- 不要硬依每 N 字元截斷技術表格；優先保留標題、段落與表格語意，token 過長時再分塊。
- 第一版的「AI 可快速索引」由 Markdown 索引與 JSONL 提供；**不等同於已完成 RAG 向量檢索**。

## 8. CLI 操作方式（必做）

使用 `uv run` 啟動。實際指令名稱由實作決定，README 必須提供下列等效操作：

```bash
# 檢查環境與可用模型（不需 API key）
uv run kb doctor

# 處理 data/input 裡的 PDF，離線模式先完成解析
uv run kb build --input data/input --config config/default.yaml --skip-vlm --skip-llm

# 配好模型後，補做圖片理解與知識增強（不應重跑已成功的 PDF 解析）
uv run kb enrich --document <document_id>

# 失敗後續跑
uv run kb resume --document <document_id>

# 驗證結果與來源頁數
uv run kb validate --document <document_id>

# 只重建索引
uv run kb index --document <document_id>
```

CLI 需提供 `--help`，輸入路徑不存在或模型不可用時提供人類可理解的錯誤訊息。

## 9. 品質驗證與測試（必做）

請自行實作 pytest 測試，涵蓋：

1. 23 頁 PDF / 每批 10 頁 → 預期 3 批（1–10、11–20、21–23）。
2. 第二批故意失敗後重啟：第一、三批不得重跑；第二批能重試。
3. 第 11 頁圖片與表格，不可錯標成第 1 頁。
4. 同一章跨越第 10/11 頁，可被合成同一章節或產生明確關聯，不能悄悄遺失內容。
5. PDF 有文字、圖片、表格：輸出必須保留可追溯的文字、圖檔、表格與來源頁碼。
6. 關閉 VLM/LLM 時，系統仍可完整執行基礎解析，不產生假摘要或假圖片描述。
7. 模型請求逾時、回傳非 JSON、速率限制，應有重試與可讀的失敗資訊。
8. Markdown frontmatter 可解析、內部圖片連結有效、INDEX 路徑有效、JSONL 每行可解析。
9. 同一 PDF 同一設定重跑應能略過成功工作，不產生重複圖片或章節。
10. 來源 PDF 發生變更或重要解析參數改變時，不得錯誤沿用舊快取。

產生 `qa_report.json` 與終端摘要，至少包含：`pages_total`、`pages_parsed`、`batches_succeeded`、`batches_failed`、`images_extracted`、`images_described`、`images_pending`、`chapters_created`、`broken_links`、`warnings`。成功率不得以「程式未報錯」冒充內容正確性；保留人工抽驗清單。

## 10. 實作順序

### Phase 1 — 先完成能跑通的離線 MVP

- 初始化 repo、uv、依賴、配置、CLI、文件。
- PDF 掃描與 10 頁批次切分。
- Docling 分批解析並保存原始結構化結果。
- 文字、表格、圖片、全域頁碼提取。
- 失敗續跑、章節組合、Markdown/INDEX/JSONL 匯出。
- 建立整合測試並實際執行。

### Phase 2 — VLM 圖片理解

- 提供 VLM provider abstraction 與可配置的本機/相容服務。
- 支援圖像截取、圖片上下文、圖片描述、結果快取與重試。
- 寫入獨立圖像 metadata，將 AI 描述插入章節 Markdown。
- 增加 VLM mock 測試，不以真實 API 支出作為 CI 前提。

### Phase 3 — 摘要與檢索增強

- 提供 LLM adapter、結構化輸出驗證、章節摘要與搜尋問題。
- 生成 README/INDEX、關聯章節與 chunks.jsonl。
- 可選 Docling HybridChunker；後續才整合 SQLite FTS5 / Chroma / reranker。

### Phase 4 — 品質、效能與操作體驗

- 測試 100+ 頁 PDF，觀察每批 RAM/VRAM 峰值、速度與中斷恢復。
- 依環境調整批次大小，提供配置範例與效能紀錄。
- 完善失敗重試、長文件 QA 與診斷指令。

## 11. 交付與驗收

僅在以下條件達成時，才宣稱本次開發完成：

- [ ] 具備可重現的 `uv sync` 安裝與 `uv run kb doctor`。
- [ ] 在有/無 GPU、無 API key 的情況下，基礎解析流程有清楚且可用的路徑。
- [ ] 能分批處理長 PDF，保存進度，中斷後繼續。
- [ ] 圖片可匯出；VLM 已配置時可真正產生圖片描述。
- [ ] Markdown 有標題、來源頁碼、內容、相對圖片路徑、可搜尋 metadata。
- [ ] INDEX.md、chunks.jsonl 與 QA 報告可生成並驗證。
- [ ] 至少完成合成資料的端到端測試，並列出通過與失敗的測試。
- [ ] 未配置 LLM/VLM 時，不虛構結果或宣稱視覺理解已完成。
- [ ] 實際 PDF 若存在，至少成功處理一份並提供輸出位置。

## 12. Codex 工作約定

1. 先檢查專案目錄、Git 狀態與系統工具，避免覆蓋現有檔案。
2. 在完成檢查後直接著手實作；僅在不可逆操作、資安風險、API 成本或必需憑證等情況才要求使用者介入。
3. 如發現重大套件相容問題，可替換相似工具，但必須記錄原因及差異。
4. 不要把 API key 寫在程式、README 或 git tracked 檔案。
5. 對輸入 PDF 採唯讀，任何中間或輸出檔寫到 `data/work`、`data/output`。
6. 網路安裝或下載模型失敗時，保留可運作的部分、列出阻礙與精確的恢復步驟，不要宣稱已安裝成功。
7. 不要執行耗資源的整本 VLM 任務作為首次測試；優先使用 1–3 頁與 mock provider，再擴大到多批測試。
8. 每完成一個 Phase 執行對應測試，最終回報具體測試輸出與未達成的要求。

---

**優先級總結：** 可靠分批解析 + 原始圖片保留 + 全域頁碼正確 + 失敗續跑 > 圖像理解與摘要 > 向量資料庫與聊天介面。第一版必須先把原始知識保存正確，AI 增強功能才有意義。
