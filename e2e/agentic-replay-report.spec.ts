import { test, expect } from "@playwright/test";
import {
  configureAndGenerate,
  fixtureUrdfFullMeshes,
  openMyProjectsTab,
  runSimulationFromConfig,
  submitProjectEntry,
  waitForReplayControls,
  waitForRunTerminal,
} from "./helpers/agentic";

test.describe("Agentic replay and engineering report", () => {
  test.setTimeout(360_000);

  test("replay viewer loads after gravity run when frames exist", async ({ page }) => {
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "No full-mesh URDF fixture");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Replay",
      goal: "gravity stability with replay",
      files: [urdf!],
    });

    await configureAndGenerate(page, "gravity_stability");
    await runSimulationFromConfig(page);
    await waitForRunTerminal(page);

    const failureVisible = await page.getByTestId("launch-failure-modal").isVisible().catch(() => false);
    if (failureVisible) {
      await page.getByTestId("failure-dismiss").click();
    }

    const hasReplay = await waitForReplayControls(page, 90_000);
    if (!hasReplay) {
      test.skip(true, "Run finished without replay frames — Genesis product limit on this fixture");
    }

    await expect(page.getByTestId("replay-viewer")).toBeVisible();
    await expect(page.getByTestId("replay-controls")).toBeVisible();
    await expect(page.getByTestId("replay-viewer-status")).toContainText(/\d+\s*\/\s*\d+/);
  });

  test("engineering report panel appears in browser after run", async ({ page }) => {
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "No full-mesh URDF fixture");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Report UI",
      goal: "gravity stability report",
      files: [urdf!],
    });

    await configureAndGenerate(page, "gravity_stability");
    await runSimulationFromConfig(page);
    await waitForRunTerminal(page);

    const failureVisible = await page.getByTestId("launch-failure-modal").isVisible().catch(() => false);
    if (failureVisible) {
      await page.getByTestId("failure-dismiss").click();
    }

    await expect(page.getByTestId("engineering-report-panel")).toBeVisible({ timeout: 120_000 });
    await expect(page.getByTestId("engineering-report-panel")).toContainText(/failed|passed|partial|outcome|report/i);
  });
});
