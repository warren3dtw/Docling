# Git Commit 規則

- Commit message 使用 `type: 簡潔描述`；常用 type 為 `feat`、`fix`、`docs`、`test`、`refactor`、`chore`。
- Commit 前檢查 status、完整 diff、`git diff --check` 與相關測試。
- 不加入 PDF、`.env*`（`.env.example` 除外）、憑證、`data/work`、`data/output`、快取或虛擬環境。
- 不使用 `git reset --hard`，不覆蓋使用者既有變更。
- Commit message 不加入 `Co-Authored-By`；repo-local agent 不執行 push。
