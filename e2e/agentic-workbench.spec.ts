import { test, expect } from "@playwright/test";
import path from "node:path";
import fs from "node:fs";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const REPO_ROOT = path.resolve(__dirname, "..");

async function openMyProjectsTab(page: import("@playwright/test").Page) {
  await page.goto("/genesis");
  await page.getByTestId("tab-my-projects").click();
  await expect(page.getByTestId("project-entry-screen")).toBeVisible({ timeout: 60_000 });
}

function fixtureUrdf(): string | null {
  const candidates = [
    path.join(REPO_ROOT, "sim-data/projects/imported-85653eba/assets/imported/robot_dog_buildables_demo.urdf"),
    path.join(REPO_ROOT, "sim-data/projects/default-robot-dog/assets/imported/robot_dog_buildables_demo.urdf"),
  ];
  return candidates.find((p) => fs.existsSync(p)) ?? null;
}

test.describe("Buildables Agentic Workbench", () => {
  test("API health and agentic dependencies", async ({ request }) => {
    const health = await request.get(`${API_BASE}/health`);
    expect(health.ok()).toBeTruthy();

    const deps = await request.get(`${API_BASE}/agentic/dependencies`);
    expect(deps.ok()).toBeTruthy();
    const body = await deps.json();
    expect(body.dependencies?.trimesh).toBe("available");
  });

  test("genesis page loads My Projects entry screen", async ({ page }) => {
    await openMyProjectsTab(page);
    await expect(page.getByTestId("pill-composer")).toBeVisible();
    await expect(page.getByText("Upload your robot files")).toBeVisible();
  });

  test("upload URDF via pill composer and reach preflight", async ({ page }) => {
    const urdf = fixtureUrdf();
    test.skip(!urdf, "No fixture URDF in sim-data");

    await openMyProjectsTab(page);
    await page.getByTestId("project-name-input").fill("QA Playwright Project");
    await page.getByTestId("pill-textarea").fill("Can I run gravity and joint sweep?");

    const fileInput = page.getByTestId("pill-file-input");
    await fileInput.setInputFiles(urdf!);

    await expect(page.getByTestId("attachment-tray")).toBeVisible();

    await page.getByTestId("pill-submit").click();

    await expect(page.getByTestId("buildables-assistant")).toBeVisible({ timeout: 30_000 });
    await expect(page.getByTestId("user-message")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByTestId("agent-timeline")).toBeVisible({ timeout: 120_000 });

    const assistant = page.getByTestId("buildables-assistant");
    await expect(assistant.getByText(/recommended|blocked|preflight|test/i).first()).toBeVisible({
      timeout: 60_000,
    });
  });

  test("API upload proves multipart import works", async ({ request }) => {
    const urdf = fixtureUrdf();
    test.skip(!urdf, "No fixture URDF in sim-data");

    const buffer = fs.readFileSync(urdf);
    const res = await request.post(`${API_BASE}/projects/import`, {
      multipart: {
        project_name: "QA API Upload",
        import_mode: "robot_mechanism",
        files: {
          name: path.basename(urdf),
          mimeType: "application/xml",
          buffer,
        },
      },
    });
    expect(res.ok()).toBeTruthy();
    const data = await res.json();
    expect(data.project_id).toMatch(/^imported-/);
    expect(data.files_saved).toBeGreaterThan(0);

    const inspect = await request.post(`${API_BASE}/projects/${data.project_id}/inspect`);
    expect(inspect.ok()).toBeTruthy();
    const report = await inspect.json();
    expect(report.project_id).toBe(data.project_id);
  });
});
