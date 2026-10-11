# 開發指南

## 建立環境

```powershell
uv python install 3.12
uv sync --python 3.12 --extra docling
uv run kb doctor
uv run pytest
```

開發指令一律透過 `uv run`。依賴變更使用 uv 更新，並提交 `pyproject.toml` 與 `uv.lock`。不要直接修改 lockfile。

## 命名與模組慣例

| 對象 | 慣例 | 例子 |
|---|---|---|
| Python 模組/函式/變數 | `snake_case` | `build_pdf`, `global_start_page` |
| 類別 / Pydantic model | `PascalCase` | `PageBatch`, `AppConfig` |
| 批次 ID | 固定五位 1-based 首尾頁 | `batch-00011-00020` |
| 章節 ID | 三位流水號 | `ch-003` |
| 圖片 ID | 原頁碼與頁內序號 | `p0011_fig001` |
| 計畫 | `YYYY-MM-DD-<feature>.md` | `2026-10-11-init-project-docs.md` |

函式盡量傳入 `Path` 與設定物件，不使用隱藏的全域狀態。解析器遵循 `BatchParser` 協定；外部 AI 以 provider 類別隔離。CLI 層將預期錯誤轉成清楚訊息與 exit code，核心層保留可測試例外。

## 變更工作流

1. 先讀根目錄與 scoped `AGENTS.md`，確認資料與頁碼不變量。
2. 修改最小範圍，避免同時變更輸出 schema 和無關重構。
3. 為外部可觀察行為新增合成、離線測試。
4. 執行 `uv run pytest`、`git diff --check` 與敏感檔案檢查。
5. 同步行為、架構、測試與 changelog 文件。
6. 使用 Conventional Commit；不加入 `Co-Authored-By`。

## 新增解析或 provider 能力

- 新解析器必須接受實體 batch PDF 與 `global_start_page`，回傳相同 pages 契約。
- 保留 `page_number` 的原始 PDF 1-based 語意，並用跨批測試證明。
- 外部 provider 預設停用，必須有明確 `enabled`、model、timeout、retries 與失敗狀態。
- 遠端呼叫前說明傳出的資料；回應需結構驗證，不將無效 JSON 當成功。
- 若設定會改變批次解析結果，加入 `AppConfig.fingerprint()`。

## 環境變數

| 變數 | 用途 | 必要性 | 預設 |
|---|---|---|---|
| `OPENAI_COMPATIBLE_BASE_URL` | OpenAI-compatible API base URL | provider 啟用時 | `http://localhost:11434/v1` |
| `OPENAI_COMPATIBLE_API_KEY` | API 驗證 | 視端點而定 | 本機相容端點使用 `ollama` fallback |
| `VISION_MODEL` | 圖片描述模型 | vision 啟用且 YAML 未指定 model 時 | 無 |
| `SUMMARY_MODEL` | 摘要模型 | summary 啟用且 YAML 未指定 model 時 | 無 |

只提交 `.env.example`。真實 `.env*`、憑證與私鑰不能讀入紀錄或提交。

## 計畫歸檔流程

1. 在 `docs/plans/` 建立 `YYYY-MM-DD-<feature-name>.md`。
2. 內容依序包含 User Story、Spec、Tasks 與驗證條件。
3. 實作中更新 Tasks，保留重要取捨與結果。
4. 完成後移至 `docs/plans/archive/`。
5. 同步 `docs/FEATURES.md` 與 `docs/CHANGELOG.md`。

詳細範本見 [plans/README.md](plans/README.md)。
