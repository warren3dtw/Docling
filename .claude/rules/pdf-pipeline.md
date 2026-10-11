---
paths:
  - "src/knowledge_builder/batching.py"
  - "src/knowledge_builder/pdf_scan.py"
  - "src/knowledge_builder/parse_docling.py"
  - "src/knowledge_builder/pipeline.py"
  - "src/knowledge_builder/chapter_assembly.py"
  - "src/knowledge_builder/image_extract.py"
  - "src/knowledge_builder/markdown_export.py"
  - "src/knowledge_builder/index_build.py"
  - "src/knowledge_builder/quality.py"
---

# PDF 管線規則

- 長文件必須切成 `pages_per_batch` 限制內的實體 PDF；批次邊界不代表章節邊界。
- local page index 一律映射為原 PDF 的 1-based 全域頁碼。
- 成功批次只有在來源、設定指紋與輸出 SHA-256 相符時才能重用。
- 失敗要保留可診斷狀態；續跑不得重做仍有效的成功批次。
- 維持 Markdown、manifest、圖片 ID 與 JSONL 契約，破壞性變更必須版本化。
- provider 未啟用或失敗時不得生成看似合理的替代摘要或圖片描述。
