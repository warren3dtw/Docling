# PDF pipeline conventions

- `pipeline.py` 是流程協調層；解析、輸出、索引、狀態與品質檢查維持可獨立測試的模組邊界。
- `pages_per_batch` 控制真正切出的 PDF 批次，不可只在記憶體中切分解析結果。
- `PageBatch.start_page`、`end_page` 與所有 `page_number` 都是原始 PDF 的 1-based 全域頁碼。
- 批次結果只有在來源 SHA-256、解析設定指紋及輸出 SHA-256 都相符時才能重用。
- manifest、JSON 與 Markdown 寫入須維持原子性；失敗批次要保留可診斷錯誤並允許續跑。
- provider 未啟用時保留 `None`、空陣列或 `pending_enrichment`，不得以規則或模型猜測補值。
- 新增外部 provider 時必須有 timeout、有限 retries、可讀錯誤、明確 opt-in 與資料外傳說明。
- 維持 Markdown frontmatter、manifest schema 與 `chunks.jsonl` 欄位的向後相容；若必須改版，先新增 schema version 與遷移說明。
