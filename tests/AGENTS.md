# Test conventions

- 使用 pytest、`tmp_path`、fixtures 與程式產生的合成 PDF；不得讀取或提交真實使用者 PDF。
- 測試需可離線執行，不可依賴 Docling 模型下載、GPU 或外部 AI 服務。
- 測試批次邊界時至少涵蓋非整除頁數；測頁碼時要跨過第二批並驗證 1-based 全域頁碼。
- 續跑測試需確認成功批次未重跑、失敗批次只重試必要部分，並保留 attempts 語意。
- AI 測試使用 monkeypatch/fake response，驗證 timeout、retry、無效 JSON 與 disabled provider 不捏造內容。
- 輸出測試同時檢查 frontmatter、Markdown、圖片連結、JSONL 與 QA 結果。
- 新增或修改測試後執行 `uv run pytest`；測試名稱描述外部可觀察行為。
