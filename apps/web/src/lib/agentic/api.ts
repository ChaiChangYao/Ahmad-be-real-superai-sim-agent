import { AGENTIC_PREFLIGHT_TIMEOUT_MS, apiFetch, importProject, uploadProjectAssets } from "../api";
import { AGENTIC_API_BASE } from "./config";
import type {
  AgenticErrorDetail,
  AgenticProjectState,
  CadBridgeResult,
  CodeGenResult,
  ExecutionFailure,
  EngineeringReport,
  ExecutionRun,
  GeneratedScriptDetail,
  ReporterResult,
  RunManifest,
  RunSummary,
  GoalParseResult,
  ProjectInspectionReport,
  RecoveryResult,
  SimulationPlan,
  SimulationTestSpec,
  TestReadinessResult,
  UploadedAsset,
} from "./types";

export class AgenticApiError extends Error {
  detail: AgenticErrorDetail | string;

  constructor(message: string, detail: AgenticErrorDetail | string) {
    super(message);
    this.name = "AgenticApiError";
    this.detail = detail;
  }

  toDetail(): AgenticErrorDetail {
    if (typeof this.detail === "object") return this.detail;
    return {
      error_code: "api_error",
      title: "Request failed",
      explanation: this.detail,
      affected_files: [],
      suggested_actions: ["Retry the action or check the session log for details."],
      copyable_debug_details: String(this.detail),
    };
  }
}

async function parseJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = (body as { detail?: unknown }).detail;
    if (typeof detail === "object" && detail !== null && "explanation" in detail) {
      const d = detail as AgenticErrorDetail;
      throw new AgenticApiError(d.explanation, d);
    }
    const msg = typeof detail === "string" ? detail : res.statusText;
    throw new AgenticApiError(msg || `Request failed (${res.status})`, msg);
  }
  return res.json() as Promise<T>;
}

const base = AGENTIC_API_BASE;

function preflightFetch(input: string, init?: RequestInit): Promise<Response> {
  return apiFetch(input, { ...init, timeoutMs: AGENTIC_PREFLIGHT_TIMEOUT_MS });
}

export type LlmSettings = {
  enable_llm_assistant: boolean;
  enable_llm_reporter: boolean;
  openrouter_api_key_set: boolean;
  openrouter_base_url: string;
  openrouter_model: string;
};

export async function getLlmSettings(): Promise<LlmSettings> {
  const res = await apiFetch(`${base}/settings/llm`, { cache: "no-store" });
  return parseJson(res);
}

export async function getDependencyStatus(): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${base}/agentic/dependencies`, { cache: "no-store" });
  return parseJson(res);
}

export type CadRecoverStatus = {
  available?: boolean;
  can_recover?: boolean;
  step_files?: string[];
  dependency?: string;
  install_hint?: string;
  fallback?: string;
};

export async function getRecoverStatus(projectId: string): Promise<CadRecoverStatus> {
  const res = await apiFetch(`${base}/projects/${projectId}/recover/status`, { cache: "no-store" });
  return parseJson(res);
}

export async function scanProject(projectId: string): Promise<{ assets: UploadedAsset[]; count: number }> {
  const res = await preflightFetch(`${base}/projects/${projectId}/scan`, { method: "POST" });
  return parseJson(res);
}

export async function inspectProject(projectId: string): Promise<ProjectInspectionReport> {
  const res = await preflightFetch(`${base}/projects/${projectId}/inspect`, { method: "POST" });
  return parseJson(res);
}

export async function parseGoal(projectId: string, userGoal: string): Promise<GoalParseResult> {
  const res = await preflightFetch(`${base}/projects/${projectId}/parse-goal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_goal: userGoal }),
  });
  return parseJson(res);
}

export async function createSimulationPlan(
  projectId: string,
  userGoal?: string | null,
): Promise<SimulationPlan> {
  const res = await preflightFetch(`${base}/projects/${projectId}/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_goal: userGoal ?? null }),
  });
  return parseJson(res);
}

export async function getTestRequirements(projectId: string): Promise<{
  project_id: string;
  specs: SimulationTestSpec[];
  readiness: TestReadinessResult[];
}> {
  const res = await preflightFetch(`${base}/projects/${projectId}/test-requirements`, { cache: "no-store" });
  return parseJson(res);
}

export async function recoverStepPreview(projectId: string): Promise<RecoveryResult> {
  const res = await preflightFetch(`${base}/projects/${projectId}/recover/step-preview`, { method: "POST" });
  return parseJson(res);
}

export async function recoverMissingMeshes(projectId: string): Promise<RecoveryResult> {
  const res = await preflightFetch(`${base}/projects/${projectId}/recover/missing-meshes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ missing_meshes: [] }),
  });
  return parseJson(res);
}

export async function getAgenticState(projectId: string): Promise<{ state: AgenticProjectState | null }> {
  const res = await apiFetch(`${base}/projects/${projectId}/agentic-state`, { cache: "no-store" });
  return parseJson(res);
}

export async function saveAgenticState(projectId: string, state: Partial<AgenticProjectState>): Promise<AgenticProjectState> {
  const res = await apiFetch(`${base}/projects/${projectId}/agentic-state`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ project_id: projectId, ...state }),
  });
  return parseJson(res);
}

export async function generateSafeDefaults(
  projectId: string,
  testId: string,
  selectedOptions?: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const res = await preflightFetch(`${base}/projects/${projectId}/generate-defaults`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ test_id: testId, selected_options: selectedOptions ?? null }),
  });
  return parseJson(res);
}

export async function cadBridgeMissingMeshes(projectId: string): Promise<CadBridgeResult> {
  const res = await apiFetch(`${base}/projects/${projectId}/cad-bridge/missing-meshes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ missing_meshes: [] }),
  });
  return parseJson(res);
}

export async function uploadProjectFiles(
  projectId: string,
  files: File[],
): Promise<Record<string, unknown>> {
  return uploadProjectAssets(projectId, files);
}

export async function uploadProjectZip(
  projectId: string,
  zipFile: File,
): Promise<Record<string, unknown>> {
  return uploadProjectAssets(projectId, [zipFile]);
}

export async function importNewProject(
  files: File[],
  projectName: string,
): Promise<Record<string, unknown>> {
  return importProject(files, { projectName, importMode: "robot_mechanism" });
}

export async function runPreflight(
  projectId: string,
  userGoal?: string | null,
): Promise<{ inspection: ProjectInspectionReport; plan: SimulationPlan }> {
  await scanProject(projectId);
  const inspection = await inspectProject(projectId);
  const plan = await createSimulationPlan(projectId, userGoal);
  return { inspection, plan };
}

export async function generateGenesisScript(
  projectId: string,
  testId: string,
  options?: { fallback_mode?: string | null; user_parameters?: Record<string, unknown> },
): Promise<CodeGenResult> {
  const res = await preflightFetch(`${base}/projects/${projectId}/generate-script`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      test_id: testId,
      fallback_mode: options?.fallback_mode ?? null,
      user_parameters: options?.user_parameters ?? null,
    }),
  });
  return parseJson(res);
}

export async function listGeneratedScripts(
  projectId: string,
): Promise<{ project_id: string; scripts: Array<Record<string, unknown>> }> {
  const res = await apiFetch(`${base}/projects/${projectId}/generated-scripts`, { cache: "no-store" });
  return parseJson(res);
}

export async function getGeneratedScript(
  projectId: string,
  scriptId: string,
): Promise<GeneratedScriptDetail> {
  const res = await apiFetch(`${base}/projects/${projectId}/generated-scripts/${scriptId}`, {
    cache: "no-store",
  });
  return parseJson(res);
}

export async function deleteGeneratedScript(projectId: string, scriptId: string): Promise<void> {
  const res = await apiFetch(`${base}/projects/${projectId}/generated-scripts/${scriptId}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    await parseJson(res);
  }
}

export async function startAgenticRun(
  projectId: string,
  body: {
    script_id: string;
    test_id?: string;
    backend?: string;
    timeout_seconds?: number;
  },
): Promise<ExecutionRun> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      script_id: body.script_id,
      test_id: body.test_id ?? "",
      backend: body.backend ?? "local",
      mode: "web",
      timeout_seconds: body.timeout_seconds ?? 300,
    }),
  });
  return parseJson(res);
}

export async function getAgenticRun(projectId: string, runId: string): Promise<ExecutionRun> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}`, { cache: "no-store" });
  return parseJson(res);
}

export async function cancelAgenticRun(projectId: string, runId: string): Promise<ExecutionRun> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/cancel`, { method: "POST" });
  return parseJson(res);
}

export async function getAgenticRunLogs(
  projectId: string,
  runId: string,
  tail = 200,
): Promise<{ stdout: string; stderr: string; combined: string }> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/logs?tail=${tail}`, {
    cache: "no-store",
  });
  return parseJson(res);
}

export async function getAgenticRunManifest(
  projectId: string,
  runId: string,
  partial = false,
): Promise<RunManifest> {
  const res = await apiFetch(
    `${base}/projects/${projectId}/runs/${runId}/manifest${partial ? "?partial=true" : ""}`,
    { cache: "no-store" },
  );
  return parseJson(res);
}

export async function getAgenticRunReplay(projectId: string, runId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/replay`, { cache: "no-store" });
  return parseJson(res);
}

export async function getAgenticRunTelemetry(projectId: string, runId: string): Promise<Record<string, unknown>> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/telemetry`, { cache: "no-store" });
  return parseJson(res);
}

export async function generateAgenticReport(
  projectId: string,
  runId: string,
  options?: { use_llm?: boolean; force?: boolean },
): Promise<ReporterResult> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ use_llm: options?.use_llm ?? false, force: options?.force ?? false }),
  });
  return parseJson(res);
}

export async function getAgenticReport(projectId: string, runId: string): Promise<EngineeringReport> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/report`, { cache: "no-store" });
  return parseJson(res);
}

export async function getAgenticReportMarkdown(projectId: string, runId: string): Promise<string> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/report.md`, { cache: "no-store" });
  if (!res.ok) throw new AgenticApiError(res.statusText, res.statusText);
  return res.text();
}

export async function getAgenticRunSummary(projectId: string, runId: string): Promise<RunSummary> {
  const res = await apiFetch(`${base}/projects/${projectId}/runs/${runId}/summary`, { cache: "no-store" });
  return parseJson(res);
}
