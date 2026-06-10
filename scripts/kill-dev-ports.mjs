#!/usr/bin/env node
/** Free ports 3000/8000 before starting dev (avoids stale broken Next/uvicorn instances). */
import { execSync } from "node:child_process";

const PORTS = [3000, 8000];

function killPortWindows(port) {
  try {
    const out = execSync(`netstat -ano | findstr ":${port} "`, { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] });
    const pids = new Set();
    for (const line of out.split(/\r?\n/)) {
      if (!line.includes("LISTENING")) continue;
      const parts = line.trim().split(/\s+/);
      const pid = parts[parts.length - 1];
      if (pid && /^\d+$/.test(pid) && pid !== "0") pids.add(pid);
    }
    for (const pid of pids) {
      try {
        execSync(`taskkill /F /PID ${pid} /T`, { stdio: "ignore" });
        console.log(`Freed port ${port} (pid ${pid})`);
      } catch {
        /* already gone */
      }
    }
  } catch {
    /* nothing listening */
  }
}

function killPortUnix(port) {
  try {
    const out = execSync(`lsof -ti :${port}`, { encoding: "utf8", stdio: ["pipe", "pipe", "ignore"] });
    for (const pid of out.trim().split(/\s+/)) {
      if (!pid) continue;
      try {
        process.kill(Number(pid), "SIGTERM");
        console.log(`Freed port ${port} (pid ${pid})`);
      } catch {
        /* ignore */
      }
    }
  } catch {
    /* nothing listening */
  }
}

for (const port of PORTS) {
  if (process.platform === "win32") killPortWindows(port);
  else killPortUnix(port);
}

console.log("Dev ports 3000/8000 cleared. Starting fresh servers...");
