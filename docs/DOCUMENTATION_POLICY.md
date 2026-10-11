# 文件雙格式規範

- 最後更新：2026-10-11
- 狀態：已生效
- 適用範圍：整個 repository

## 規則

任何新增或修改的規則、工作流程、功能、內容或 App 操作方式，都必須在同一個變更中同步記錄為 Markdown 與 HTML。兩種格式必須呈現相同的核心資訊，不得讓其中一份落後。

全域狀態固定維護於：

- [`PROJECT_STATUS.md`](PROJECT_STATUS.md)
- [`PROJECT_STATUS.html`](PROJECT_STATUS.html)

本規範固定維護於：

- `DOCUMENTATION_POLICY.md`
- [`DOCUMENTATION_POLICY.html`](DOCUMENTATION_POLICY.html)

## 每次文件必備內容

1. 最後更新日期。
2. 目前開發或交付階段。
3. 已完成項目。
4. 進行中項目與下一步。
5. App 安裝、啟動、操作或驗證方式。
6. 測試與驗證結果。
7. 已知限制、風險或尚未驗證事項。

## 更新流程

1. 判斷變更是否涉及規則、流程、功能、內容或操作方式。
2. 更新最接近主題的 Markdown；若沒有合適文件，建立新的主題文件。
3. 同步更新同名 HTML，並保持日期、狀態、指令和限制一致。
4. 更新 `PROJECT_STATUS.md` 與 `PROJECT_STATUS.html` 的階段、完成項目和下一步。
5. 在 `docs/README.md` 同時加入 Markdown 與 HTML 入口。
6. 執行相關測試，並驗證 HTML 可解析、文件內相對連結存在。

## HTML 要求

- 必須是可直接開啟的完整 HTML 文件。
- 提供標題、導覽、清楚的章節與適合桌面／行動裝置的可讀版面。
- 不得依賴外部 CDN、遠端字型或 JavaScript 才能閱讀。
- 操作指令使用 `<code>` 或 `<pre>`，狀態與階段需在頁面上方容易辨識。

## 驗證結果

本規範建立時，已同步新增 Markdown／HTML 規範文件與專案狀態頁，並將入口加入文件索引。

## 已知限制

目前 HTML 為人工同步維護，尚未由 Markdown 自動產生；每次變更必須透過審查與連結驗證避免內容漂移。
