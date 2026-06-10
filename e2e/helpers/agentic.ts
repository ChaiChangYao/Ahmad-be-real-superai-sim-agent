import { expect, type Page } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

export const REPO_ROOT = path.resolve(__dirname, "../..");

const FULL_MESH_URDF = path.join(
  REPO_ROOT,
  "sim-data/projects/imported-85653eba/assets/imported/robot_dog_buildables_demo.urdf",
);
const MISSING_MESH_URDF = path.join(
  REPO_ROOT,
  "sim-data/projects/default-robot-dog/assets/imported/robot_dog_buildables_demo.urdf",
);

export function fixtureUrdfFullMeshes(): string | null {
  return fs.existsSync(FULL_MESH_URDF) ? FULL_MESH_URDF : null;
}

export function fixtureUrdf(preferMissingMeshes = false): string | null {
  if (preferMissingMeshes && fs.existsSync(MISSING_MESH_URDF)) return MISSING_MESH_URDF;
  if (fs.existsSync(FULL_MESH_URDF)) return FULL_MESH_URDF;
  if (fs.existsSync(MISSING_MESH_URDF)) return MISSING_MESH_URDF;
  return null;
}

export async function openMyProjectsTab(page: Page) {
  await page.goto("/genesis");
  await page.getByTestId("tab-my-projects").click();
  await expect(page.getByTestId("project-entry-screen")).toBeVisible({ timeout: 60_000 });
}

export async function submitProjectEntry(
  page: Page,
  opts: { projectName: string; goal: string; files: string[] },
) {
  await page.getByTestId("project-name-input").fill(opts.projectName);
  await page.getByTestId("pill-textarea").fill(opts.goal);
  const fileInput = page.getByTestId("pill-file-input");
  await fileInput.setInputFiles(opts.files);
  await expect(page.getByTestId("attachment-tray")).toBeVisible();
  await page.getByTestId("pill-submit").click();
  await expect(page.getByTestId("buildables-assistant")).toBeVisible({ timeout: 30_000 });
  await expect(page.getByTestId("user-message")).toBeVisible({ timeout: 15_000 });
  if (opts.files.length) {
    await expect(page.getByTestId("user-message-attachments")).toBeVisible({ timeout: 15_000 });
  }
  await expect(page.getByTestId("agent-timeline")).toBeVisible({ timeout: 120_000 });
}

export async function waitForAgentTimelineStep(
  page: Page,
  stepId: string,
  status: "pending" | "running" | "done" | "failed" | "skipped",
  timeoutMs = 120_000,
) {
  const step = page.getByTestId(`agent-timeline-step-${stepId}`);
  await expect(step).toBeVisible({ timeout: timeoutMs });
  await expect(page.getByTestId(`agent-timeline-step-status-${stepId}`)).toContainText(
    status === "done" ? "✓" : status === "failed" ? "✗" : status === "skipped" ? "—" : /[◐○]/,
    { timeout: timeoutMs },
  );
}

export async function assertUserMessagePersists(page: Page, text: string) {
  const msg = page.getByTestId("user-message");
  await expect(msg).toBeVisible({ timeout: 30_000 });
  await expect(msg).toContainText(text, { timeout: 5_000 });
  await page.waitForTimeout(2000);
  await expect(msg).toBeVisible();
}

export function localMyProjectsFixtureDir(): string | null {
  const dir = process.env.QA_MY_PROJECTS_FIXTURE_DIR;
  if (!dir) return null;
  return fs.existsSync(dir) ? dir : null;
}

export async function closeGeneratedScriptViewer(page: Page) {
  const viewer = page.getByTestId("generated-script-viewer");
  if (await viewer.isVisible().catch(() => false)) {
    await page.getByTestId("generated-script-close").click();
    await expect(viewer).toHaveCount(0);
  }
}

export async function configureAndGenerate(page: Page, testId: string, opts?: { keepViewerOpen?: boolean }) {
  await page.getByTestId(`test-configure-${testId}`).click();
  await expect(page.getByTestId("test-config-panel")).toBeVisible({ timeout: 30_000 });
  const generateBtn = page.getByTestId("generate-script-button");
  await expect(generateBtn).toBeEnabled({ timeout: 30_000 });
  await generateBtn.click();
  const viewer = page.getByTestId("generated-script-viewer");
  const viewerVisible = await viewer
    .waitFor({ state: "visible", timeout: 120_000 })
    .then(() => true)
    .catch(() => false);
  if (!viewerVisible) {
    await page.getByTestId("view-generated-code-button").click();
    await expect(viewer).toBeVisible({ timeout: 30_000 });
  }
  if (!opts?.keepViewerOpen) {
    await closeGeneratedScriptViewer(page);
    await expect(page.getByTestId("view-generated-code-button")).toBeVisible({ timeout: 30_000 });
  }
}

export async function waitForRunTerminal(page: Page, timeoutMs = 180_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await page.getByTestId("launch-failure-modal").isVisible().catch(() => false)) {
      return "failure_modal" as const;
    }
    const card = page.getByTestId("run-execution-card");
    if (await card.isVisible().catch(() => false)) {
      const text = await card.textContent().catch(() => "");
      if (/Completed|Failed|Cancelled|Timed out/i.test(text ?? "")) {
        return "terminal" as const;
      }
    }
    await page.waitForTimeout(2000);
  }
  throw new Error("Timed out waiting for run terminal state");
}

export async function waitForReplayControls(page: Page, timeoutMs = 60_000): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (await page.getByTestId("replay-controls").isVisible().catch(() => false)) {
      return true;
    }
    const status = await page.getByTestId("replay-viewer-status").textContent().catch(() => "");
    if (/\d+\s*\/\s*\d+/.test(status ?? "") && !/0\s*\/\s*0/.test(status ?? "")) {
      return true;
    }
    await page.waitForTimeout(2000);
  }
  return false;
}

export async function runSimulationFromConfig(page: Page) {
  await expect(page.getByTestId("run-simulation-button")).toBeEnabled({ timeout: 10_000 });
  await page.getByTestId("run-simulation-button").click();
  await expect(page.getByTestId("run-execution-card")).toBeVisible({ timeout: 60_000 });
}
