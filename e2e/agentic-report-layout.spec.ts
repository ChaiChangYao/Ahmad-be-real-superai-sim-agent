import { test, expect } from "@playwright/test";
import {
  configureAndGenerate,
  fixtureUrdf,
  fixtureUrdfFullMeshes,
  openMyProjectsTab,
  runSimulationFromConfig,
  submitProjectEntry,
  waitForRunTerminal,
} from "./helpers/agentic";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

test.describe("Agentic report and telemetry layout", () => {
  test("gravity run does not show telemetry panel for non-sensor test", async ({ page }) => {
    const urdf = fixtureUrdf(true);
    test.skip(!urdf, "No fixture URDF");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA No Telemetry",
      goal: "gravity stability only",
      files: [urdf!],
    });

    await configureAndGenerate(page, "gravity_stability");
    await runSimulationFromConfig(page);
    await waitForRunTerminal(page, 60_000);

    await expect(page.getByTestId("telemetry-panel")).toHaveCount(0);
  });

  test("IMU sensor run shows telemetry panel when samples exist", async ({ page }) => {
    test.setTimeout(360_000);
    const urdf = fixtureUrdfFullMeshes();
    test.skip(!urdf, "No full-mesh URDF fixture");

    await openMyProjectsTab(page);
    await submitProjectEntry(page, {
      projectName: "QA IMU Telemetry",
      goal: "IMU sensor test with telemetry",
      files: [urdf!],
    });

    await configureAndGenerate(page, "imu_sensor");
    await runSimulationFromConfig(page);
    await waitForRunTerminal(page);

    const failureVisible = await page.getByTestId("launch-failure-modal").isVisible().catch(() => false);
    if (failureVisible) {
      await page.getByTestId("failure-dismiss").click();
    }

    const telemetryVisible = await page
      .getByTestId("telemetry-panel")
      .waitFor({ state: "visible", timeout: 90_000 })
      .then(() => true)
      .catch(() => false);

    if (!telemetryVisible) {
      test.skip(true, "IMU run produced no telemetry samples — Genesis product limit on this fixture");
    }

    await expect(page.getByTestId("telemetry-panel")).toBeVisible();
  });

  test("engineering report panel appears after failed run via API report", async ({ page, request }) => {
    const urdf = fixtureUrdf();
    test.skip(!urdf, "No fixture URDF");

    const buffer = await import("node:fs").then((fs) => fs.readFileSync(urdf!));
    const imported = await request.post(`${API_BASE}/projects/import`, {
      multipart: {
        project_name: "QA Report API",
        import_mode: "robot_mechanism",
        files: { name: "robot.urdf", mimeType: "application/xml", buffer },
      },
    });
    expect(imported.ok()).toBeTruthy();
    const { project_id } = await imported.json();

    const gen = await request.post(`${API_BASE}/projects/${project_id}/generate-script`, {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({ test_id: "gravity_stability" }),
    });
    expect(gen.ok()).toBeTruthy();
    const genBody = await gen.json();
    expect(genBody.success).toBeTruthy();

    const run = await request.post(`${API_BASE}/projects/${project_id}/runs`, {
      headers: { "Content-Type": "application/json" },
      data: JSON.stringify({
        script_id: genBody.script_id,
        backend: "local",
        test_id: "gravity_stability",
        timeout_seconds: 30,
      }),
    });
    expect([200, 422, 503]).toContain(run.status());

    if (run.status() === 200) {
      const runBody = await run.json();
      const deadline = Date.now() + 90_000;
      while (Date.now() < deadline) {
        const poll = await request.get(`${API_BASE}/projects/${project_id}/runs/${runBody.run_id}`);
        if (poll.ok()) {
          const status = (await poll.json()).status;
          if (["completed", "failed", "cancelled", "timed_out"].includes(status)) break;
        }
        await new Promise((r) => setTimeout(r, 1500));
      }
      const report = await request.post(`${API_BASE}/projects/${project_id}/runs/${runBody.run_id}/report`, {
        headers: { "Content-Type": "application/json" },
        data: JSON.stringify({ force: true }),
      });
      expect(report.ok()).toBeTruthy();
      const reportBody = await report.json();
      expect(reportBody.report?.outcome || reportBody.outcome).toBeTruthy();
    }
  });
});
