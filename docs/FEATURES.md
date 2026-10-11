# 功能與狀態

## 已完成

### 有界 PDF 分批

掃描來源後依 `processing.pages_per_batch` 建立 1-based、首尾包含的範圍，並把每批真正寫成小 PDF 再交給解析器。23 頁、每批 10 頁會形成 1–10、11–20、21–23。這個限制與 VLM 圖片批量無關。

### Docling 與 PyMuPDF 解析

預設使用 Docling standard pipeline，支援 OCR、表格結構與圖片；PyMuPDF 是無 Docling 時的基礎 fallback，可抽取排序文字、簡單表格與標題候選。兩者輸出相同的逐頁契約，頁碼皆映射回原 PDF。

### 可恢復處理與快取失效

每批狀態、attempts、輸出雜湊與錯誤寫入 manifest。再次執行會跳過可驗證的成功批次，只重試失敗或損壞項目。來源內容或影響解析的設定改變時，document ID 或設定指紋使舊快取失效。

### 章節與 Markdown 匯出

所有成功頁面跨批次載入後才組裝章節，因此批次邊界沒有語意。標題改變時切章；沒有標題則依 fallback 頁數切分。輸出含 YAML frontmatter、來源頁範圍、擷取式關鍵字、圖片與相鄰章節連結。

### 圖片抽取與可選 VLM

圖片依原始頁碼產生穩定 ID，套用最小尺寸、最大像素與去重規則，並記錄被過濾原因。VLM 預設停用；啟用後只描述可觀察內容，保留辨識文字、數值與不確定性。失敗會留下 `failed` 與原因，不偽造 caption。

### 可選 LLM 摘要

章節預設 `summary: null`、空搜尋問題及 `pending_enrichment`。啟用 OpenAI-compatible summary provider 後，輸入以保守字元上限限制，結果經 Pydantic 驗證並依模型快取；失敗標記 `enrichment_failed`。

### 索引與 QA

每份文件建立 README、章節 INDEX 與 `chunks.jsonl`。QA 檢查 frontmatter YAML、圖片連結、JSONL 語法、批次失敗與頁數，並提供人工抽驗清單。QA 是結構性檢查，不宣稱內容已由人驗證。

### CLI 與環境診斷

`doctor` 不呼叫模型，只回報 OS、Python、CPU/RAM、GPU、Docling、模型設定與 key 是否存在。`build`、`resume`、`validate`、`index`、`enrich` 分別處理初次建置、續跑、驗證、重建及 opt-in enrichment。

## 已知限制

- PyMuPDF 不等同 Docling 的複雜版面與表格辨識品質。
- 向量圖未必以可抽取嵌入圖片存在；目前不無限制渲染整頁給 VLM。
- `chunks.jsonl` 是搜尋或 embedding 的輸入，專案尚未建立向量資料庫或 RAG runtime。
- QA 不驗證技術陳述真偽，仍需對照原 PDF 抽驗。
- `max_workers` 與部分描述類設定已存在設定模型中，但目前流程仍依序處理批次與圖片。

## 本次文件移植

已加入 Codex 分層 `AGENTS.md`、Claude Code rules/hooks/7 個 subagents，以及繁體中文開發文件；未更動 PDF 處理行為或公開 CLI。
