---
paths:
  - "**/*.md"
  - "config/**/*.yaml"
  - ".env.example"
---

# 文件規則

- 使用繁體中文敘述，命令、欄位、模組與標準技術詞保留英文。
- 文件只描述現有行為；未完成功能要明確標示限制或規劃中。
- CLI、設定、資料流、測試或輸出格式異動時同步相關 docs 與 changelog。
- 較大功能採 User Story → Spec → Tasks，完成後移至 `docs/plans/archive/`。
- `CLAUDE.md` 保持精簡（少於 200 行），細節放在 `docs/`。
