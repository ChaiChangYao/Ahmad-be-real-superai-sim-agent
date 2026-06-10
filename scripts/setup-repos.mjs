#!/usr/bin/env node
/** Clone genesis-world + genesis-nyx example repos next to the monorepo root (catalogue demos). */
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const REPOS = [
  {
    dir: "genesis-world",
    url: "https://github.com/Genesis-Embodied-AI/Genesis.git",
  },
  {
    dir: "genesis-nyx",
    url: "https://github.com/Genesis-Embodied-AI/genesis-nyx.git",
  },
];

function run(cmd, args, label) {
  console.log(`[setup-repos] ${label}`);
  const result = spawnSync(cmd, args, { cwd: root, stdio: "inherit", shell: false });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

for (const repo of REPOS) {
  const path = join(root, repo.dir);
  if (existsSync(join(path, ".git"))) {
    run("git", ["-C", path, "pull", "--ff-only"], `Updating ${repo.dir}`);
  } else if (existsSync(path)) {
    console.log(`[setup-repos] ${repo.dir}/ exists but is not a git clone — skipping`);
  } else {
    run("git", ["clone", "--depth", "1", repo.url, repo.dir], `Cloning ${repo.dir}`);
  }
}

console.log("[setup-repos] Example repos ready (genesis-world, genesis-nyx).");
