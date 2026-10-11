import { spawnSync } from "node:child_process";

const check = spawnSync("uv", ["--version"], {
  encoding: "utf8",
  shell: false,
});

if (check.error?.code === "ENOENT") {
  console.error(
    "\n[setup] uv was not found. Install it from https://docs.astral.sh/uv/getting-started/installation/ and run npm install again.\n",
  );
  process.exit(1);
}

if (check.status !== 0) {
  console.error("\n[setup] Unable to run uv. Check your uv installation and PATH.\n");
  process.exit(check.status ?? 1);
}

console.log(`[setup] ${check.stdout.trim()}`);
console.log("[setup] Installing the Python 3.12 environment with Docling...");

const sync = spawnSync(
  "uv",
  ["sync", "--python", "3.12", "--extra", "docling", "--locked"],
  { stdio: "inherit", shell: false },
);

if (sync.error) {
  console.error(`\n[setup] Failed to start uv: ${sync.error.message}\n`);
  process.exit(1);
}

process.exit(sync.status ?? 1);
