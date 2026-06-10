#!/usr/bin/env node
/** Create apps/api/.venv and install pinned requirements (avoids system Python version skew). */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const apiDir = join(root, "apps", "api");
const venvDir = join(apiDir, ".venv");
const venvPython =
  process.platform === "win32"
    ? join(venvDir, "Scripts", "python.exe")
    : join(venvDir, "bin", "python");
const requirementsCore = join(apiDir, "requirements-core.txt");

function run(cmd, args, label) {
  console.log(`[setup-api] ${label}`);
  const result = spawnSync(cmd, args, { cwd: root, stdio: "inherit", shell: false });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function canImport(snippet) {
  const result = spawnSync(venvPython, ["-c", snippet], { cwd: root, stdio: "pipe", shell: false });
  return result.status === 0;
}

function venvReady() {
  if (!existsSync(venvPython)) return false;
  if (!canImport("import uvicorn")) return false;
  if (!canImport("import fastapi")) return false;
  if (!canImport("from fastapi import APIRouter; APIRouter(tags=['x'])")) return false;
  if (!canImport("import torch")) return false;
  if (!canImport("import genesis")) return false;
  const verify = spawnSync(
    venvPython,
    ["app/scripts/verify_genesis_install.py"],
    { cwd: apiDir, stdio: "pipe", shell: false, env: { ...process.env, PYTHONPATH: apiDir } },
  );
  return verify.status === 0;
}

if (!existsSync(venvPython)) {
  const launcher = process.platform === "win32" ? "py" : "python3";
  const venvArgs = process.platform === "win32" ? ["-3", "-m", "venv", venvDir] : ["-m", "venv", venvDir];
  run(launcher, venvArgs, `Creating venv at ${venvDir}`);
}

if (venvReady()) {
  console.log("[setup-api] Core API + Genesis already ready — skipping pip install");
  console.log("[setup-api] Start dev with: npm run dev");
  process.exit(0);
}

run(venvPython, ["-m", "pip", "install", "-U", "pip"], "Upgrading pip");

if (!canImport("import torch")) {
  if (process.platform === "win32") {
    run(
      venvPython,
      [
        "-m",
        "pip",
        "install",
        "torch",
        "torchvision",
        "torchaudio",
        "--index-url",
        "https://download.pytorch.org/whl/cpu",
      ],
      "Installing PyTorch (CPU wheel for Windows — required before genesis-world)",
    );
  } else {
    run(venvPython, ["-m", "pip", "install", "torch"], "Installing PyTorch (required before genesis-world)");
  }
  run(venvPython, ["-m", "pip", "install", "-U", "setuptools>=77"], "Restoring setuptools for genesis-world/quadrants");
} else {
  console.log("[setup-api] PyTorch already installed in venv");
}

run(venvPython, ["-m", "pip", "install", "-r", requirementsCore], "Installing core API deps");

console.log("[setup-api] Verifying Genesis install...");
const verify = spawnSync(
  venvPython,
  ["app/scripts/verify_genesis_install.py"],
  { cwd: apiDir, stdio: "inherit", shell: false, env: { ...process.env, PYTHONPATH: apiDir } },
);
if (verify.status !== 0) {
  console.error("[setup-api] Genesis verification failed. See docs/GENESIS_SETUP_WINDOWS.md");
  process.exit(verify.status ?? 1);
}

console.log("[setup-api] Core API + Genesis ready. Optional: pip install -r apps/api/requirements.txt for pydantic-ai");
console.log("[setup-api] Start dev with: npm run dev");
