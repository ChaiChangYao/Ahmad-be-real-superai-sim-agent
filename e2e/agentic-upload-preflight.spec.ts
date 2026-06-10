import { test, expect } from "@playwright/test";
import path from "node:path";
import { fixtureUrdf, openMyProjectsTab, submitProjectEntry } from "./helpers/agentic";

test.describe("Agentic upload and preflight", () => {
  test("upload shows attachment tray and file name", async ({ page }) => {
    const urdf = fixtureUrdf();
    test.skip(!urdf, "No fixture URDF");

    await openMyProjectsTab(page);
    await page.getByTestId("pill-file-input").setInputFiles(urdf!);
    await expect(page.getByTestId("attachment-tray")).toBeVisible();
    await expect(page.getByTestId("attachment-tray")).toContainText(path.basename(urdf!));
  });

  test("URDF with missing meshes shows missing mesh table before Genesis", async ({ page }) => {
    const urdf = fixtureUrdf(true);
    test.skip(!urdf, "No default-robot-dog URDF fixture");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Missing Mesh",
      goal: "joint sweep gravity IMU",
      files: [urdf!],
    });

    await expect(page.getByTestId("missing-mesh-table")).toBeVisible({ timeout: 90_000 });
    await expect(page.getByTestId("test-recommendations")).toBeVisible();
    await expect(page.getByTestId("test-recommendations")).toContainText(/Gravity|gravity|joint/i);
  });

  test("preflight shows blocked tests with reasons", async ({ page }) => {
    const urdf = fixtureUrdf(true);
    test.skip(!urdf, "No default-robot-dog URDF fixture");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA Blocked Tests",
      goal: "FEA and CFD readiness",
      files: [urdf!],
    });

    const rec = page.getByTestId("test-recommendations");
    await expect(rec).toBeVisible({ timeout: 90_000 });
    await expect(rec.getByText(/Blocked|blocked|readiness/i).first()).toBeVisible();
  });
});
