"use client";

import { useEffect, useRef, useState } from "react";
import { activateProject, generateMeshesFromStep, getImportValidation, inspectProjectStep, uploadProjectAssets } from "@/lib/api";
import {
  getProjectLaunchReadiness,
  getProjectSensorValidation,
  getShowcaseLaunchLogs,
  getShowcaseLaunchStatus,
  getShowcaseLaunchTelemetry,
  getShowcaseLaunchTimeseries,
  launchProjectWebViewer,
  type LaunchReadiness,
} from "@/lib/genesisWorkbenchApi";
import { cancelAgenticRun, getAgenticRunLogs, getTestRequirements, saveAgenticState } from "@/lib/agentic/api";
import { isTransientPollError } from "@/lib/pollUtils";
import {
  autoRunAgenticTest,
  generateEngineeringReport,
  pickAutoRunTest,
  pollAgenticRun,
  runAgenticEntryPipeline,
  runSimulation,
  toAgenticError,
} from "@/lib/agentic/actions";
import { fetchBrainrotProjectName } from "@/lib/ai/brainrotProjectName";
import { hasRunIntent } from "@/lib/agentic/timeline";
import {
  buildGoalResponseMessages,
  buildTimelineMessage,
  buildUploadSummaryMessages,
  engineeringReportMessage,
  errorMessage,
  textMessage,
  executionStatusMessage,
  formatUploadDiagnosticsDetail,
  updateTimelineStep,
  userMessage,
  welcomeMessage,
} from "@/lib/agentic/messages";
import type { EngineeringReport, ExecutionRun } from "@/lib/agentic/types";
import { normalizeReplay, normalizeTelemetryBundle, type ReplayBundle, type ReplayViewSource } from "./replay/types";
import { useAssistantStore } from "@/lib/agentic/store";
import { BuildablesAssistant } from "./assistant/BuildablesAssistant";
import { EngineeringReportModal } from "./assistant/EngineeringReportModal";
import { ProjectEntryScreen } from "./assistant/ProjectEntryScreen";
import { getAgenticReportMarkdown } from "@/lib/agentic/api";
import { GenesisVerticalSplit } from "./GenesisWorkbenchLayout";
import { ImportValidationSummary } from "./ImportValidationSummary";

const TERMINAL = new Set(["completed", "failed", "unknown"]);
type ImportPhase = "entry" | "workbench";

const TEST_TYPES = [
  { id: "simulation", label: "Normal simulation" },
  { id: "gui", label: "GUI control" },
  { id: "imu", label: "IMU" },
  { id: "temperature_grid", label: "Temperature grid" },
  { id: "depth_camera", label: "Depth camera" },
  { id: "lidar", label: "Lidar" },
  { id: "contact_force", label: "Contact force" },
] as const;

type Props = {
  customProjectId: string | null;
  onProjectImported: (projectId: string) => void;
  onLaunchNative: (msg: string) => void;
  onReplay: (replay: ReplayBundle | null) => void;
  onLifecycle: (lifecycle: string | null) => void;
  onLaunchFailure?: (failure: import("./LaunchFailureModal").LaunchFailureInfo | null) => void;
  onAgenticRunIdChange?: (runId: string | null) => void;
  onReportChange?: (report: EngineeringReport | null) => void;
};

export function GenesisProjectImport({
  customProjectId,
  onProjectImported,
  onLaunchNative,
  onReplay,
  onLifecycle,
  onLaunchFailure,
  onAgenticRunIdChange,
  onReportChange,
}: Props) {
  const [phase, setPhase] = useState<ImportPhase>(customProjectId ? "workbench" : "entry");
  const [entryGoal, setEntryGoal] = useState("");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [entrySubmitting, setEntrySubmitting] = useState(false);
  const [legacyOpen, setLegacyOpen] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [testType, setTestType] = useState<string>("simulation");
  const [sensorValidation, setSensorValidation] = useState<Record<string, unknown> | null>(null);
  const [validation, setValidation] = useState<Record<string, unknown> | null>(null);
  const [readiness, setReadiness] = useState<LaunchReadiness | null>(null);
  const [launchingWeb, setLaunchingWeb] = useState(false);
  const [launchId, setLaunchId] = useState<string | null>(null);
  const [agenticRunId, setAgenticRunId] = useState<string | null>(null);
  const [agenticRun, setAgenticRun] = useState<ExecutionRun | null>(null);
  const [agenticLogTail, setAgenticLogTail] = useState("");
  const [agenticRunBusy, setAgenticRunBusy] = useState(false);
  const [agenticCancelling, setAgenticCancelling] = useState(false);
  const [lifecycle, setLifecycle] = useState<string | null>(null);
  const pollRef = useRef(0);
  const logOffsetRef = useRef({ stdout: 0, stderr: 0 });
  const lastFrameCountRef = useRef(0);
  const lastTelemetryCountRef = useRef(0);
  const lastReplayVersionRef = useRef(0);
  const [stepInspect, setStepInspect] = useState<Record<string, unknown> | null>(null);
  const [stepMappings, setStepMappings] = useState<Record<string, string>>({});
  const [stepBusy, setStepBusy] = useState(false);
  const setAssistantProjectName = useAssistantStore((s) => s.setProjectName);
  const assistantSelectedTest = useAssistantStore((s) => s.selectedTestId);
  const agenticPathActive = Boolean(customProjectId && assistantSelectedTest);
  const appendMessage = useAssistantStore((s) => s.appendMessage);
  const setMessages = useAssistantStore((s) => s.setMessages);
  const updateMessageById = useAssistantStore((s) => s.updateMessageById);
  const setInspection = useAssistantStore((s) => s.setInspection);
  const setPlan = useAssistantStore((s) => s.setPlan);
  const setPersistedState = useAssistantStore((s) => s.setPersistedState);
  const setLoading = useAssistantStore((s) => s.setLoading);
  const setSelectedTestId = useAssistantStore((s) => s.setSelectedTestId);
  const agenticRunStatusRef = useRef<string | null>(null);
  const [latestReport, setLatestReport] = useState<EngineeringReport | null>(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  useEffect(() => {
    if (phase !== "entry" || customProjectId) return;
    let cancelled = false;
    void fetchBrainrotProjectName().then((name) => {
      if (!cancelled && name) setProjectName(name);
    });
    return () => {
      cancelled = true;
    };
  }, [phase, customProjectId]);

  useEffect(() => {
    if (!customProjectId) {
      setSensorValidation(null);
      return;
    }
    void getProjectSensorValidation(customProjectId, testType)
      .then(setSensorValidation)
      .catch(() => setSensorValidation(null));
  }, [customProjectId, testType]);

  const sensorLaunchBlocked = Boolean(
    sensorValidation && sensorValidation.can_launch_with_sensors === false,
  );

  const isRunning = lifecycle === "launching" || lifecycle === "running" || lifecycle === "receiving_frames";
  const canLaunchWeb = readiness?.can_launch_web ?? false;
  const canPreviewSkeleton = readiness?.can_preview_skeleton_web ?? false;
  const missingMeshCount = readiness?.missing_mesh_count ?? 0;
  const firstMissingMesh = readiness?.first_missing_mesh ?? null;
  const launchSummary = (validation?.launch_summary ?? validation) as Record<string, unknown> | undefined;
  const stepUploaded = Boolean(launchSummary?.stepUploaded ?? (validation?.geometry as Record<string, unknown>)?.step_source_found);
  const canGenerateFromStep = stepUploaded && missingMeshCount > 0;
  const stepParts = (stepInspect?.parts as Array<{ name?: string }> | undefined) ?? [];
  const suggestedMappings = (stepInspect?.suggested_mappings as Array<{ urdf_mesh_path?: string; suggested_step_part?: string | null }> | undefined) ?? [];

  useEffect(() => {
    if (!customProjectId || !canGenerateFromStep) {
      setStepInspect(null);
      return;
    }
    void inspectProjectStep(customProjectId)
      .then((result) => {
        setStepInspect(result);
        const suggestions = (result.suggested_mappings as typeof suggestedMappings) ?? [];
        const initial: Record<string, string> = {};
        for (const row of suggestions) {
          if (row.urdf_mesh_path && row.suggested_step_part) {
            initial[row.urdf_mesh_path] = row.suggested_step_part;
          }
        }
        setStepMappings(initial);
      })
      .catch(() => setStepInspect(null));
  }, [customProjectId, canGenerateFromStep, missingMeshCount]);

  function setLifecycleState(next: string | null) {
    setLifecycle(next);
    onLifecycle(next);
  }

  async function refreshReadiness(projectId: string) {
    try {
      const r = await getProjectLaunchReadiness(projectId);
      setReadiness(r);
    } catch {
      setReadiness(null);
    }
  }

  useEffect(() => {
    if (!customProjectId) {
      setReadiness(null);
      return;
    }
    void refreshReadiness(customProjectId);
  }, [customProjectId, validation]);

  async function handleEntrySubmit() {
    const goal = entryGoal.trim();
    if (!goal && pendingFiles.length === 0) return;
    const names = pendingFiles.map((f) => f.name);
    const timelineMsg = buildTimelineMessage();
    const timelineId = timelineMsg.id;

    setPhase("workbench");
    setEntrySubmitting(true);
    setLoading(true);
    setMessages([
      welcomeMessage(),
      userMessage(goal || "(files only)", names.length ? names : undefined),
      timelineMsg,
    ]);

    const onTimeline = (
      stepId: import("@/lib/agentic/types").AgentTimelineStepId,
      status: import("@/lib/agentic/types").AgentTimelineStepStatus,
      detail?: string,
      error?: string,
    ) => {
      updateMessageById(timelineId, (m) => updateTimelineStep(m, stepId, status, detail, error));
    };

    try {
      const { projectId: pid, inspection, plan, specs, uploadDiagnostics } = await runAgenticEntryPipeline(
        customProjectId,
        pendingFiles,
        projectName,
        goal || null,
        onTimeline,
        onLaunchNative,
      );

      setAssistantProjectName(projectName);
      setInspection(inspection);
      setPlan(plan);

      const followUps = goal
        ? buildGoalResponseMessages(goal, inspection, plan, specs).slice(1)
        : buildUploadSummaryMessages(names, inspection, plan).slice(1);

      if (uploadDiagnostics) {
        const diagText = formatUploadDiagnosticsDetail(uploadDiagnostics);
        if (diagText) {
          followUps.unshift({
            id: `msg-diag-${Date.now()}`,
            role: "assistant",
            type: "text",
            text: `Import diagnostics: ${diagText}`,
            timestamp: new Date().toISOString(),
          });
        }
      }

      setMessages((prev) => [...prev, ...followUps]);

      await activateProject(pid);
      setValidation(null);
      await refreshReadiness(pid);

      const saved = await saveAgenticState(pid, {
        user_goal: goal || null,
        latest_plan: plan,
        latest_inspection: inspection,
        selected_test: plan.selected_test,
        chat_summary: plan.agent_explanation ?? "",
        messages: useAssistantStore.getState().messages,
      });
      setPersistedState(saved);

      onProjectImported(pid);
      setPendingFiles([]);
      setEntryGoal("");
      onLaunchNative(`[Entry] Project ${pid} ready — preflight complete.`);

      const req = await getTestRequirements(pid);
      const autoTest = pickAutoRunTest(plan, req.readiness);
      const shouldAutoRun =
        autoTest &&
        hasRunIntent(goal) &&
        !plan.goal_parse?.needs_clarification;

      if (shouldAutoRun && autoTest) {
        setSelectedTestId(autoTest.testId);
        await saveAgenticState(pid, { selected_test: autoTest.testId });
        await autoRunAgenticTest(
          pid,
          autoTest.testId,
          onTimeline,
          onLaunchNative,
          (scriptId, testId) => onRunAgentic(scriptId, testId),
          { fallbackMode: autoTest.fallbackMode },
        );
      }
    } catch (error) {
      const detail = toAgenticError(error);
      updateMessageById(timelineId, (m) => ({
        ...m,
        timelineSteps: [
          ...(m.timelineSteps ?? []),
          {
            step_id: "failed" as const,
            status: "failed" as const,
            label: "Failed",
            error: detail.explanation,
          },
        ],
      }));
      appendMessage(errorMessage(detail));
      appendMessage(
        textMessage(
          "This is likely a software import issue, not necessarily your file. Try uploading again, upload extracted meshes + URDF separately, or use Retry preflight below.",
        ),
      );
      onLaunchNative(`[Entry][Error] ${detail.explanation}`);
      if (onLaunchFailure) {
        onLaunchFailure({
          title: detail.title,
          failureDetail: detail.explanation,
          suggestedFix: detail.suggested_actions[0],
          logs: detail.copyable_debug_details,
        });
      }
    } finally {
      setEntrySubmitting(false);
      setLoading(false);
    }
  }

  async function refreshValidation() {
    if (!customProjectId) return;
    try {
      const v = await getImportValidation(customProjectId);
      setValidation(v);
      await refreshReadiness(customProjectId);
    } catch {
      setValidation(null);
    }
  }

  async function loadReplay(id: string, projectId: string, force = false, expectedFrames = 0) {
    const fetchTimeseries = () => getShowcaseLaunchTimeseries(projectId, id);

    const applyBundle = async (data: Awaited<ReturnType<typeof fetchTimeseries>>) => {
      const demoType = String((data.meta as Record<string, unknown> | undefined)?.demo_type ?? "");
      const viewSource: ReplayViewSource =
        demoType === "telemetry" || demoType === "hybrid" ? "raw" : "smooth";
      let bundle = normalizeReplay(
        {
          launch_id: data.launch_id,
          project_id: projectId,
          scene: data.scene,
          objects: data.objects as Parameters<typeof normalizeReplay>[0]["objects"],
          state_timeseries: data.state_timeseries as Parameters<typeof normalizeReplay>[0]["state_timeseries"],
          raw_frames: data.raw_frames as Parameters<typeof normalizeReplay>[0]["raw_frames"],
          preview_frames: data.preview_frames as Parameters<typeof normalizeReplay>[0]["preview_frames"],
          telemetry: data.telemetry as Parameters<typeof normalizeReplay>[0]["telemetry"],
          meta: data.meta,
        },
        projectId,
        id,
        viewSource,
      );

      const metaTeleCount = Number(bundle.meta.telemetry_sample_count ?? 0);
      const teleCount = bundle.telemetry?.timestamps?.length ?? 0;
      const isSensorDemo = demoType === "telemetry" || demoType === "hybrid";
      if (isSensorDemo && teleCount === 0 && (metaTeleCount > 0 || force)) {
        try {
          const telePayload = await getShowcaseLaunchTelemetry(projectId, id);
          const resolved = normalizeTelemetryBundle(telePayload.telemetry);
          if (resolved?.timestamps?.length) {
            bundle = { ...bundle, telemetry: resolved };
          }
        } catch {
          /* optional until API restart */
        }
      }

      const frameCount = bundle.frames.length;
      const resolvedTeleCount = bundle.telemetry?.timestamps?.length ?? 0;
      if (
        !force &&
        frameCount > 0 &&
        frameCount <= lastFrameCountRef.current &&
        resolvedTeleCount <= lastTelemetryCountRef.current
      ) {
        return frameCount;
      }
      if (frameCount > lastFrameCountRef.current || resolvedTeleCount > lastTelemetryCountRef.current || force) {
        lastFrameCountRef.current = Math.max(lastFrameCountRef.current, frameCount);
        lastTelemetryCountRef.current = Math.max(lastTelemetryCountRef.current, resolvedTeleCount);
        onReplay(bundle);
        if (frameCount > 0) {
          onLaunchNative(`[Web] Replay loaded (${frameCount} frames, ${bundle.objects.length} objects).`);
        }
      }
      return frameCount;
    };

    try {
      return await applyBundle(await fetchTimeseries());
    } catch {
      if (expectedFrames > 0) {
        await new Promise((r) => setTimeout(r, 350));
        try {
          return await applyBundle(await fetchTimeseries());
        } catch {
          return 0;
        }
      }
      return 0;
    }
  }

  function shouldReloadReplay(replayVersion: number): boolean {
    if (replayVersion > lastReplayVersionRef.current) {
      lastReplayVersionRef.current = replayVersion;
      return true;
    }
    return false;
  }

  async function pollLogs(id: string, projectId: string) {
    try {
      const logs = await getShowcaseLaunchLogs(projectId, id);
      const { stdout, stderr } = logs;
      if (stdout.length > logOffsetRef.current.stdout) {
        const chunk = stdout.slice(logOffsetRef.current.stdout);
        logOffsetRef.current.stdout = stdout.length;
        for (const line of chunk.split(/\r?\n/)) {
          if (line.trim()) onLaunchNative(`[stdout] ${line}`);
        }
      }
      if (stderr.length > logOffsetRef.current.stderr) {
        const chunk = stderr.slice(logOffsetRef.current.stderr);
        logOffsetRef.current.stderr = stderr.length;
        for (const line of chunk.split(/\r?\n/)) {
          if (line.trim()) onLaunchNative(`[stderr] ${line}`);
        }
      }
    } catch {
      /* logs not ready */
    }
  }

  async function pollStatus(id: string, projectId: string, pollToken: number) {
    for (let i = 0; i < 240; i++) {
      if (pollRef.current !== pollToken) return;
      await new Promise((r) => setTimeout(r, i === 0 ? 600 : 1200));
      if (pollRef.current !== pollToken) return;
      try {
        await pollLogs(id, projectId);
        const status = await getShowcaseLaunchStatus(projectId, id);
        if (pollRef.current !== pollToken) return;
        setLifecycleState(String(status.lifecycle ?? status.status ?? "running"));
        if (status.replay_available || Number(status.replay_frames) > 0) {
          const replayVersion = Number(status.replay_version ?? 0);
          const replayReady = status.replay_ready !== false;
          const replayPartial = status.replay_partial === true;
          const terminal = TERMINAL.has(String(status.status));
          if ((replayReady || replayPartial) && (shouldReloadReplay(replayVersion) || terminal)) {
            await loadReplay(id, projectId, terminal, Number(status.replay_frames));
          }
        }
        if (status.status === "failed") {
          const detail = String(status.failure_detail ?? status.error_summary ?? "Launch failed");
          onLaunchNative(`[Web][Error] ${detail}`);
          onLaunchFailure?.({
            title: "Project launch failed",
            failureCode: status.failure_code ? String(status.failure_code) : null,
            failureDetail: detail,
            suggestedFix: status.suggested_fix ? String(status.suggested_fix) : null,
          });
        }
        if (TERMINAL.has(String(status.status))) {
          await pollLogs(id, projectId);
          onLaunchNative(`[Web] ${id} → ${status.status}`);
          if (status.status === "completed") {
            const frames = await loadReplay(id, projectId, true);
            if (frames === 0) {
              onLaunchNative("[Web][Error] Simulation finished but no replay frames were recorded.");
              setLifecycleState("failed");
            }
          }
          return;
        }
      } catch (error) {
        const msg = (error as Error).message;
        if (isTransientPollError(msg)) {
          onLaunchNative(`[Web][Poll] ${msg} — still running, retrying…`);
          continue;
        }
        onLaunchNative(`[Web][Poll] ${msg}`);
        setLifecycleState("failed");
        return;
      }
    }
    setLifecycleState("failed");
    onLaunchNative("[Web] Timed out waiting for simulation.");
  }

  async function onCancelAgenticRun() {
    if (!customProjectId || !agenticRunId || agenticCancelling) return;
    setAgenticCancelling(true);
    try {
      const updated = await cancelAgenticRun(customProjectId, agenticRunId);
      setAgenticRun(updated);
      setLifecycleState(updated.status);
      onLaunchNative(`[Agentic] Cancel requested for ${agenticRunId}`);
    } catch (error) {
      onLaunchNative(`[Agentic][Cancel] ${(error as Error).message}`);
    } finally {
      setAgenticCancelling(false);
    }
  }

  async function onRunAgentic(scriptId: string, testId: string) {
    if (!customProjectId || agenticRunBusy) return;
    setAgenticRunBusy(true);
    setLifecycleState("launching");
    setAgenticRun(null);
    setAgenticLogTail("");
    onReplay(null);
    onAgenticRunIdChange?.(null);
    lastFrameCountRef.current = 0;
    lastTelemetryCountRef.current = 0;
    lastReplayVersionRef.current = 0;
    let activeRunId: string | null = null;
    try {
      const run = await runSimulation(customProjectId, testId, onLaunchNative, { script_id: scriptId });
      activeRunId = run.run_id;
      setAgenticRunId(run.run_id);
      setAgenticRun(run);
      onAgenticRunIdChange?.(run.run_id);
      setLaunchId(null);
      onLaunchNative(`[Agentic] Run ${run.run_id} started for ${testId}`);
      agenticRunStatusRef.current = null;
      await pollAgenticRun(customProjectId, run.run_id, {
        onLog: onLaunchNative,
        onStatus: (status) => {
          setAgenticRun(status);
          if (agenticRunStatusRef.current !== status.status) {
            agenticRunStatusRef.current = status.status;
            appendMessage(executionStatusMessage(status));
          }
          void getAgenticRunLogs(customProjectId, run.run_id, 2000)
            .then((logs) => setAgenticLogTail(logs.combined || logs.stderr || logs.stdout))
            .catch(() => undefined);
        },
        onLifecycle: setLifecycleState,
        onReplay: (data) => {
          const manifest = data.manifest as Record<string, unknown> | undefined;
          const teleRaw = data.telemetry;
          let telemetry = normalizeTelemetryBundle(teleRaw);
          if (!telemetry && teleRaw && typeof teleRaw === "object") {
            const schema = (teleRaw as Record<string, unknown>).schema as Record<string, unknown> | undefined;
            if (schema?.type === "imu" || schema?.type === "contact_force") {
              telemetry = normalizeTelemetryBundle({
                type: schema.type,
                samples: (teleRaw as Record<string, unknown>).samples,
                sampleRate: schema.sampleRate,
              });
            }
          }
          const sensorType =
            (manifest as { telemetry?: { sensorTypes?: string[] } } | undefined)?.telemetry?.sensorTypes?.[0] ??
            (testId === "imu_sensor"
              ? "imu"
              : testId === "contact_force"
                ? "contact_force"
                : testId === "depth_camera"
                  ? "depth_camera"
                  : testId);
          const bundle = normalizeReplay(
            {
              state_timeseries: (data.state_timeseries ?? data.frames) as Parameters<
                typeof normalizeReplay
              >[0]["state_timeseries"],
              objects: data.objects as Parameters<typeof normalizeReplay>[0]["objects"],
              scene: data.scene as Parameters<typeof normalizeReplay>[0]["scene"],
              raw_frames: data.raw_frames as Parameters<typeof normalizeReplay>[0]["raw_frames"],
              preview_frames: data.preview_frames as Parameters<typeof normalizeReplay>[0]["preview_frames"],
              telemetry: telemetry ?? undefined,
              meta: {
                ...((data.meta as Record<string, unknown>) ?? {}),
                agentic_run_id: run.run_id,
                test_id: testId,
                sensor_type: sensorType,
                kind: "sensor",
                manifest,
              },
            },
            customProjectId!,
            run.run_id,
            "smooth",
          );
          lastFrameCountRef.current = bundle.frames.length;
          onReplay(bundle);
          onLaunchNative(`[Agentic] Replay loaded (${bundle.frames.length} frames).`);
        },
        onFailure: (f) => {
          onLaunchFailure?.({
            title: f.title,
            failureDetail: f.failureDetail,
            suggestedFix: f.suggestedFix ?? undefined,
            logs: f.logs,
            scriptPath: f.scriptPath,
          });
        },
      });
      try {
        const report = await generateEngineeringReport(customProjectId, run.run_id, onLaunchNative);
        setLatestReport(report);
        onReportChange?.(report);
        appendMessage(engineeringReportMessage(report));
        onLaunchNative(`[Agentic] Engineering report ${report.report_id} generated.`);
      } catch (reportErr) {
        onLaunchNative(`[Agentic][Report] ${(reportErr as Error).message}`);
      }
    } catch (error) {
      onLaunchNative(`[Agentic][Error] ${(error as Error).message}`);
      setLifecycleState("failed");
      onLaunchFailure?.({
        title: "Agentic run failed",
        failureDetail: (error as Error).message,
      });
      if (customProjectId && activeRunId) {
        try {
          const report = await generateEngineeringReport(customProjectId, activeRunId, onLaunchNative);
          setLatestReport(report);
          onReportChange?.(report);
          appendMessage(engineeringReportMessage(report));
        } catch {
          /* report optional on failure */
        }
      }
    } finally {
      setAgenticRunBusy(false);
    }
  }

  async function onLaunchWeb(skeleton = false) {
    if (!customProjectId || launchingWeb || isRunning) return;
    if (sensorLaunchBlocked) {
      const errors = (sensorValidation?.errors as string[] | undefined) ?? [];
      onLaunchFailure?.({
        title: "Sensor validation failed",
        failureDetail: errors.join("\n") || "Fix sensor requirements before launch.",
        suggestedFix: "Adjust attach links or upload a URDF with the required links.",
      });
      return;
    }
    setLaunchingWeb(true);
    setLifecycleState("launching");
    onReplay(null);
    lastFrameCountRef.current = 0;
    logOffsetRef.current = { stdout: 0, stderr: 0 };
    pollRef.current += 1;
    const pollToken = pollRef.current;
    try {
      const result = await launchProjectWebViewer(customProjectId, 400, { skeleton });
      setLaunchId(result.launch_id);
      setLifecycleState(String(result.lifecycle ?? result.status ?? "running"));
      onLaunchNative(
        skeleton
          ? `[Web] Launching skeleton preview · id=${result.launch_id}`
          : `[Web] Launching imported robot · id=${result.launch_id}`,
      );
      void pollStatus(result.launch_id, customProjectId, pollToken);
    } catch (error) {
      onLaunchNative(`[Web][Error] ${(error as Error).message}`);
      setLifecycleState("failed");
    } finally {
      setLaunchingWeb(false);
    }
  }

  async function onUploadMissingAssets(files: FileList | null) {
    if (!customProjectId || !files || files.length === 0) return;
    try {
      const result = await uploadProjectAssets(customProjectId, Array.from(files));
      setValidation((result.import_validation as Record<string, unknown>) ?? validation);
      await refreshReadiness(customProjectId);
      onLaunchNative(`[Import] Uploaded ${files.length} asset file(s). Missing meshes: ${String(result.missing_mesh_count ?? "?")}`);
    } catch (error) {
      onLaunchNative(`[Import][Error] ${(error as Error).message}`);
    }
  }

  async function onGenerateFromStep() {
    if (!customProjectId) return;
    setStepBusy(true);
    try {
      const result = await generateMeshesFromStep(customProjectId, { mappings: stepMappings });
      setValidation((result.import_validation as Record<string, unknown>) ?? validation);
      await refreshReadiness(customProjectId);
      const exported = (result.export as Record<string, unknown> | undefined)?.exported_count;
      onLaunchNative(
        `[Import] STEP export complete (${String(exported ?? 0)} mesh file(s)). Missing meshes: ${String(result.missing_mesh_count ?? "?")}`,
      );
    } catch (error) {
      onLaunchNative(`[Import][STEP] ${(error as Error).message}`);
    } finally {
      setStepBusy(false);
    }
  }

  function resetLaunch() {
    pollRef.current += 1;
    setLaunchId(null);
    setLifecycleState("idle");
    lastFrameCountRef.current = 0;
    lastReplayVersionRef.current = 0;
    onReplay(null);
    onLaunchNative("[Web] Reset — you can run again.");
  }

  const btn = "rounded border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs hover:bg-slate-200 disabled:opacity-40";
  const primary = "rounded bg-[#FF6A1A] px-3 py-1.5 text-xs text-white hover:bg-[#e55f15] disabled:opacity-40";
  const disabledWebReason = readiness?.disabled_reason_web;

  const launchControls = legacyOpen ? (
    <div className="space-y-3 overflow-auto p-3">
      <div className="text-xs font-semibold text-slate-800">Legacy web viewer</div>
      <p className="text-[10px] text-slate-500">
        Optional showcase launcher — prefer Run Simulation in the assistant for agentic scripts.
      </p>

      <label className="block text-xs text-slate-700">
        Sensor test type
        <select
          className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900"
          value={testType}
          onChange={(e) => setTestType(e.target.value)}
        >
          {TEST_TYPES.map((t) => (
            <option key={t.id} value={t.id}>
              {t.label}
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-2">
        {customProjectId ? (
          <>
            <button type="button" className={btn} onClick={() => void refreshValidation()}>
              Refresh validation
            </button>
            <button
              type="button"
              className={primary}
              disabled={!canLaunchWeb || launchingWeb || isRunning || sensorLaunchBlocked}
              title={disabledWebReason ?? undefined}
              onClick={() => void onLaunchWeb(false)}
            >
              {launchingWeb || isRunning ? "Running…" : "Run in web viewer"}
            </button>
            <button
              type="button"
              className={btn}
              disabled={!canPreviewSkeleton || launchingWeb || isRunning}
              title={canPreviewSkeleton ? "Skeleton preview — meshes missing" : disabledWebReason ?? undefined}
              onClick={() => void onLaunchWeb(true)}
            >
              Preview skeleton
            </button>
            {launchId ? (
              <button type="button" className={btn} onClick={resetLaunch}>
                Reset
              </button>
            ) : null}
          </>
        ) : null}
      </div>

      {!canLaunchWeb && disabledWebReason && customProjectId ? (
        <p className="text-xs text-amber-300">{disabledWebReason}</p>
      ) : null}

      {canGenerateFromStep && suggestedMappings.length > 0 ? (
        <div className="rounded border border-slate-200 bg-slate-50 p-2 text-xs text-slate-700">
          <div className="mb-1 font-semibold text-slate-900">STEP part mapping</div>
          <div className="max-h-32 space-y-1 overflow-auto">
            {suggestedMappings.map((row) => {
              const path = row.urdf_mesh_path ?? "";
              return (
                <label key={path} className="flex flex-wrap items-center gap-2 text-[10px]">
                  <span className="font-mono text-red-200">{path}</span>
                  <select
                    className="rounded border border-slate-300 bg-white px-1 py-0.5"
                    value={stepMappings[path] ?? ""}
                    onChange={(e) => setStepMappings((prev) => ({ ...prev, [path]: e.target.value }))}
                  >
                    <option value="">— part —</option>
                    {stepParts.map((part) => (
                      <option key={part.name} value={part.name ?? ""}>
                        {part.name}
                      </option>
                    ))}
                  </select>
                </label>
              );
            })}
          </div>
          <button type="button" className={`${btn} mt-2`} disabled={stepBusy} onClick={() => void onGenerateFromStep()}>
            {stepBusy ? "Generating…" : "Generate from STEP"}
          </button>
        </div>
      ) : null}

      {customProjectId && validation ? (
        <ImportValidationSummary validation={validation} />
      ) : null}
      {customProjectId ? (
        <p className="text-[10px] text-slate-500">
          Launchable (web): {canLaunchWeb ? "yes" : "no"}
          {firstMissingMesh ? ` · first missing: ${firstMissingMesh}` : ""}
          {agenticRunId ? ` · run=${agenticRunId}` : launchId ? ` · ${launchId}` : ""}
        </p>
      ) : null}
    </div>
  ) : !agenticPathActive ? (
    <div className="flex items-center justify-between px-3 py-2">
      <span className="text-[10px] text-slate-500">Legacy demo launcher (optional)</span>
      <button type="button" className={btn} onClick={() => setLegacyOpen(true)}>
        Expand
      </button>
    </div>
  ) : null;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <EngineeringReportModal
        open={reportModalOpen}
        report={latestReport}
        onClose={() => setReportModalOpen(false)}
        onCopyJson={() => {
          if (latestReport) void navigator.clipboard.writeText(JSON.stringify(latestReport, null, 2));
        }}
        onDownloadMd={async () => {
          if (!customProjectId || !latestReport) return;
          const md = await getAgenticReportMarkdown(customProjectId, latestReport.run_id);
          const blob = new Blob([md], { type: "text/markdown" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${latestReport.run_id}-report.md`;
          a.click();
          URL.revokeObjectURL(url);
        }}
      />
      {phase === "workbench" ? (
        <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-3 py-2">
          <div>
            <h1 className="text-sm font-semibold text-slate-900">My Projects</h1>
            <p className="text-[10px] text-slate-500">
              {customProjectId ? `Project: ${customProjectId}` : "Workbench"}
            </p>
          </div>
          <button type="button" className={btn} onClick={() => setPhase("entry")}>
            New project
          </button>
        </div>
      ) : null}
      <div className="min-h-0 flex-1">
        {phase === "entry" ? (
          <ProjectEntryScreen
            goal={entryGoal}
            onGoalChange={setEntryGoal}
            pendingFiles={pendingFiles}
            onAddFiles={(files) =>
              setPendingFiles((prev) => {
                const seen = new Set(prev.map((f) => `${f.name}:${f.size}`));
                return [...prev, ...files.filter((f) => !seen.has(`${f.name}:${f.size}`))];
              })
            }
            onRemoveFile={(index) => setPendingFiles((prev) => prev.filter((_, i) => i !== index))}
            onSubmit={() => void handleEntrySubmit()}
            submitting={entrySubmitting}
            projectName={projectName}
            onProjectNameChange={(name) => {
              setProjectName(name);
              setAssistantProjectName(name);
            }}
          />
        ) : !legacyOpen ? (
          <div className="h-full min-h-0">
            <BuildablesAssistant
              projectId={customProjectId}
              hideUpload
              onProjectIdChange={onProjectImported}
              onLog={onLaunchNative}
              onPreflightComplete={() => void refreshValidation()}
              onRunAgentic={onRunAgentic}
              runBusy={agenticRunBusy}
              agenticRun={agenticRun}
              agenticLogTail={agenticLogTail}
              onCancelAgenticRun={() => void onCancelAgenticRun()}
              agenticCancelling={agenticCancelling}
              onClearAgenticLogView={() => setAgenticLogTail("")}
              latestReport={latestReport}
              onViewReport={() => setReportModalOpen(true)}
              onCopyReportSummary={() => {
                if (latestReport) void navigator.clipboard.writeText(latestReport.plain_language_summary);
              }}
              onDownloadReportMd={async () => {
                if (!customProjectId || !latestReport) return;
                const md = await getAgenticReportMarkdown(customProjectId, latestReport.run_id);
                const blob = new Blob([md], { type: "text/markdown" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${latestReport.run_id}-report.md`;
                a.click();
                URL.revokeObjectURL(url);
              }}
            />
          </div>
        ) : (
          <GenesisVerticalSplit
            storageKey="projects-assistant"
            defaultTop={75}
            top={
              <BuildablesAssistant
                projectId={customProjectId}
                hideUpload
                onProjectIdChange={onProjectImported}
                onLog={onLaunchNative}
                onPreflightComplete={() => void refreshValidation()}
                onRunAgentic={onRunAgentic}
                runBusy={agenticRunBusy}
                agenticRun={agenticRun}
                agenticLogTail={agenticLogTail}
                onCancelAgenticRun={() => void onCancelAgenticRun()}
                agenticCancelling={agenticCancelling}
                onClearAgenticLogView={() => setAgenticLogTail("")}
                latestReport={latestReport}
                onViewReport={() => setReportModalOpen(true)}
                onCopyReportSummary={() => {
                  if (latestReport) void navigator.clipboard.writeText(latestReport.plain_language_summary);
                }}
                onDownloadReportMd={async () => {
                  if (!customProjectId || !latestReport) return;
                  const md = await getAgenticReportMarkdown(customProjectId, latestReport.run_id);
                  const blob = new Blob([md], { type: "text/markdown" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `${latestReport.run_id}-report.md`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
              />
            }
            bottom={launchControls}
          />
        )}
      </div>
    </div>
  );
}
