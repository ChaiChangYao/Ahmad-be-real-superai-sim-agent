#!/usr/bin/env node
/** Fast check before dev:api — create venv and install core deps if uvicorn is missing. */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const venvPython =
  process.platform === "win32"
    ? join(root, "apps", "api", ".venv", "Scripts", "python.exe")
    : join(root, "apps", "api", ".venv", "bin", "python");

function canImport(python, snippet) {
  const result = spawnSync(python, ["-c", snippet], { cwd: root, stdio: "pipe", shell: false });
  return result.status === 0;
}

function needsSetup() {
  if (!existsSync(venvPython)) {
    return "API virtualenv missing";
  }
  if (!canImport(venvPython, "import uvicorn")) {
    return "uvicorn not installed in apps/api/.venv";
  }
  if (!canImport(venvPython, "import fastapi")) {
    return "fastapi not installed in apps/api/.venv";
  }
  // Guard against broken/partial installs (system Python often has incompatible Starlette).
  if (!canImport(venvPython, "from fastapi import APIRouter; APIRouter(tags=['x'])")) {
    return "FastAPI/Starlette in apps/api/.venv failed import check";
  }
  // Torch/Genesis are verified by setup:api — skip here to keep predev fast (~30s saved).
  return null;
}

const reason = needsSetup();
if (reason) {
  console.log(`[ensure-api-ready] ${reason} — running npm run setup:api ...`);
  const setup = spawnSync(process.platform === "win32" ? "npm.cmd" : "npm", ["run", "setup:api"], {
    cwd: root,
    stdio: "inherit",
    shell: false,
  });
  if (setup.status !== 0) {
    process.exit(setup.status ?? 1);
  }
  const after = needsSetup();
  if (after) {
    console.error(`[ensure-api-ready] Setup finished but API env still broken: ${after}`);
    process.exit(1);
  }
}
