# Page-grounded PDF pipeline

## User Story

身為知識庫維護者，我希望每一頁 PDF 的抽取結果、品質狀態與來源影像都能被追溯，讓掃描頁、圖表頁或失敗頁不會在 Markdown 產製過程中無聲消失。

## Spec

- 在解析前建立逐頁 preflight profile，區分原生文字、掃描／影像、圖表、混合與空白頁，並記錄建議路由。
- 保留來源 PDF 的本機工作副本與每一頁的完整影像；所有人類可讀頁碼維持原 PDF 的 1-based 全域頁碼。
- 在產生章節 Markdown 前，以原子寫入保存每頁結構化 JSON，明確標示成功、部分、失敗或有原因的略過。
- 偵測空白／低資訊／重複文字與可能包含精確數字單位的內容，將不確定內容標示為需要人工複核，不捏造事實。
- 章節 Markdown 加入來源頁影像連結，並保持既有 frontmatter、manifest 與 `chunks.jsonl` 欄位相容。
- VLM/LLM 維持 opt-in；未啟用或失敗時不生成替代描述。

## Tasks

- [x] 新增 preflight page profile 與 bounded page rendering。
- [x] 新增逐頁 record、品質規則與 manifest 摘要。
- [x] 將來源頁連結接入 Markdown 與 QA。
- [x] 新增失敗頁、掃描頁、來源連結與相容性測試。
- [x] 更新 audit、README、功能、架構、測試與 changelog 文件。
- [x] 執行 `uv run pytest` 與相關設定載入驗證。

## 驗證

- 合成的文字、影像與空白頁具有正確 profile、狀態和全域頁碼。
- 失敗 batch 的所有頁面都有 `failed` record，續跑仍只重試失敗 batch。
- 所有 Markdown 來源頁連結都存在，且現有 frontmatter/JSONL 測試繼續通過。
- 完整測試套件通過。

## 結果

已完成來源 PDF 雜湊副本、規則式逐頁 profile、選擇性 batch OCR、bounded 全頁 WebP、逐頁 JSON 四態狀態、品質警告、Markdown 來源連結與 QA。既有 frontmatter、manifest 舊欄位與 `chunks.jsonl` 欄位未移除或改名。

驗證結果：`uv run pytest` 共 11 項通過；`uv run kb doctor` 與預設設定載入成功。尚未以真實掃描、密集表格、工程圖或 200+ 頁 PDF 做準確率與資源基準，後續工作詳見 `docs/PDF_PIPELINE_AUDIT.md`。
