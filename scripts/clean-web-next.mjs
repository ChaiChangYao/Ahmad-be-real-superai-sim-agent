#!/usr/bin/env node
/** Remove Next.js build cache (fixes white screen / MODULE_NOT_FOUND after mixed build+dev). */
import { rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const nextDir = join(root, "apps", "web", ".next");
rmSync(nextDir, { recursive: true, force: true });
console.log(`Removed ${nextDir}`);
