---
paths:
  - "tests/**/*.py"
---

# 測試規則

- 使用 pytest、`tmp_path` 與合成 PDF，測試必須離線且不接觸真實使用者文件。
- 批次與頁碼案例涵蓋跨批邊界和非整除頁數。
- provider 以 monkeypatch/fake response 測試 timeout、retry、驗證與停用行為。
- 輸出測試同時檢查 Markdown/frontmatter、圖片、JSONL、manifest 與 QA。
- 完成程式變更後執行完整 `uv run pytest`。
