import { test, expect } from "@playwright/test";
import {
  assertUserMessagePersists,
  fixtureUrdfFullMeshes,
  openMyProjectsTab,
  submitProjectEntry,
  waitForAgentTimelineStep,
  waitForRunTerminal,
} from "./helpers/agentic";

const GOAL = "testing the joint of this robot";

test.describe("My Projects agent thread", () => {
  test("Enter creates persistent thread with attachments and timeline", async ({ page }) => {
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "full-mesh URDF fixture missing in sim-data");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: `QA Thread ${Date.now()}`,
      goal: GOAL,
      files: [urdf!],
    });

    await assertUserMessagePersists(page, GOAL);
    await waitForAgentTimelineStep(page, "planning_tests", "done", 120_000);

    const timeline = page.getByTestId("agent-timeline");
    await expect(timeline).toBeVisible();
    await expect(page.getByTestId("test-recommendations").or(page.getByText(/joint_sweep/i))).toBeVisible({
      timeout: 60_000,
    });
  });

  test("goal maps to joint_sweep in recommendations", async ({ page }) => {
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "full-mesh URDF fixture missing");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: `QA Goal ${Date.now()}`,
      goal: GOAL,
      files: [urdf!],
    });

    await expect(page.getByText(/joint_sweep/i).first()).toBeVisible({ timeout: 120_000 });
  });

  test("auto pipeline reaches run or explains failure in thread", async ({ page }) => {
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "full-mesh URDF fixture missing");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: `QA AutoRun ${Date.now()}`,
      goal: "test the joint movement of this robot",
      files: [urdf!],
    });

    await waitForAgentTimelineStep(page, "planning_tests", "done", 120_000);

    const outcome = await Promise.race([
      waitForRunTerminal(page, 180_000).then((r) => r),
      page
        .getByTestId("agent-timeline-step-generating_script")
        .waitFor({ state: "visible", timeout: 180_000 })
        .then(() => "codegen" as const),
    ]).catch(() => "timeout" as const);

    if (outcome === "failure_modal") {
      await expect(page.getByTestId("launch-failure-modal")).toBeVisible();
      await expect(page.getByTestId("agent-timeline")).toBeVisible();
      return;
    }

    expect(outcome).not.toBe("timeout");
    await expect(page.getByTestId("user-message")).toBeVisible();
    await expect(page.getByTestId("agent-timeline")).toBeVisible();
  });

  test("broken zip shows failed step in timeline via API", async ({ request }) => {
    const health = await request.get("http://127.0.0.1:8000/health");
    test.skip(!health.ok(), "API not running");

    const badZip = Buffer.from("not-a-real-zip-file");
    const res = await request.post("http://127.0.0.1:8000/projects/import", {
      multipart: {
        project_name: "QA Bad Zip",
        import_mode: "robot_mechanism",
        files: {
          name: "broken.zip",
          mimeType: "application/zip",
          buffer: badZip,
        },
      },
    });
    expect(res.status()).toBe(400);
    const body = await res.json();
    const detail = body.detail ?? body;
    expect(JSON.stringify(detail)).toMatch(/zip|extract/i);
  });
});
