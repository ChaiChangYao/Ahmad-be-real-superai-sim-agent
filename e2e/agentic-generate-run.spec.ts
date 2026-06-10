import { test, expect } from "@playwright/test";
import { configureAndGenerate, fixtureUrdf, openMyProjectsTab, submitProjectEntry } from "./helpers/agentic";

test.describe("Agentic generate and run", () => {
  test("generate script opens viewer with Python source", async ({ page }) => {
    const urdf = fixtureUrdf(true);
    test.skip(!urdf, "No fixture URDF");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Codegen",
      goal: "gravity stability test",
      files: [urdf!],
    });

    await configureAndGenerate(page, "gravity_stability", { keepViewerOpen: true });
    await expect(page.getByTestId("generated-script-viewer")).toBeVisible();
    await expect(page.getByTestId("generated-script-source")).toContainText(/genesis|import|def main/i);
  });

  test("run simulation shows status card and logs with copy", async ({ page }) => {
    const urdf = fixtureUrdf(true);
    test.skip(!urdf, "No fixture URDF");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Run",
      goal: "gravity stability",
      files: [urdf!],
    });

    await configureAndGenerate(page, "gravity_stability");
    await expect(page.getByTestId("run-simulation-button")).toBeEnabled({ timeout: 10_000 });
    await page.getByTestId("run-simulation-button").click();

    await expect(page.getByTestId("run-execution-card")).toBeVisible({ timeout: 60_000 });

    const terminal = Date.now() + 180_000;
    while (Date.now() < terminal) {
      if (await page.getByTestId("launch-failure-modal").isVisible().catch(() => false)) break;
      if (await page.getByTestId("run-execution-card").getByText(/Completed|Failed|Cancelled|Timed out/i).isVisible().catch(() => false)) {
        break;
      }
      await page.waitForTimeout(2000);
    }

    const failureVisible = await page.getByTestId("launch-failure-modal").isVisible().catch(() => false);
    if (failureVisible) {
      await expect(page.getByTestId("failure-copy-logs")).toBeVisible();
      await page.getByTestId("failure-dismiss").click();
    }

    const logsVisible = await page.getByTestId("run-log-copy").isVisible().catch(() => false);
    if (logsVisible) {
      await expect(page.getByTestId("run-log-copy")).toBeEnabled();
    }
  });
});
