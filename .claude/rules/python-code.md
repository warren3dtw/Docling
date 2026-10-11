---
paths:
  - "src/**/*.py"
  - "scripts/**/*.py"
---

# Python 程式碼規則

- 使用 Python 3.11 相容語法與明確型別；路徑使用 `pathlib.Path`。
- 設定由 strict Pydantic models 驗證，不默默接受未知欄位。
- 模組維持單一責任；CLI 呈現與核心處理邏輯分離。
- 檔案輸出使用既有原子寫入 helper；不要留下半份 manifest 或 JSON。
- 執行專案程式與工具時使用 `uv run`，依賴異動同步 `uv.lock`。
