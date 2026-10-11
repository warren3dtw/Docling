# Project conventions

## 常用指令

- 使用 `uv run` 執行 Python 指令；依賴異動後保留並提交 `uv.lock`。
- 安裝：`npm install` 或 `uv sync --python 3.12 --extra docling`。
- 環境檢查：`npm run doctor` 或 `uv run kb doctor`。
- 測試：`npm test` 或 `uv run pytest`。
- 離線建置：`npm run build:kb`。

## 資料與安全

- `data/input` 永遠視為唯讀。中間產物寫入 `data/work`，結果寫入 `data/output`。
- 不得提交使用者 PDF、真實 `.env`、API key、私鑰、憑證、快取或產出資料。
- `.env.example` 只能包含空白或安全的範例值。
- 啟用遠端 AI provider 前，必須提醒使用者圖片與文字會離開本機。

## PDF 管線不變量

- 長 PDF 必須切成有明確上限的實體小 PDF 批次；不可一次載入整份長文件規避批次限制。
- 所有對外輸出、manifest、圖片 ID 與錯誤訊息都保留原 PDF 的 1-based 全域頁碼。
- 續跑只重試失敗、缺漏或雜湊不符的批次；狀態與結果使用原子寫入。
- AI enrichment 是 opt-in。provider 停用或失敗時，不得捏造摘要、搜尋問題或圖片描述。
- 不得未經明確需求變更 Markdown frontmatter、manifest 或 `chunks.jsonl` 相容格式。

## 變更與文件

- 修改程式後執行 `uv run pytest`；文件或設定變更至少執行相關格式與載入驗證。
- 行為、設定、CLI 或輸出格式變更時，同步更新 README、`docs/FEATURES.md`、`docs/ARCHITECTURE.md`、`docs/TESTING.md` 與 `docs/CHANGELOG.md` 中受影響部分。
- 較大功能先在 `docs/plans/YYYY-MM-DD-<feature>.md` 記錄 User Story、Spec、Tasks；完成後移至 `docs/plans/archive/`。
- Commit 使用 Conventional Commits，且不得加入 `Co-Authored-By`。
