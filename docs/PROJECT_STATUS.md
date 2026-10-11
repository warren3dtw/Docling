# 專案狀態總覽

- 最後更新：2026-10-11
- 目前階段：P0 可追溯管線與 86 頁實際文件 smoke validation 已完成，進入品質校準與效能改善階段
- 最近驗證：86 頁實際 PDF QA `valid: true`；最新程式變更以實際 PDF resume／validate 驗證。此前完整測試為 11 項通過。
- 預設模式：完全離線；VLM／LLM enrichment 為 opt-in

## 階段進度

| 階段 | 狀態 | 說明 |
|---|---|---|
| 專案基礎與 CLI | 已完成 | 安裝、doctor、build、resume、validate、index、enrich 指令已建立 |
| 有界 PDF 分批與續跑 | 已完成 | 實體小 PDF、全域 1-based 頁碼、原子 manifest、失敗 batch 重試 |
| 逐頁來源追溯 | 已完成 | 來源 SHA-256、副本、page profile、完整頁面 WebP、逐頁 JSON |
| Markdown 與 QA | 已完成 | 章節、frontmatter、來源頁連結、chunks、manifest、QA 報告 |
| Markdown 文件數量 | 已調整 | 100 頁內輸出單一 `DOCUMENT.md`；更大文件最多每 100 頁分段 |
| OCR／路由品質校準 | 下一階段 | 需以經授權的掃描、表格與技術圖代表頁校準規則和品質 |
| Topic synthesis／檢索評估 | 尚未開始 | 先完成 source-grounded baseline，再評估語意檢索與多模態能力 |
| 人工審核介面 | 尚未開始 | 目前只有 machine-readable warnings，尚無 approve/edit/reject UI |

## 已完成內容

- 長 PDF 依 `pages_per_batch` 切成有上限的實體小 PDF。
- 所有對外頁碼保持原 PDF 的 1-based 全域頁碼。
- PDF 來源以 SHA-256 識別，並在 work 目錄保存雜湊驗證副本。
- 每頁建立 profile、建議路由、bounded WebP、逐頁 JSON 與品質警告。
- Docling `ocr: auto` 只在 batch 含低文字量影像頁時啟用 OCR。
- 失敗或低品質頁面具有明確狀態，不會無聲消失。
- Markdown 可點回來源頁影像；QA 驗證頁面覆蓋、資產、frontmatter、JSONL 與連結。
- VLM／LLM 預設停用；停用或失敗時不捏造摘要、問題或圖片描述。
- 規則、流程、功能、內容與操作文件開始採 Markdown／HTML 雙格式維護。
- 已以 `data/input` 的 86 頁影像型 PDF 完成離線流程：9/9 batches、86/86 page records、86/86 page images、0 broken links，QA 通過。
- 實際 resume 未增加任何 batch attempt，證明成功解析結果可重用。
- 86 頁 PDF 已重新匯出：只有 `DOCUMENT.md`、`INDEX.md`、`README.md` 三份 Markdown；64 個語意章節仍保留在同檔錨點及 `chunks.jsonl`。

## 最近實際 PDF 驗證

- 文件狀態：`partial`；83 頁 success、3 頁 partial、0 failed。
- 3 個 partial 頁（71、78、86）皆為以照片為主、幾乎沒有文字的頁面；完整來源影像已保留。
- 產生 64 章、64 chunks、151 張抽取圖片；VLM 停用，所以沒有圖片描述。
- 9 個 batch 累計解析 696.87 秒；resume 37.61 秒且沒有重跑 batch。
- 詳細結果：[Markdown](validation/2026-10-11-real-pdf-validation.md)／[HTML](validation/2026-10-11-real-pdf-validation.html)。
- 整併後 `DOCUMENT.md` 為 91,889 bytes；QA `valid: true`，0 broken links。
- 每 batch 抽樣顯示主要文字多數可讀，但頁 11、61 有產品標題／代碼 OCR 錯誤且未被品質規則攔截；`QA valid` 目前只代表結構完整，不代表內容準確。

## App 操作方式

### 安裝與環境檢查

```powershell
npm install
npm run doctor
```

完整 Docling 環境也可使用：

```powershell
uv sync --python 3.12 --extra docling
uv run kb doctor
```

### PDF 轉 Markdown

1. 將 PDF 放入 `data/input/`；這個目錄視為唯讀。
2. 執行：

```powershell
npm run build:kb
```

3. 中間產物位於 `data/work/<document_id>/`，結果位於 `data/output/<document_id>/`。

### 維護與驗證

```powershell
npm run kb -- resume <document_id>
npm run kb -- validate <document_id>
npm run kb -- index <document_id>
npm test
```

只有在使用者明確啟用 provider 後才執行 `enrich`。若 provider 是遠端服務，圖片與文字可能離開本機，必須先確認資料授權與隱私要求。

## 目前輸出

| 路徑 | 用途 |
|---|---|
| `data/work/<id>/source/original.pdf` | 本機來源真相副本 |
| `data/work/<id>/batch_pdfs/` | 有界實體 PDF batches |
| `data/work/<id>/extracted/page_NNNN.json` | 逐頁原始／品質記錄 |
| `data/output/<id>/pages/page_NNNN.webp` | 可檢視的來源頁影像 |
| `data/output/<id>/DOCUMENT.md` | 預設完整閱讀文件 |
| `data/output/<id>/PART-*.md` | 超過每檔頁數上限時才產生 |
| `data/output/<id>/chunks.jsonl` | 具來源頁碼的檢索 chunks |
| `data/output/<id>/manifest.json` | 文件、batch、page、image 與 chapter 狀態 |
| `data/output/<id>/qa_report.json` | 完整性與人工複核提示 |

## 下一步

1. 選取經授權的 10–30 個代表頁，涵蓋原生文字、掃描、圖表、密集表格與技術圖。
2. 量測 OCR 正確率、表格結構、數字／單位、圖片對頁碼、執行時間與記憶體。
3. 依結果把建議路由升級為更細的 OCR／VLM page queues。
4. 增加 prompt-injection 邊界、provider／prompt 版本紀錄和表格驗證。
5. 完成基本來源引用檢索評估後，再決定是否加入向量或圖片檢索。

## 驗證結果

- 完整測試套件最近一次結果：11 passed（早於 Markdown 整併變更）；整併後以真實 PDF resume、validate 和連結檢查完成流程驗證。
- `uv run kb doctor`：Python 3.12、Docling 與本機環境可偵測。
- `config/default.yaml`：Pydantic 載入成功。
- `git diff --check`：通過。

## 已知限制

- 尚未使用真實掃描、密集工程表格、爆炸圖或 200+ 頁文件完成準確率與壓力基準。
- Page profile 與品質規則仍是啟發式，需要代表性資料校準。
- PyMuPDF fallback 不提供 OCR；影像頁會保留並標示為需要處理。
- 技術數字只會標記為需要人工複核，不會自動視為已驗證事實。
- 尚未建置向量資料庫、多模態檢索或人工審核 UI。
- Windows 非 UTF-8 console 直接輸出中文 QA 時可能出現 `UnicodeEncodeError`；目前可先設定 `$env:PYTHONUTF8 = "1"`。
- 每個 OCR batch 都會初始化 converter，這份 86 頁文件的解析累計約 11 分 37 秒。
- 技術代碼與精確 token 的 OCR 錯誤可能仍被標成 `success`，輸出目前不可直接當作權威技術資料。
- 文件頁數超過每檔上限時會產生多個 PART 文件；預設上限為 100 頁，可在 `output.max_markdown_pages_per_file` 調整。

## 延伸文件

- [PDF pipeline audit](PDF_PIPELINE_AUDIT.md)
- [架構](ARCHITECTURE.md)
- [功能與限制](FEATURES.md)
- [測試指南](TESTING.md)
- [文件雙格式規範](DOCUMENTATION_POLICY.md)
- [HTML 狀態頁](PROJECT_STATUS.html)
