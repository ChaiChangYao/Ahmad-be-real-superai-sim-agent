#!/usr/bin/env node
/**
 * Run the full Buildables Agentic QA suite:
 * - Python verify scripts (preflight, codegen, execution, reporting, API E2E)
 * - Web build
 * - Optional Playwright browser E2E (when --e2e or QA_E2E=1)
 */
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { waitForApi } from "./wait-for-api.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const venvPython =
  process.platform === "win32"
    ? join(root, "apps", "api", ".venv", "Scripts", "python.exe")
    : join(root, "apps", "api", ".venv", "bin", "python");

const runE2e = process.argv.includes("--e2e") || process.env.QA_E2E === "1";

const steps = [
  {
    id: "setup",
    label: "Ensure API venv",
    fn: () => {
      const ensure = spawnSync(process.execPath, [join(root, "scripts", "ensure-api-ready.mjs")], {
        cwd: root,
        stdio: "inherit",
        shell: false,
      });
      return ensure.status ?? 1;
    },
    required: true,
  },
  {
    id: "agentic-layer",
    label: "verify_agentic_layer.py",
    fn: () => runPython("apps/api/app/scripts/verify_agentic_layer.py"),
    required: true,
  },
  {
    id: "goal-parser",
    label: "verify_goal_parser.py",
    fn: () => runPython("apps/api/app/scripts/verify_goal_parser.py"),
    required: true,
  },
  {
    id: "codegen",
    label: "verify_codegen.py",
    fn: () => runPython("apps/api/app/scripts/verify_codegen.py"),
    required: true,
  },
  {
    id: "execution",
    label: "verify_execution.py",
    fn: () => runPython("apps/api/app/scripts/verify_execution.py"),
    required: false,
  },
  {
    id: "reporting",
    label: "verify_reporting.py",
    fn: () => runPython("apps/api/app/scripts/verify_reporting.py"),
    required: true,
  },
  {
    id: "api-e2e",
    label: "verify_agentic_api_e2e.py",
    fn: () => runPython("apps/api/app/scripts/verify_agentic_api_e2e.py"),
    required: true,
  },
  {
    id: "golden-paths",
    label: "qa_agentic_golden_paths.py",
    fn: () => runPython("apps/api/app/scripts/qa_agentic_golden_paths.py"),
    required: true,
  },
  {
    id: "build-web",
    label: "build:web",
    fn: () => runNpmScript("build:web"),
    required: true,
  },
];

function runNpmScript(script) {
  const r = spawnSync("npm", ["run", script], {
    cwd: root,
    stdio: "inherit",
    shell: true,
  });
  return r.status ?? 1;
}

function runPython(relPath) {
  if (!existsSync(venvPython)) {
    console.error(`[qa] Missing venv python at ${venvPython}`);
    return 1;
  }
  const r = spawnSync(venvPython, [relPath], {
    cwd: root,
    stdio: "inherit",
    shell: false,
    env: { ...process.env, PYTHONPATH: join(root, "apps", "api") },
  });
  return r.status ?? 1;
}

function spawnDetached(cmd, args, cwd, name) {
  const child = spawn(cmd, args, {
    cwd,
    stdio: "inherit",
    shell: false,
    detached: process.platform !== "win32",
    env: process.env,
  });
  child.on("exit", (code) => {
    if (code !== 0 && code !== null) {
      console.error(`[qa] ${name} exited with code ${code}`);
    }
  });
  return child;
}

async function runPlaywrightE2e() {
  console.log("\n[qa] Starting API + web for Playwright E2E …");
  const api = spawnDetached(
    process.execPath,
    [join(root, "scripts", "dev-api.mjs")],
    root,
    "api",
  );
  const web = spawnDetached(
    process.execPath,
    [join(root, "scripts", "dev-web.mjs")],
    root,
    "web",
  );

  const ready = await waitForApi({ timeoutMs: 120_000, intervalMs: 1000 });
  if (!ready) {
    console.error("[qa] API did not become ready for E2E");
    killChild(api);
    killChild(web);
    return 1;
  }
  await sleep(8000);

  const pw = spawnSync("npx", ["playwright", "test", "--config", "e2e/playwright.config.ts"], {
    cwd: root,
    stdio: "inherit",
    shell: true,
    env: { ...process.env, CI: "1" },
  });
  killChild(api);
  killChild(web);
  return pw.status ?? 1;
}

function killChild(child) {
  if (!child?.pid) return;
  try {
    if (process.platform === "win32") {
      spawnSync("taskkill", ["/pid", String(child.pid), "/f", "/t"], { stdio: "ignore", shell: false });
    } else {
      process.kill(-child.pid, "SIGTERM");
    }
  } catch {
    try {
      child.kill("SIGTERM");
    } catch {
      /* ignore */
    }
  }
}

function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

async function main() {
  console.log("=== Buildables Agentic QA Suite ===\n");
  const outcomes = [];

  for (const step of steps) {
    console.log(`\n--- ${step.label} ---`);
    const code = step.fn();
    outcomes.push({ ...step, code });
    if (code !== 0 && step.required) {
      console.error(`\n[qa] REQUIRED step failed: ${step.label} (exit ${code})`);
      printSummary(outcomes);
      process.exit(code);
    }
    if (code !== 0) {
      console.warn(`[qa] Optional step failed (continuing): ${step.label}`);
    }
  }

  if (runE2e) {
    console.log("\n--- Playwright browser E2E ---");
    const e2eCode = await runPlaywrightE2e();
    outcomes.push({ id: "playwright", label: "Playwright E2E", code: e2eCode, required: true });
    if (e2eCode !== 0) {
      printSummary(outcomes);
      process.exit(e2eCode);
    }
  } else {
    console.log("\n[qa] Skipping Playwright E2E (run with --e2e or QA_E2E=1)");
  }

  printSummary(outcomes);
  const failed = outcomes.filter((o) => o.code !== 0);
  process.exit(failed.length ? 1 : 0);
}

function printSummary(outcomes) {
  console.log("\n=== QA Summary ===");
  for (const o of outcomes) {
    const mark = o.code === 0 ? "PASS" : o.required === false ? "WARN" : "FAIL";
    console.log(`  [${mark}] ${o.label}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
