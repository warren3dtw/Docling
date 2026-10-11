# 86 頁實際 PDF 流程驗證

- 驗證日期：2026-10-11
- 文件 ID：`26_clt_and_mass_timber_en_-32cd7da6637d`
- 階段：實際文件 smoke validation 完成
- 執行模式：本機離線 Docling + RapidOCR；VLM／LLM 停用
- 結論：資料、追溯與結構 QA 通過；內容準確率尚未通過，抽樣發現標題、產品代碼與材料文字 OCR 錯誤

## 驗證範圍

使用 `data/input` 中唯一一份經使用者指定的 PDF 執行完整流程。來源檔案保持唯讀，所有中間產物寫入 `data/work`，結果寫入 `data/output`。驗證未啟用遠端 provider，因此圖片與文字沒有離開本機。

## 執行方式

```powershell
uv run kb build --input data/input --config config/default.yaml --skip-vlm --skip-llm
```

Windows 終端輸出驗證使用 UTF-8：

```powershell
$env:PYTHONUTF8 = "1"
uv run kb validate 26_clt_and_mass_timber_en_-32cd7da6637d --config config/default.yaml
uv run kb resume 26_clt_and_mass_timber_en_-32cd7da6637d --config config/default.yaml
```

## 結果摘要

| 項目 | 結果 |
|---|---:|
| 來源 PDF | 1 份，86 頁，約 17 MB |
| 實體 batches | 9 個：10、10、10、10、10、10、10、10、6 頁 |
| Batch 成功／失敗 | 9／0 |
| Batch 累計解析時間 | 696.87 秒 |
| Page records | 86 |
| Page WebP | 86 |
| Page 狀態 | 83 success、3 partial、0 failed、0 skipped |
| Chapters | 64 |
| Chunks | 64 |
| 抽取圖片 | 151；VLM 停用，因此全部 pending enrichment |
| Broken links | 0 |
| Output 大小 | 54.81 MiB |
| QA | `valid: true` |

## 完整性驗證

- 來源 PDF 與 `data/work/<id>/source/original.pdf` 的 SHA-256 完全相同。
- 9 個實體小 PDF 都未超過 10 頁，合計 86 頁。
- Batch 結果的全域頁碼完整且連續為 1–86。
- 86 份逐頁 JSON 的 `document_id`、`source_sha256` 與頁碼一致。
- 64 個 `chunks.jsonl` records 都包含有效來源頁碼。
- 86 張頁面影像、86 份逐頁 JSON、Markdown frontmatter 與相對連結通過 QA。
- 實際 resume 於 37.61 秒完成，9 個 batch 的 `attempts` 全部未改變，證明成功 batch 沒有重跑。

## Partial 頁面抽查

| 原 PDF 頁碼 | 狀態 | 原因 | 人工觀察 |
|---:|---|---|---|
| 71 | partial | `very_short_extracted_text` | 以貨櫃與設備照片為主，幾乎沒有可辨識文字 |
| 78 | partial | `very_short_extracted_text` | 以木構外牆細部照片為主，幾乎沒有可辨識文字 |
| 86 | partial | `very_short_extracted_text` | 以樓板施工工具照片為主，幾乎沒有可辨識文字 |

三頁完整來源影像均已保存。將它們標為 `partial` 而不是文字抽取成功，符合目前保守品質政策；未發現頁面遺失。

## Markdown 文件整併

依照使用需求，閱讀文件已重新匯出為單一 `DOCUMENT.md`，不再為 64 個語意章節各產生一份小檔。64 個章節錨點仍留在完整文件內，`INDEX.md` 連到相應錨點，`chunks.jsonl` 維持 64 筆章節粒度資料。

- Markdown 檔案：`DOCUMENT.md`、`INDEX.md`、`README.md` 共 3 份；舊 `chapters/*.md` 為 0。
- `DOCUMENT.md`：91,889 bytes，含 64 個章節錨點。
- QA：`valid: true`、0 broken links。
- 9 個解析 batch 仍成功，重新輸出沒有改變 batch 嘗試次數。

## Page profile 觀察

- 86 頁都被辨識為 `image_only` 與 `scan_or_image`。
- 80 頁帶有 `technical_diagram` 訊號。
- 34 頁帶有 `scan` 訊號。

這證明該文件高度影像化，也表示下一階段需以人工標註樣本校準 `technical_diagram` 和 `scan` 規則，而不能把目前 heuristic 當成真實分類標籤。

## 每 batch 內容抽樣

人工對照原 PDF 頁 1、11、21、31、41、51、61、71、81 的來源影像與逐頁抽取文字：

- 頁 1、21、31、41、51、81 的主要中英文內容大致一致，閱讀順序可用。
- 頁 71 是照片頁，抽取內容只有圖片標記，維持 `partial` 符合預期。
- 頁 11 的產品頁標題出現遺漏與破碎文字。
- 頁 61 的產品代碼、塗層／材料文字有拼字及字符辨識錯誤。
- 頁 11、61 仍被標示為 `success`，現有品質規則沒有提出警告。

因此，本次的 `QA valid: true` 只代表頁面覆蓋、資料結構、連結與處理狀態完整，不代表 OCR 文字或技術規格完全正確。現階段輸出適合做可追溯的草稿與人工複核來源，不應直接視為權威技術知識。

## 發現的問題

1. 在目前 Windows CP932 console 中，直接執行 `kb validate` 會在輸出中文 QA 內容時觸發 `UnicodeEncodeError`；設定 `PYTHONUTF8=1` 後驗證正常回傳。資料與驗證邏輯本身沒有失敗。
2. 每個需要 OCR 的 batch 都會重新初始化 Docling／RapidOCR converter。本次 9 個 batch 累計約 11 分 37 秒，是明顯的效能改善點。
3. Resume 沒有重跑解析 batch，但仍需約 38 秒重新掃描頁面、圖片與輸出。
4. 151 張圖片沒有語意描述，因為 VLM 按規範維持停用；系統沒有捏造替代描述。
5. 現有低品質偵測沒有抓到頁 11 與 61 的產品標題／代碼 OCR 錯誤，結構 QA 與內容準確率之間仍有缺口。

## 下一步

1. 修正 CLI 在 Windows 非 UTF-8 console 的輸出相容性。
2. 評估安全重用 Docling／RapidOCR converter，降低每 batch 初始化成本。
3. 針對文字頁、表格頁和技術圖建立人工標註樣本，衡量 OCR 與分類準確率。
4. 為產品代碼、認證編號、材料等精確 token 增加 OCR 一致性／字典／人工複核規則。
5. 擴大 64 章 Markdown 的內容層級抽樣，而不只驗證結構完整性。
6. 維持 VLM opt-in；若要啟用遠端 provider，先確認圖片與文字離開本機的授權與隱私風險。

## 已知限制

本次只驗證一份 86 頁、高度影像化的文件；它能證明有界分批、追溯、輸出、QA 與 resume 的實際運作，但不能代表所有語言、表格類型、原生文字 PDF 或 200+ 頁文件的品質與效能。

## 快速入口

- [HTML 報告](2026-10-11-real-pdf-validation.html)
- [專案狀態](../PROJECT_STATUS.md)

PDF 與生成的 `data/output`／`data/work` 產物依專案規範不納入 Git；需在本機完成流程後查看對應輸出。
