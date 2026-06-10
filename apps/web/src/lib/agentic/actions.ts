/**
 * Agent tool/action layer — used by UI buttons and future CopilotKit tools.
 */
import {
  AgenticApiError,
  cadBridgeMissingMeshes,
  createSimulationPlan,
  cancelAgenticRun,
  generateAgenticReport,
  generateGenesisScript,
  getAgenticRun,
  getAgenticRunLogs,
  getAgenticRunManifest,
  getAgenticRunReplay,
  getAgenticRunTelemetry,
  startAgenticRun,
  generateSafeDefaults,
  getTestRequirements,
  importNewProject,
  inspectProject,
  recoverMissingMeshes,
  recoverStepPreview,
  runPreflight,
  scanProject,
  uploadProjectFiles,
} from "./api";
import type {
  AgenticErrorDetail,
  AgentMessage,
  AgentTimelineStepId,
  AgentTimelineStepStatus,
  CadBridgeResult,
  CodeGenResult,
  EngineeringReport,
  ExecutionRun,
  ProjectInspectionReport,
  RecoveryResult,
  SimulationPlan,
  SimulationTestSpec,
  TestReadinessResult,
  UploadDiagnostics,
} from "./types";
import { hasRunIntent } from "./timeline";

export type ActionLogFn = (msg: string) => void;

export type InspectResult = {
  inspection: ProjectInspectionReport;
  assets: ProjectInspectionReport["assets"];
};

export type RecommendResult = {
  plan: SimulationPlan;
  specs: SimulationTestSpec[];
  readiness: TestReadinessResult[];
};

export type ExplainResult = {
  testId: string | null;
  missingMeshes: ProjectInspectionReport["robot_descriptions"][0]["mesh_references"];
  missingMetadata: Array<{ key: string; label: string; status: string; action: string }>;
  blockers: string[];
  explanation: string;
};


export async function inspectUploadedFiles(
  projectId: string,
  onLog?: ActionLogFn,
): Promise<InspectResult> {
  onLog?.(`[Assistant] Scanning project ${projectId}…`);
  await scanProject(projectId);
  onLog?.("[Assistant] Inspecting URDF, meshes, and assets…");
  const inspection = await inspectProject(projectId);
  onLog?.(`[Assistant] Found ${inspection.assets.length} assets, ${inspection.missing_mesh_count} missing meshes.`);
  return { inspection, assets: inspection.assets };
}

export async function recommendTests(
  projectId: string,
  userGoal: string | null,
  onLog?: ActionLogFn,
): Promise<RecommendResult> {
  onLog?.(`[Assistant] Building simulation plan${userGoal ? ` for: ${userGoal}` : ""}…`);
  const [plan, req] = await Promise.all([
    createSimulationPlan(projectId, userGoal),
    getTestRequirements(projectId),
  ]);
  onLog?.(
    `[Assistant] ${plan.recommended_tests.length} recommended, ${plan.blocked_tests.length} blocked.`,
  );
  return { plan, specs: req.specs, readiness: req.readiness };
}

export async function explainMissingRequirements(
  projectId: string,
  testId?: string | null,
  onLog?: ActionLogFn,
): Promise<ExplainResult> {
  const { inspection, plan, specs, readiness } = await (async () => {
    const pre = await runPreflight(projectId);
    const req = await getTestRequirements(projectId);
    return { inspection: pre.inspection, plan: pre.plan, specs: req.specs, readiness: req.readiness };
  })();

  const target = testId
    ? readiness.find((r) => r.test_id === testId)
    : [...plan.blocked_tests, ...plan.recommended_tests][0];

  const missingMeshes = inspection.robot_descriptions.flatMap((r) =>
    r.mesh_references.filter((m) => m.status === "missing"),
  );

  const missingMetadata: ExplainResult["missingMetadata"] = [];
  if (target) {
    for (const req of target.missing_required) {
      missingMetadata.push({
        key: req,
        label: req.replace(/_/g, " "),
        status: "missing",
        action: target.suggested_actions[0] ?? "Upload or configure required input",
      });
    }
    for (const q of target.required_user_questions) {
      missingMetadata.push({
        key: "user_choice",
        label: q,
        status: "needs_choice",
        action: "Use safe defaults or answer in chat",
      });
    }
  }

  const spec = testId ? specs.find((s) => s.test_id === testId) : undefined;
  const explanation = target
    ? `${spec?.display_name ?? target.test_id}: ${target.blockers[0] ?? "See missing items below."}`
    : `Project has ${inspection.missing_mesh_count} missing mesh references.`;

  onLog?.(`[Assistant] ${explanation}`);
  return {
    testId: testId ?? target?.test_id ?? null,
    missingMeshes,
    missingMetadata,
    blockers: target?.blockers ?? [],
    explanation,
  };
}

export async function generateSafeDefaultsAction(
  projectId: string,
  testId: string,
  userChoices?: Record<string, unknown>,
  onLog?: ActionLogFn,
): Promise<Record<string, unknown>> {
  onLog?.(`[Assistant] Generating safe defaults for ${testId}…`);
  const result = await generateSafeDefaults(projectId, testId, userChoices);
  onLog?.(`[Assistant] ${String(result.message ?? "Defaults saved.")}`);
  return result;
}

export async function recoverFromStep(
  projectId: string,
  mode: "preview" | "missing_meshes",
  onLog?: ActionLogFn,
): Promise<RecoveryResult> {
  onLog?.(`[Assistant] STEP recovery (${mode})…`);
  const result =
    mode === "preview" ? await recoverStepPreview(projectId) : await recoverMissingMeshes(projectId);
  onLog?.(`[Assistant] ${result.explanation}`);
  return result;
}

export async function askBuildablesCad(
  projectId: string,
  onLog?: ActionLogFn,
): Promise<CadBridgeResult> {
  onLog?.("[Assistant] Requesting Buildables CAD generation (stub)…");
  const result = await cadBridgeMissingMeshes(projectId);
  onLog?.(`[Assistant] ${result.explanation}`);
  return result;
}

export async function prepareGenesisScript(
  projectId: string,
  testId: string,
  onLog?: ActionLogFn,
  options?: { fallback_mode?: string | null; user_parameters?: Record<string, unknown> },
): Promise<CodeGenResult> {
  onLog?.(`[Assistant] Generating Genesis script for ${testId}…`);
  const result = await generateGenesisScript(projectId, testId, options);
  if (result.success) {
    onLog?.(`[Assistant] Script ${result.script_id} generated (${result.template_id}).`);
  } else {
    onLog?.(`[Assistant] Codegen blocked: ${result.explanation}`);
  }
  return result;
}

export async function runSimulation(
  projectId: string,
  testId: string,
  onLog?: ActionLogFn,
  options?: { script_id: string; timeout_seconds?: number },
): Promise<ExecutionRun> {
  if (!options?.script_id) {
    throw new Error("Generate a Genesis script before running the simulation.");
  }
  onLog?.(`[Assistant] Starting agentic run for ${testId} (${options.script_id})…`);
  const run = await startAgenticRun(projectId, {
    script_id: options.script_id,
    test_id: testId,
    timeout_seconds: options.timeout_seconds,
  });
  onLog?.(`[Assistant] Run ${run.run_id} started (backend=${run.backend}).`);
  return run;
}

export type AgenticRunPollCallbacks = {
  onLog?: ActionLogFn;
  onStatus?: (run: ExecutionRun) => void;
  onLifecycle?: (lifecycle: string) => void;
  onReplay?: (data: Record<string, unknown>) => void;
  onFailure?: (detail: {
    title: string;
    failureDetail: string;
    suggestedFix?: string;
    logs?: string;
    scriptPath?: string;
  }) => void;
};

export async function pollAgenticRun(
  projectId: string,
  runId: string,
  callbacks: AgenticRunPollCallbacks,
): Promise<ExecutionRun> {
  const TERMINAL = new Set(["completed", "failed", "cancelled", "timed_out"]);
  let logOffset = { stdout: 0, stderr: 0 };

  for (let i = 0; i < 300; i++) {
    await new Promise((r) => setTimeout(r, i === 0 ? 500 : 1200));
    const run = await getAgenticRun(projectId, runId);
    callbacks.onStatus?.(run);
    callbacks.onLifecycle?.(run.status);

    try {
      const logs = await getAgenticRunLogs(projectId, runId, 5000);
      if (logs.stdout.length > logOffset.stdout) {
        const chunk = logs.stdout.slice(logOffset.stdout);
        logOffset.stdout = logs.stdout.length;
        for (const line of chunk.split(/\r?\n/)) {
          if (line.trim()) callbacks.onLog?.(`[stdout] ${line}`);
        }
      }
      if (logs.stderr.length > logOffset.stderr) {
        const chunk = logs.stderr.slice(logOffset.stderr);
        logOffset.stderr = logs.stderr.length;
        for (const line of chunk.split(/\r?\n/)) {
          if (line.trim()) callbacks.onLog?.(`[stderr] ${line}`);
        }
      }
    } catch {
      /* logs not ready */
    }

    if (run.status === "recording" || run.status === "running") {
      try {
        const manifest = await getAgenticRunManifest(projectId, runId, true);
        if (manifest.visual?.hasReplay && manifest.status !== "complete") {
          callbacks.onLifecycle?.("receiving_frames");
        }
      } catch {
        /* manifest not ready */
      }
    }

    if (TERMINAL.has(run.status)) {
      try {
        const manifest = await getAgenticRunManifest(projectId, runId, true);
        const hasReplay =
          Boolean(manifest.visual?.hasReplay) &&
          (manifest.status === "complete" || Number(manifest.visual?.frameCount ?? 0) > 0);
        if (hasReplay) {
          const replay = await getAgenticRunReplay(projectId, runId);
          let telemetry: Record<string, unknown> | undefined;
          if (manifest.telemetry?.hasTelemetry) {
            try {
              telemetry = await getAgenticRunTelemetry(projectId, runId);
            } catch {
              /* optional */
            }
          }
          callbacks.onReplay?.({ ...replay, telemetry, manifest });
        }
      } catch (err) {
        callbacks.onLog?.(`[Assistant] Replay load: ${err instanceof Error ? err.message : String(err)}`);
      }

      if (run.status !== "completed") {
        const logs = await getAgenticRunLogs(projectId, runId, 500).catch(() => ({
          stdout: "",
          stderr: "",
          combined: "",
        }));
        callbacks.onFailure?.({
          title: run.status === "failed" ? "Simulation run failed" : `Simulation run ${run.status}`,
          failureDetail: run.error_summary || run.status,
          suggestedFix: (run.failure as { suggested_fix?: string } | null)?.suggested_fix,
          logs: logs.combined || logs.stderr,
          scriptPath: run.run_dir,
        });
      }
      callbacks.onLog?.(`[Assistant] Run ${runId} → ${run.status}`);
      return run;
    }
  }

  await cancelAgenticRun(projectId, runId);
  throw new Error("Timed out waiting for simulation run.");
}

export async function generateEngineeringReport(
  projectId: string,
  runId: string,
  onLog?: ActionLogFn,
): Promise<EngineeringReport> {
  onLog?.(`[Assistant] Generating engineering report for ${runId}…`);
  const result = await generateAgenticReport(projectId, runId);
  if (!result.success || !result.report) {
    throw new Error(result.error || "Report generation failed");
  }
  onLog?.(`[Assistant] Report ${result.report.report_id} — ${result.report.outcome.label}`);
  return result.report;
}

export type TimelineUpdater = (
  stepId: AgentTimelineStepId,
  status: AgentTimelineStepStatus,
  detail?: string,
  error?: string,
) => void;

export type EntryPipelineResult = {
  projectId: string;
  inspection: ProjectInspectionReport;
  plan: SimulationPlan;
  specs: SimulationTestSpec[];
  uploadDiagnostics?: UploadDiagnostics | null;
};

export async function runAgenticEntryPipeline(
  projectId: string | null,
  files: File[],
  projectName: string,
  userGoal: string | null,
  onTimeline: TimelineUpdater,
  onLog?: ActionLogFn,
): Promise<EntryPipelineResult> {
  let pid = projectId;
  let uploadDiagnostics: UploadDiagnostics | null = null;
  const hasZip = files.some((f) => f.name.toLowerCase().endsWith(".zip"));

  onTimeline("user_submitted", "done");
  onTimeline("uploading", "running");

  if (!pid) {
    onLog?.(`[Assistant] Importing ${files.length} file(s) as new project…`);
    const imported = await importNewProject(files, projectName);
    pid = String(imported.project_id);
    uploadDiagnostics = (imported.upload_diagnostics as UploadDiagnostics) ?? null;
    onLog?.(`[Assistant] Created project ${pid}`);
  } else {
    onLog?.(`[Assistant] Uploading ${files.length} file(s) to ${pid}…`);
    const uploaded = await uploadProjectFiles(pid, files);
    uploadDiagnostics = (uploaded.upload_diagnostics as UploadDiagnostics) ?? null;
  }
  onTimeline("uploading", "done", formatDiagShort(uploadDiagnostics));

  if (hasZip) {
    onTimeline("extracting_zip", "running");
    if (uploadDiagnostics?.zip_errors?.length) {
      onTimeline("extracting_zip", "failed", undefined, uploadDiagnostics.zip_errors.join("; "));
      throw new Error(uploadDiagnostics.zip_errors.join("; "));
    }
    onTimeline(
      "extracting_zip",
      "done",
      uploadDiagnostics
        ? `${uploadDiagnostics.extracted_file_count ?? 0} files from zip`
        : "Zip processed",
    );
  } else {
    onTimeline("extracting_zip", "skipped", "No zip uploaded");
  }

  onTimeline("scanning_assets", "running");
  await scanProject(pid);
  onTimeline("scanning_assets", "done");

  onTimeline("inspecting_robot_description", "running");
  const inspection = await inspectProject(pid);
  const robot = inspection.robot_descriptions.find((r) => r.parsed);
  const inspectDetail = robot
    ? `${robot.links_count} links, ${robot.joints_count} joints (${robot.movable_joints_count} movable)`
    : `${inspection.assets.length} assets`;
  onTimeline("inspecting_robot_description", "done", inspectDetail);

  onTimeline("checking_meshes", "running");
  const meshDetail = `${inspection.missing_mesh_count} missing of ${robot?.mesh_references.length ?? 0} refs`;
  onTimeline("checking_meshes", inspection.missing_mesh_count > 0 ? "done" : "done", meshDetail);

  onTimeline("planning_tests", "running");
  const [plan, req] = await Promise.all([
    createSimulationPlan(pid, userGoal),
    getTestRequirements(pid),
  ]);
  const planDetail = plan.selected_test
    ? `Selected: ${plan.selected_test}`
    : `${plan.recommended_tests.length} recommended`;
  onTimeline("planning_tests", "done", planDetail);

  if (plan.goal_parse?.needs_clarification) {
    onTimeline("needs_clarification", "running");
    onTimeline("needs_clarification", "done", "Waiting for your choice");
  }

  onLog?.(`[Assistant] Preflight complete for ${pid}`);
  return {
    projectId: pid,
    inspection,
    plan,
    specs: req.specs,
    uploadDiagnostics,
  };
}

function formatDiagShort(diag: UploadDiagnostics | null | undefined): string {
  if (!diag) return "";
  const parts: string[] = [];
  if (diag.extracted_file_count) parts.push(`${diag.extracted_file_count} files`);
  if (diag.urdf_count) parts.push(`${diag.urdf_count} URDF`);
  if (diag.mesh_count) parts.push(`${diag.mesh_count} meshes`);
  return parts.join(", ");
}

export function pickAutoRunTest(
  plan: SimulationPlan,
  readiness: TestReadinessResult[],
): { testId: string; fallbackMode?: string } | null {
  const candidate = plan.selected_test;
  if (!candidate) return null;
  const row = readiness.find((r) => r.test_id === candidate);
  if (!row) return null;
  if (row.can_run) return { testId: candidate };
  if (row.can_run_with_fallback) {
    return { testId: candidate, fallbackMode: "skeleton" };
  }
  return null;
}

export async function autoRunAgenticTest(
  projectId: string,
  testId: string,
  onTimeline: TimelineUpdater,
  onLog: ActionLogFn | undefined,
  runHook: (scriptId: string, testId: string) => Promise<void>,
  options?: { fallbackMode?: string },
): Promise<CodeGenResult | null> {
  onTimeline("ready_to_generate", "done", testId);
  onTimeline("generating_script", "running");
  const codegen = await prepareGenesisScript(projectId, testId, onLog, {
    fallback_mode: options?.fallbackMode ?? null,
    user_parameters: { duration_seconds: 4 },
  });
  if (!codegen.success || !codegen.script_id) {
    onTimeline("generating_script", "failed", undefined, codegen.explanation);
    return codegen;
  }
  onTimeline("generating_script", "done");
  onTimeline("script_generated", "done", codegen.script_path);
  onTimeline("running_simulation", "running");
  await runHook(codegen.script_id, testId);
  onTimeline("running_simulation", "done");
  return codegen;
}

export async function uploadAndPreflight(
  projectId: string | null,
  files: File[],
  projectName: string,
  userGoal: string | null,
  onLog?: ActionLogFn,
): Promise<{ projectId: string; inspection: ProjectInspectionReport; plan: SimulationPlan }> {
  const result = await runAgenticEntryPipeline(
    projectId,
    files,
    projectName,
    userGoal,
    () => undefined,
    onLog,
  );
  return { projectId: result.projectId, inspection: result.inspection, plan: result.plan };
}

export function toAgenticError(err: unknown): AgenticErrorDetail {
  if (err instanceof AgenticApiError) return err.toDetail();
  const msg = err instanceof Error ? err.message : String(err);
  return {
    error_code: "unexpected_error",
    title: "Something went wrong",
    explanation: msg,
    affected_files: [],
    suggested_actions: ["Check the session log.", "Retry preflight.", "Verify API is running."],
    copyable_debug_details: msg,
  };
}
