import process from "node:process";

let raw = "";
for await (const chunk of process.stdin) raw += chunk;

let input;
try {
  input = JSON.parse(raw || "{}");
} catch {
  process.exit(0);
}

const filePath = input?.tool_input?.file_path;
if (typeof filePath !== "string" || filePath.length === 0) process.exit(0);

const normalized = filePath.replaceAll("\\", "/").replace(/\/+/g, "/").toLowerCase();
const basename = normalized.slice(normalized.lastIndexOf("/") + 1);
const parts = normalized.split("/").filter(Boolean);
const inInputDirectory = parts.some(
  (part, index) => part === "data" && parts[index + 1] === "input",
);
const realEnv = basename.startsWith(".env") && basename !== ".env.example";
const credentialExtension = /\.(pem|key|p12|pfx|jks|keystore)$/.test(basename);
const credentialName = /^(id_rsa|id_dsa|id_ecdsa|id_ed25519|credentials?|secrets?)($|\.)/.test(
  basename,
);
const userPdf = basename.endsWith(".pdf");

if (realEnv || credentialExtension || credentialName || userPdf || inInputDirectory) {
  const reason = `受保護的檔案不可由 Claude Code 寫入：${filePath}`;
  process.stdout.write(
    JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    }),
  );
}
