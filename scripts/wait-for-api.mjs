#!/usr/bin/env node
/** Poll GET /health until the Buildables API responds (used before starting Next.js). */
import http from "node:http";

const HOST = process.env.BUILDABLES_API_HOST ?? "127.0.0.1";
const PORT = Number(process.env.BUILDABLES_API_PORT ?? 8000);
const TIMEOUT_MS = Number(process.env.BUILDABLES_API_WAIT_MS ?? 120_000);
const INTERVAL_MS = Number(process.env.BUILDABLES_API_POLL_MS ?? 500);

function checkHealth() {
  return new Promise((resolve) => {
    const req = http.get(
      { hostname: HOST, port: PORT, path: "/health", timeout: 3000 },
      (res) => {
        res.resume();
        resolve(res.statusCode === 200);
      },
    );
    req.on("error", () => resolve(false));
    req.on("timeout", () => {
      req.destroy();
      resolve(false);
    });
  });
}

export async function waitForApi(options = {}) {
  const timeoutMs = options.timeoutMs ?? TIMEOUT_MS;
  const intervalMs = options.intervalMs ?? INTERVAL_MS;
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await checkHealth()) {
      return true;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
  return false;
}
