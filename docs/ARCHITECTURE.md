# 架構

## 設計目標

管線優先確保長 PDF 不會一次無界載入解析器、所有結果能回溯原始頁碼、執行中斷後能安全續跑，以及沒有 provider 時不產生虛構 enrichment。CLI 只負責參數與呈現；主要行為集中在可測試的 Python 模組。

## 目錄與模組責任

| 路徑 | 責任 |
|---|---|
| `config/default.yaml` | 路徑、批次、解析器、provider 與輸出預設值 |
| `cli.py` | Typer 的 `doctor/build/resume/validate/index/enrich` 命令 |
| `config.py` | 嚴格 Pydantic 設定與解析快取指紋 |
| `pdf_scan.py` | SHA-256、document ID、頁數/metadata/TOC 與實體 PDF 切分 |
| `batching.py` | 1-based、首尾都包含的批次邊界 |
| `parse_docling.py` | `BatchParser` 協定、Docling 與 PyMuPDF 解析器 |
| `pipeline.py` | manifest、批次重試/續跑、enrichment 與輸出協調 |
| `image_extract.py` | 圖片抽取、尺寸限制、去重及過濾原因 |
| `chapter_assembly.py` | 跨批次頁面排序、章節組裝、擷取式關鍵字 |
| `vlm.py` / `llm.py` | Disabled 與 OpenAI-compatible provider |
| `markdown_export.py` | 章節 frontmatter、來源頁碼、圖片與相鄰章節連結 |
| `index_build.py` | 文件 README、INDEX 與 `chunks.jsonl` |
| `quality.py` | frontmatter、圖片連結、JSONL、批次與人工抽驗清單 |
| `state.py` | UTC 時間、SHA-256、JSON 載入與原子寫入 |

## 資料流

```text
data/input/*.pdf（唯讀）
  → scan_pdf：來源 SHA-256、document_id、頁數
  → make_batches：1-based 有界範圍
  → split_pdf：data/work/<id>/batch_pdfs/*.pdf
  → Docling 或 PyMuPDF：逐批 JSON + 全域頁碼
  → 重載所有成功批次並依 page_number 排序
  → 圖片抽取（可驗證）
  → VLM enrichment（選用、可快取）
  → 跨批次章節組裝
  → LLM enrichment（選用、輸入受限、可快取）
  → Markdown / INDEX / chunks.jsonl / manifest / QA
  → data/output/<id>/
```

`pages_per_batch` 限制 PDF 解析工作；`max_images_per_vlm_batch` 是不同的設定，不能替代 PDF 分批。Docling 的批次內頁碼透過 `global_start_page + local_index` 映射回原始 PDF。

## 狀態、快取與續跑

`document_id` 由安全化檔名與來源 SHA-256 前 12 碼構成。解析批次是否可重用同時取決於來源 SHA-256、`pages_per_batch` 與 parsing 設定所組成的 `config_fingerprint`，以及批次 JSON 的實際 SHA-256。任何條件不符就重新建立相關批次。

每批先在 manifest 標記 `running`，成功後記錄 `output_path`、`output_sha256`、attempts 與耗時；失敗則保留例外型別和訊息。JSON/文字先寫同目錄暫存檔再 replace，避免中斷留下半份狀態。`continue_on_error` 允許其他批次繼續，最終 manifest 會是 `partial`。

## Enrichment 邊界

預設 `vision.enabled` 與 `summary.enabled` 都是 `false`。離線輸出只包含原始可擷取內容、擷取式關鍵字及 `pending_enrichment`。啟用 OpenAI-compatible provider 後，圖片與章節文字可能傳到本機或遠端端點；呼叫具有 timeout、有限 retry 與 JSON 驗證。失敗狀態明確記錄，不能用猜測內容掩蓋。

## 輸出契約

| 產物 | 重要欄位 / 語意 |
|---|---|
| `data/work/<id>/manifest.json` | 來源、指紋、批次狀態、圖片、章節與 warnings |
| `data/work/<id>/batches/*.json` | parser 名稱與帶全域 `page_number` 的 pages |
| `data/output/<id>/chapters/*.md` | YAML frontmatter、來源頁範圍、原始內容、選用 enrichment |
| `INDEX.md` | 章節、頁碼、關鍵字、處理狀態 |
| `chunks.jsonl` | chunk/document/chapter ID、文字、標題、頁碼、圖片與來源路徑 |
| `qa_report.json` | 成功/失敗批次、頁數、圖片、broken links、warnings、manual review |

`schema_version` 目前為 1。任何破壞性格式變更都需版本化與遷移說明。
