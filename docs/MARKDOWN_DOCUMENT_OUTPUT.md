# Markdown 文件整併方式

- 最後更新：2026-10-11
- 階段：已實作並套用到既有 86 頁 PDF 輸出
- 預設：每份 PDF 一份 `DOCUMENT.md`

## 使用者看到的文件

解析 batch 的大小只控制記憶體和續跑範圍；它不會決定閱讀文件的數量。解析完成後，系統先保留語意章節，再把它們整合到一份完整 Markdown。章節仍有標題和錨點，`INDEX.md` 可跳至對應章節，`chunks.jsonl` 繼續保留每個語意章節，供下游檢索使用。

預設 `output.max_markdown_pages_per_file: 100`。文件不超過 100 頁時只產生 `DOCUMENT.md`；超過時在章節邊界拆為 `PART-001.md`、`PART-002.md` 等。單一章節也會依同一頁數上限切開，確保大型文件不會形成無界 Markdown。

## 輸出位置

- `data/output/<document_id>/DOCUMENT.md`：一般文件的完整閱讀版。
- `data/output/<document_id>/PART-*.md`：超過每檔頁數上限時的連續部分。
- `INDEX.md`：語意章節索引，連至 `DOCUMENT.md#ch-...` 或對應 PART 錨點。
- `chunks.jsonl`：保持既有 JSONL 欄位，以來源路徑連回 Markdown 章節錨點。

舊版的 `chapters/ch-*.md` 會在重新匯出時清除，避免舊的小檔案與新整合文件並存造成混淆。

## 目前套用情況

86 頁 CLT PDF 低於 100 頁上限，會整理成一份 `DOCUMENT.md`。原先 64 個語意章節仍留在文件內，檢索資料仍有 64 個章節 chunks；使用者不必再逐個打開 64 個 Markdown 檔。

重新匯出後的實際結果：根目錄只有 `DOCUMENT.md`、`INDEX.md`、`README.md` 三份 Markdown；章節子目錄中沒有舊 Markdown。`DOCUMENT.md` 為 91,889 bytes，包含 64 個章節錨點；`chunks.jsonl` 仍有 64 筆，QA `valid: true` 且 0 broken links。

## 操作

重新產生既有 PDF 輸出時執行：

```powershell
uv run kb resume 26_clt_and_mass_timber_en_-32cd7da6637d --config config/default.yaml
```

調整分段門檻時修改 `config/default.yaml` 的 `output.max_markdown_pages_per_file`，然後重新執行 `resume` 或 `build`。此為輸出設定，不會使成功的解析 batches 失效。

## 驗證與限制

- 必須確認單一文件頁數未超上限、章節錨點有效、圖片與來源頁連結存在。
- `chunks.jsonl` 保留章節粒度，因此檢索用途不會被迫使用整份長文件作為單一 chunk。
- 文件整併只整理檔案與章節呈現，不會修正 OCR 文字錯誤；技術代碼仍需人工抽驗。
