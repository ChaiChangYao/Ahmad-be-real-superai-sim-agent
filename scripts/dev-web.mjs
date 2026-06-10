#!/usr/bin/env node
/** Wait for API health, then start Next.js (avoids "Cannot reach API" on cold boot). */
import { spawn } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import net from "node:net";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { waitForApi } from "./wait-for-api.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const webDir = join(root, "apps", "web");
const nextDir = join(webDir, ".next");
const WEB_PORT = 3000;

/** Partial .next (e.g. after QA clean during dev) causes white screen / routes-manifest ENOENT. */
function repairNextCacheIfCorrupt() {
  if (!existsSync(nextDir)) return;
  const routesManifest = join(nextDir, "routes-manifest.json");
  if (existsSync(routesManifest)) return;
  console.warn("[dev-web] Corrupt .next cache (missing routes-manifest.json) — removing and rebuilding …");
  rmSync(nextDir, { recursive: true, force: true });
}

function portAvailable(port) {
  return new Promise((resolvePort) => {
    const server = net.createServer();
    server.once("error", () => resolvePort(false));
    server.once("listening", () => {
      server.close(() => resolvePort(true));
    });
    server.listen(port);
  });
}

console.log("[dev-web] Waiting for API at http://127.0.0.1:8000 …");
const ready = await waitForApi({ timeoutMs: 30_000, intervalMs: 500 });
if (!ready) {
  console.warn(
    "[dev-web] API not ready yet — starting Next.js anyway (workbench shows Retry; run npm run setup:api if API crashed).",
  );
}

console.log("[dev-web] API ready — starting Next.js on http://localhost:3000");

repairNextCacheIfCorrupt();

if (!(await portAvailable(WEB_PORT))) {
  console.error(
    `[dev-web] Port ${WEB_PORT} is already in use (stale Next.js?). Run: npm run dev:clean`,
  );
  process.exit(1);
}

const nextCli = join(root, "node_modules", "next", "dist", "bin", "next");
if (!existsSync(nextCli)) {
  console.error("[dev-web] Next.js not found. Run: npm install (from repo root)");
  process.exit(1);
}

const child = spawn(process.execPath, [nextCli, "dev", "-p", String(WEB_PORT)], {
  cwd: webDir,
  env: process.env,
  stdio: "inherit",
  shell: false,
});

child.on("exit", (code) => process.exit(code ?? 0));

process.on("SIGINT", () => child.kill("SIGINT"));
process.on("SIGTERM", () => child.kill("SIGTERM"));
