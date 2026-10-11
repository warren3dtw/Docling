# 測試指南

## 執行方式

```powershell
npm test
# 等同
uv run pytest
```

測試使用 PyMuPDF 與 Pillow 動態建立 23 頁合成 PDF，不需要 Docling 模型、GPU、網路、API key 或真實文件。

## 逐頁 grounding 測試

`tests/test_page_grounding.py` 產生三頁合成 PDF（原生文字、整頁圖片、空白頁），驗證：

- page profile 與建議路由的分類訊號。
- `success`、`partial`、`skipped_with_reason` 狀態。
- 數字／單位需要複核，以及 PyMuPDF 沒有 OCR 的明確警告。
- 原始來源副本的 SHA-256、逐頁 WebP、逐頁 JSON 與 QA 統計。

`tests/test_resume.py` 另驗證失敗 batch 的頁面會產生 `failed` record，成功 batch 在續跑時不會重做。`tests/test_markdown.py` 驗證來源頁面連結、頁面影像與逐頁 JSON 存在，同時保留既有 frontmatter 和 JSONL 相容性。

Markdown 匯出以 `DOCUMENT.md` 作為單一文件入口；語意章節仍映射到同檔錨點，`chunks.jsonl` 保持章節粒度。只有文件超過 `max_markdown_pages_per_file` 時才輸出 `PART-*.md`，並在 QA 驗證合併後的相對連結。

目前共有 11 個離線測試；真實 OCR、密集表格、工程圖與 200+ 頁壓力測試仍需使用經授權的代表性資料另行執行。

## Fixtures

`tests/conftest.py` 的 `synthetic_pdf` 建立 23 頁內容，在第 1 頁放標題、第 11 頁放表格與 120×120 圖片。`config` 將 input/work/output 指向 `tmp_path`、使用 PyMuPDF、每批 10 頁、零 retry，確保隔離且快速。

## 現有 9 項測試

| 測試 | 覆蓋行為 |
|---|---|
| `test_23_pages_in_three_batches` | 非整除頁數形成三個正確批次 |
| `test_second_batch_uses_global_page_numbers` | 第二批第一頁仍為全域第 11 頁 |
| `test_repeat_skips_and_changed_source_gets_new_id` | 重跑跳過成功批次；內容改變產生新 ID |
| `test_config_change_invalidates_cache` | 解析設定變更使指紋與批次快取失效 |
| `test_resume_only_retries_failed_batch` | 首次中斷後只重跑失敗批次 |
| `test_offline_markdown_and_jsonl_are_valid` | 離線 frontmatter、跨批文字、圖片、索引、JSONL、QA |
| `test_model_timeout_is_retried` | provider timeout 依設定重試 |
| `test_invalid_json_has_readable_error` | 無效模型 JSON 產生可讀的有限重試錯誤 |
| `test_disabled_providers_never_fabricate` | disabled VLM/LLM 明確拒絕生成內容 |

## 新增測試

1. 從使用者可觀察行為命名測試，不測私有實作細節。
2. PDF 情境以 fixture 程式產生，所有輸出放 `tmp_path`。
3. 頁碼相關案例至少跨越批次邊界；續跑案例同時驗證 calls 與 attempts。
4. provider 使用 `monkeypatch` 與本機 fake response，禁止實際網路呼叫。
5. 修改輸出時同時檢查 Markdown frontmatter、JSONL 與 `qa_report`。
6. 執行完整 `uv run pytest`，避免只跑單檔漏掉相容性回歸。

範例：

```python
def test_global_page_survives_batch_boundary(synthetic_pdf, config):
    manifest, _ = build_pdf(synthetic_pdf, config, skip_vlm=True, skip_llm=True)
    # 讀取第二批輸出，斷言 page_number == 11。
```

## 常見陷阱

- 不要把 batch PDF 的 local page index 當成輸出頁碼。
- 不要讓測試依賴 Docling 權重下載或特定 GPU。
- 不要在 disabled provider 測試中填入看似合理的摘要或 caption。
- 修改設定指紋時要分辨解析產物與純輸出/enrichment 設定，避免不必要重跑。
- 合成 PDF 通過只證明管線契約，不代表真實複雜文件的內容品質。
