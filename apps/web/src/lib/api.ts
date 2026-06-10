import { GenesisCatalog, GenesisStatus, ManifestState, RunResult, ShowcaseCatalog, ShowcaseLaunchResult, TestCatalogItem, TestRunResult } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_TIMEOUT_MS = 15000;
export const API_BOOT_TIMEOUT_MS = 90000;
/** Zip import + scan/inspect/plan on large robot projects can exceed 15s. */
export const AGENTIC_PREFLIGHT_TIMEOUT_MS = 120_000;
const API_DEV_HINT =
  "From the repo root run: npm run dev\n(This starts the API on :8000 and web on :3000 together.)";

type ApiFetchOptions = RequestInit & { timeoutMs?: number };

export async function apiFetch(input: string, init?: ApiFetchOptions): Promise<Response> {
  const timeoutMs = init?.timeoutMs ?? API_TIMEOUT_MS;
  const { timeoutMs: _ignored, ...fetchInit } = init ?? {};
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { ...fetchInit, signal: controller.signal });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      const hint =
        timeoutMs >= AGENTIC_PREFLIGHT_TIMEOUT_MS
          ? "Large zip/URDF preflight can take up to 2 minutes on first load."
          : timeoutMs >= API_BOOT_TIMEOUT_MS
            ? "Genesis startup can be slow on first load."
            : "Try again or check that the API is running.";
      throw new Error(`API request timed out after ${timeoutMs / 1000}s (${hint}): ${input}`);
    }
    throw new Error(`Cannot reach API at ${API_BASE}. ${API_DEV_HINT}`);
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function pingApiHealth(timeoutMs = 5000): Promise<boolean> {
  try {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const res = await fetch(`${API_BASE}/health`, { cache: "no-store", signal: controller.signal });
      return res.ok;
    } finally {
      window.clearTimeout(timeout);
    }
  } catch {
    return false;
  }
}

export async function waitForApiHealth(options?: { timeoutMs?: number; intervalMs?: number }): Promise<void> {
  const timeoutMs = options?.timeoutMs ?? API_BOOT_TIMEOUT_MS;
  const intervalMs = options?.intervalMs ?? 1000;
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    if (await pingApiHealth(4000)) return;
    await new Promise((resolve) => window.setTimeout(resolve, intervalMs));
  }
  throw new Error(`Cannot reach API at ${API_BASE} after ${Math.round(timeoutMs / 1000)}s. ${API_DEV_HINT}`);
}

export async function getGenesisStatus(): Promise<GenesisStatus> {
  const res = await apiFetch(`${API_BASE}/genesis/status`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Genesis status failed: ${res.status}`);
  }
  return res.json();
}

export async function listProjects(): Promise<Array<{ project_id: string; project_name: string }>> {
  const res = await apiFetch(`${API_BASE}/projects`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Projects fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function loadDefaultRobotDog(): Promise<{ project_id: string; project_name: string; loaded: boolean }> {
  const res = await apiFetch(`${API_BASE}/projects/default-robot-dog/load`, { method: "POST", timeoutMs: API_BOOT_TIMEOUT_MS });
  if (!res.ok) {
    throw new Error(`Default robot dog load failed: ${res.status}`);
  }
  return res.json();
}

export async function loadDefaultRobotArm(): Promise<{ project_id: string; project_name: string; loaded: boolean }> {
  const res = await apiFetch(`${API_BASE}/projects/default-robot-arm/load`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`Default robot arm load failed: ${res.status}`);
  }
  return res.json();
}

export async function importFromDownloadsRobotDog(): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/import-from-downloads`, { method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Import from Downloads failed: ${res.status}`);
  }
  return res.json();
}

export async function getManifest(projectId: string): Promise<ManifestState> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/manifest`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Manifest fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function saveManifest(projectId: string, manifest: ManifestState): Promise<{ saved: boolean; manifest?: ManifestState }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/manifest`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(manifest)
  });
  if (!res.ok) {
    throw new Error(`Manifest save failed: ${res.status}`);
  }
  return res.json();
}

export async function validateManifest(projectId: string): Promise<{ valid: boolean; errors: string[]; warnings: string[] }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/manifest/validate`, { method: "POST" });
  if (!res.ok) {
    throw new Error(`Manifest validation failed: ${res.status}`);
  }
  return res.json();
}

export async function listScenarios(projectId: string): Promise<Array<{ id: string; name: string }>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/scenarios`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Scenarios fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function runScenario(projectId: string, scenarioId: string): Promise<RunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/scenarios/${scenarioId}/run`, {
    method: "POST"
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Scenario run failed: ${res.status}`);
  }
  return res.json();
}

export async function startInteractive(projectId: string): Promise<{ session_id: string }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/simulations/interactive/start`, { method: "POST" });
  if (!res.ok) {
    throw new Error("Failed to start interactive simulation.");
  }
  return res.json();
}

export async function sendInteractiveCommand(
  projectId: string,
  command: string,
  sessionId: string,
  durationS = 0.35
): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/simulations/interactive/command`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, command, duration_s: durationS })
  });
  if (!res.ok) {
    throw new Error("Failed to send interactive command.");
  }
  return res.json();
}

export async function stopInteractive(projectId: string): Promise<{ status: string }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/simulations/interactive/stop`, { method: "POST" });
  if (!res.ok) {
    throw new Error("Failed to stop interactive simulation.");
  }
  return res.json();
}

export async function getGenesisCatalog(): Promise<GenesisCatalog> {
  const res = await apiFetch(`${API_BASE}/genesis/catalog`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Genesis catalog fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function getShowcaseCatalog(): Promise<ShowcaseCatalog> {
  const res = await apiFetch(`${API_BASE}/genesis/showcase/catalog`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Showcase catalog fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function launchShowcaseDemo(
  projectId: string,
  scenarioId: string,
  options?: { viewMode?: "web" | "native"; headless?: boolean },
): Promise<ShowcaseLaunchResult> {
  const q = new URLSearchParams();
  if (options?.viewMode) q.set("view_mode", options.viewMode);
  else if (options?.headless != null) q.set("headless", String(options.headless));
  const suffix = q.size ? `?${q}` : "";
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/showcase/${scenarioId}/launch${suffix}`, {
    method: "POST",
    timeoutMs: 60000,
  });
  if (!res.ok) {
    const body = await res.text();
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      if (parsed.detail) throw new Error(parsed.detail);
    } catch (e) {
      if (e instanceof Error && e.message && !e.message.startsWith("Unexpected")) throw e;
    }
    throw new Error(body || `Showcase launch failed: ${res.status}`);
  }
  return res.json();
}

export async function getShowcaseLaunchTimeseries(
  projectId: string,
  launchId: string,
): Promise<{
  launch_id: string;
  frames: number;
  state_timeseries: Array<Record<string, unknown>>;
  raw_frames?: Array<Record<string, unknown>>;
  preview_frames?: Array<Record<string, unknown>>;
  telemetry?: Record<string, unknown> | null;
  scene?: Record<string, unknown>;
  objects?: Array<Record<string, unknown>>;
  meta?: Record<string, unknown>;
}> {
  const res = await apiFetch(
    `${API_BASE}/projects/${projectId}/genesis/showcase/launch/${launchId}/timeseries`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Showcase timeseries fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function getShowcaseLaunchTelemetry(
  projectId: string,
  launchId: string,
): Promise<{ launch_id: string; telemetry: Record<string, unknown> }> {
  const res = await apiFetch(
    `${API_BASE}/projects/${projectId}/genesis/showcase/launch/${launchId}/telemetry`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Showcase telemetry fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function getShowcaseLaunchLogs(
  projectId: string,
  launchId: string,
): Promise<{ launch_id: string; stdout: string; stderr: string }> {
  const res = await apiFetch(
    `${API_BASE}/projects/${projectId}/genesis/showcase/launch/${launchId}/logs`,
    { cache: "no-store" },
  );
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Showcase launch logs failed: ${res.status}`);
  }
  return res.json();
}

export async function getShowcaseLaunchStatus(projectId: string, launchId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/showcase/launch/${launchId}`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Showcase launch status failed: ${res.status}`);
  }
  return res.json();
}

export async function getProjectTestsCatalog(projectId: string): Promise<{ project_id: string; project_type: string; tests: TestCatalogItem[] }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/catalog`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Project test catalog failed: ${res.status}`);
  }
  return res.json();
}

export async function getProjectTestsAvailable(projectId: string): Promise<{ project_id: string; project_type: string; tests: TestCatalogItem[] }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/available`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Project test availability failed: ${res.status}`);
  }
  return res.json();
}

export async function runSelectedTest(projectId: string, testId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/${testId}/run`, { method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Run selected test failed: ${res.status}`);
  }
  return res.json();
}

export async function runTestSuite(projectId: string): Promise<{ suite_run_id: string; summary: Record<string, unknown>; results: TestRunResult[] }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/run-suite`, { method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Run test suite failed: ${res.status}`);
  }
  return res.json();
}

export async function getRunResult(runId: string): Promise<RunResult> {
  const res = await apiFetch(`${API_BASE}/runs/${runId}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Run result fetch failed: ${res.status}`);
  }
  return res.json();
}

export async function runGenesisScene(projectId: string, steps = 240): Promise<RunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/run-scene?steps=${steps}`, { method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Genesis run-scene failed: ${res.status}`);
  }
  return res.json();
}

export async function runNativeGenesisViewer(projectId: string, steps = 600): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/native-viewer/run?steps=${steps}`, { method: "POST" });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Native viewer run failed: ${res.status}`);
  }
  return res.json();
}

export async function getProjectDofs(projectId: string): Promise<{ count: number; dofs: Array<Record<string, unknown>>; robot_description_type?: string }> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/dofs`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Project DOFs fetch failed: ${res.status}`);
  return res.json();
}

export async function applyJointTargets(projectId: string, targets: number[], steps = 60): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/joints/apply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ targets, steps }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Apply joint targets failed: ${res.status}`);
  }
  return res.json();
}

export async function importProject(files: File[], options: { projectName: string; importMode: "robot_mechanism" | "cad_geometry_only" | "buildables_package" }): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append("project_name", options.projectName);
  formData.append("import_mode", options.importMode);
  for (const file of files) {
    formData.append("files", file, (file as File & { webkitRelativePath?: string }).webkitRelativePath || file.name);
  }
  const res = await apiFetch(`${API_BASE}/projects/import`, {
    method: "POST",
    body: formData,
    timeoutMs: AGENTIC_PREFLIGHT_TIMEOUT_MS,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Project import failed: ${res.status}`);
  }
  return res.json();
}

export async function uploadProjectAssets(projectId: string, files: File[]): Promise<Record<string, unknown>> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file, file.webkitRelativePath || file.name);
  }
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/assets/upload`, {
    method: "POST",
    body: form,
    timeoutMs: AGENTIC_PREFLIGHT_TIMEOUT_MS,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Asset upload failed: ${res.status}`);
  }
  return res.json();
}

export async function getImportValidation(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/import-validation`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Import validation fetch failed: ${res.status}`);
  return res.json();
}

export async function inspectProjectStep(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/step/inspect`, { cache: "no-store" });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `STEP inspect failed: ${res.status}`);
  }
  return res.json();
}

export async function generateMeshesFromStep(
  projectId: string,
  payload: { mappings?: Record<string, string>; whole_preview?: boolean },
): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/step/generate-meshes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      mappings: payload.mappings ?? {},
      whole_preview: payload.whole_preview ?? false,
    }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: string | Record<string, unknown> }).detail;
    if (typeof detail === "object" && detail !== null) {
      throw new Error(String((detail as { message?: string }).message ?? JSON.stringify(detail)));
    }
    throw new Error(String(detail ?? `STEP mesh generation failed: ${res.status}`));
  }
  return res.json();
}

export async function getStepConverterStatus(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/step/converter-status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`STEP converter status failed: ${res.status}`);
  return res.json();
}

export async function activateProject(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/activate`, { method: "POST" });
  if (!res.ok) throw new Error(`Activate project failed: ${res.status}`);
  return res.json();
}

export async function clearActiveProject(): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/active/clear`, { method: "POST" });
  if (!res.ok) throw new Error(`Clear active project failed: ${res.status}`);
  return res.json();
}

export async function getActiveProject(): Promise<{ project_id: string | null; project_name?: string; project_mode?: string }> {
  const res = await apiFetch(`${API_BASE}/projects/active`, { cache: "no-store", timeoutMs: API_BOOT_TIMEOUT_MS });
  if (!res.ok) throw new Error(`Get active project failed: ${res.status}`);
  return res.json();
}

export async function getProjectAssetResolutionStatus(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/assets/resolution-status`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Resolution status fetch failed: ${res.status}`);
  return res.json();
}

export async function getProjectRobotDescription(projectId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/robot-description`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Robot description fetch failed: ${res.status}`);
  return res.json();
}

export async function runPassiveGravityTest(projectId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/passive-gravity/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Passive gravity test failed: ${res.status}`);
  return res.json();
}

export async function runJointSweepTest(projectId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/joint-sweep/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Joint sweep test failed: ${res.status}`);
  return res.json();
}

export async function runMechanismMotionTest(projectId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/mechanism-motion/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Mechanism motion test failed: ${res.status}`);
  return res.json();
}

export async function runControlScriptTest(projectId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/control-script/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Control script test failed: ${res.status}`);
  return res.json();
}

export async function runVisualCollisionAlignmentTest(projectId: string): Promise<TestRunResult> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/tests/visual-collision-alignment/run`, { method: "POST" });
  if (!res.ok) throw new Error(`Visual collision alignment test failed: ${res.status}`);
  return res.json();
}
