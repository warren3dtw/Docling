const reminder = [
  "Context 已壓縮，請重新遵守專案核心規則：",
  "data/input 唯讀；不得提交 PDF、真實 .env 或憑證。",
  "長 PDF 必須以有界實體批次處理，並保留 1-based 全域頁碼。",
  "AI enrichment 必須 opt-in，停用時不得捏造摘要或圖片描述。",
  "程式變更後執行 uv run pytest，並同步受影響文件。",
].join("\n");

process.stdout.write(
  JSON.stringify({
    hookSpecificOutput: {
      hookEventName: "SessionStart",
      additionalContext: reminder,
    },
  }),
);
