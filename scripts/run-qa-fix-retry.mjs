#!/usr/bin/env node
/**
 * Run QA suite with retry loop. Exits non-zero if any required step still fails
 * after MAX_CYCLES. The agent should fix code between cycles.
 */
import { spawnSync } from "node:child_process";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const MAX_CYCLES = Number(process.env.QA_MAX_CYCLES ?? 3);
const runE2e = process.argv.includes("--e2e") || process.env.QA_E2E === "1";

function run(cmd, args) {
  const r = spawnSync(cmd, args, { cwd: root, stdio: "inherit", shell: true });
  return r.status ?? 1;
}

for (let cycle = 1; cycle <= MAX_CYCLES; cycle++) {
  console.log(`\n========== QA Fix-Retry Cycle ${cycle}/${MAX_CYCLES} ==========\n`);
  const args = ["scripts/run-qa-agentic.mjs"];
  if (runE2e) args.push("--e2e");
  const code = run("node", args);
  if (code === 0) {
    console.log(`\n[qa-retry] PASSED on cycle ${cycle}`);
    process.exit(0);
  }
  console.error(`\n[qa-retry] Cycle ${cycle} failed (exit ${code}). Fix and retry.`);
  if (cycle === MAX_CYCLES) {
    console.error(`[qa-retry] Exhausted ${MAX_CYCLES} cycles. See docs/qa-agentic-fix-log.md`);
    process.exit(code);
  }
}
