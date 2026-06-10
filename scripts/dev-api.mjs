#!/usr/bin/env node
/**
 * Cross-platform API dev launcher (replaces manual start-api.ps1).
 * Sets Genesis env vars and starts uvicorn without --reload (Genesis/Taichi on Windows).
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const world = join(root, "genesis-world");
const nyx = join(root, "genesis-nyx");
const PORT = 8000;
const HOST = "127.0.0.1";

function resolvePython() {
  const candidates = [
    join(root, "apps", "api", ".venv", "Scripts", "python.exe"),
    join(root, "apps", "api", ".venv", "bin", "python"),
    join(root, ".venv", "Scripts", "python.exe"),
    join(root, ".venv", "bin", "python"),
  ];
  for (const candidate of candidates) {
    if (existsSync(candidate)) return candidate;
  }
  return null;
}

function checkHealth() {
  return new Promise((resolveHealth) => {
    const req = http.get({ hostname: HOST, port: PORT, path: "/health", timeout: 3000 }, (res) => {
      res.resume();
      resolveHealth(res.statusCode === 200);
    });
    req.on("error", () => resolveHealth(false));
    req.on("timeout", () => {
      req.destroy();
      resolveHealth(false);
    });
  });
}

function portAvailable(port) {
  return new Promise((resolvePort) => {
    const server = net.createServer();
    server.once("error", () => resolvePort(false));
    server.once("listening", () => {
      server.close(() => resolvePort(true));
    });
    server.listen(port, HOST);
  });
}

const env = { ...process.env };
if (existsSync(world)) env.GENESIS_WORLD_ROOT = world;
if (existsSync(nyx)) env.GENESIS_NYX_ROOT = nyx;
env.PYTHONUTF8 = "1";
env.PYTHONIOENCODING = "utf-8";

let child = null;
let shuttingDown = false;

function startUvicorn() {
  const python = resolvePython();
  if (!python) {
    console.error("[dev-api] API virtualenv not found.");
    console.error("[dev-api] Run once from repo root: npm run setup:api");
    console.error("[dev-api] (System Python is not used — it often has incompatible FastAPI/Starlette versions.)");
    process.exit(1);
  }

  console.log(`Starting API on http://${HOST}:${PORT} ... (python: ${python})`);
  console.log("[dev-api] API ready when you see: Uvicorn running on http://127.0.0.1:8000");

  child = spawn(
    python,
    [
      "-m",
      "uvicorn",
      "main:app",
      "--app-dir",
      "apps/api",
      "--host",
      HOST,
      "--port",
      String(PORT),
    ],
    { cwd: root, env, stdio: "inherit", shell: false },
  );

  child.on("exit", (code, signal) => {
    if (shuttingDown) {
      process.exit(code ?? 0);
      return;
    }
    const label = signal ? `signal ${signal}` : `code ${code ?? "?"}`;
    console.error(`[dev-api] Uvicorn stopped (${label}).`);
    if (signal === "SIGTERM" || signal === "SIGKILL") {
      console.error("[dev-api] Process was killed externally (second npm run dev? npm run dev:clean first).");
    }
    process.exit(code ?? 1);
  });
}

function shutdown(forwardSignal) {
  if (shuttingDown) return;
  shuttingDown = true;
  if (child && !child.killed) {
    child.kill(forwardSignal);
  } else {
    process.exit(0);
  }
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));

async function main() {
  console.log(`GENESIS_WORLD_ROOT=${env.GENESIS_WORLD_ROOT ?? "(not set)"}`);
  console.log(`GENESIS_NYX_ROOT=${env.GENESIS_NYX_ROOT ?? "(not set)"}`);

  if (!(await portAvailable(PORT))) {
    if (await checkHealth()) {
      console.log(`[dev-api] Reusing existing API on http://${HOST}:${PORT}`);
      return;
    }
    console.error(
      `[dev-api] Port ${PORT} is in use but /health failed. Stop the stale process or run: npm run dev:clean`,
    );
    process.exit(1);
  }

  startUvicorn();
}

main().catch((error) => {
  console.error("[dev-api]", error);
  process.exit(1);
});
