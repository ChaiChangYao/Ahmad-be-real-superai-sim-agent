"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { activateProject } from "@/lib/api";
import {
  getAgenticState,
  getGeneratedScript,
  getLlmSettings,
  getRecoverStatus,
  getTestRequirements,
  saveAgenticState,
} from "@/lib/agentic/api";
import {
  askBuildablesCad,
  explainMissingRequirements,
  generateSafeDefaultsAction,
  prepareGenesisScript,
  recommendTests,
  recoverFromStep,
  runSimulation,
  toAgenticError,
  uploadAndPreflight,
} from "@/lib/agentic/actions";
import {
  buildGoalResponseMessages,
  buildResumeMessages,
  buildUploadSummaryMessages,
  errorMessage,
  textMessage,
  userMessage,
  welcomeMessage,
} from "@/lib/agentic/messages";
import { useAssistantStore } from "@/lib/agentic/store";
import type {
  AgenticErrorDetail,
  CodeGenResult,
  EngineeringReport,
  ExecutionRun,
  GeneratedScriptDetail,
} from "@/lib/agentic/types";
import { ENABLE_LLM_ASSISTANT } from "@/lib/agentic/config";
import { ASSISTANT_LOADING_LABELS } from "@/lib/agentic/timeline";
import { accent, accentBg, accentHover } from "../buildablesTheme";
import { AssistantErrorModal } from "./AssistantErrorModal";
import { AssistantMessageView } from "./AssistantMessageView";
import { GeneratedScriptViewer } from "./GeneratedScriptViewer";
import { RunExecutionCard, RunLogPanel } from "./RunExecutionCard";
import { defaultTestConfig, TestConfigPanel, type TestConfigValues } from "./TestConfigPanel";
import { GeneratedScriptsList } from "./GeneratedScriptsList";
import { AttachmentTray } from "./AttachmentTray";
import { UploadDropzone } from "./UploadDropzone";

const FILE_ACCEPT =
  ".urdf,.xml,.mjcf,.xacro,.step,.stp,.stl,.obj,.glb,.gltf,.dae,.mtl,.png,.jpg,.jpeg,.py,.yaml,.yml,.json,.zip";

type Props = {
  projectId: string | null;
  hideUpload?: boolean;
  onProjectIdChange: (id: string) => void;
  onLog?: (msg: string) => void;
  onPreflightComplete?: () => void;
  onRunAgentic?: (scriptId: string, testId: string) => Promise<void>;
  runBusy?: boolean;
  agenticRun?: ExecutionRun | null;
  agenticLogTail?: string;
  onCancelAgenticRun?: () => void;
  agenticCancelling?: boolean;
  onClearAgenticLogView?: () => void;
  latestReport?: EngineeringReport | null;
  onViewReport?: () => void;
  onCopyReportSummary?: () => void;
  onDownloadReportMd?: () => void;
};

export function BuildablesAssistant({
  projectId,
  hideUpload = false,
  onProjectIdChange,
  onLog,
  onPreflightComplete,
  onRunAgentic,
  runBusy = false,
  agenticRun = null,
  agenticLogTail = "",
  onCancelAgenticRun,
  agenticCancelling = false,
  onClearAgenticLogView,
  latestReport = null,
  onViewReport,
  onCopyReportSummary,
  onDownloadReportMd,
}: Props) {
  const {
    projectName,
    messages,
    inspection,
    plan,
    loading,
    selectedTestId,
    setMessages,
    appendMessage,
    setInspection,
    setPlan,
    setLoading,
    setSelectedTestId,
    setPersistedState,
  } = useAssistantStore();

  const [composer, setComposer] = useState("");
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [modalError, setModalError] = useState<AgenticErrorDetail | null>(null);
  const [specs, setSpecs] = useState<import("@/lib/agentic/types").SimulationTestSpec[]>([]);
  const [readiness, setReadiness] = useState<import("@/lib/agentic/types").TestReadinessResult[]>([]);
  const [testConfig, setTestConfig] = useState<TestConfigValues>(defaultTestConfig());
  const [codegenResult, setCodegenResult] = useState<CodeGenResult | null>(null);
  const [scriptDetail, setScriptDetail] = useState<GeneratedScriptDetail | null>(null);
  const [viewerOpen, setViewerOpen] = useState(false);
  const [llmBackendOn, setLlmBackendOn] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState<string | null>(null);
  const [toolsCollapsed, setToolsCollapsed] = useState(false);
  const [stepPreviewAvailable, setStepPreviewAvailable] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const welcomedRef = useRef(false);

  function beginLoading(detail: string) {
    setLoading(true);
    setLoadingDetail(detail);
  }

  function endLoading() {
    setLoading(false);
    setLoadingDetail(null);
  }

  useEffect(() => {
    void getLlmSettings()
      .then((s) => setLlmBackendOn(s.enable_llm_assistant || s.openrouter_api_key_set))
      .catch(() => setLlmBackendOn(false));
  }, []);

  const selectedReadiness = selectedTestId ? readiness.find((r) => r.test_id === selectedTestId) : undefined;
  const runBlocked = Boolean(
    selectedTestId &&
      selectedReadiness &&
      !selectedReadiness.can_run &&
      !selectedReadiness.can_run_with_fallback &&
      plan?.blocked_tests.some((t) => t.test_id === selectedTestId),
  );

  const log = useCallback((msg: string) => onLog?.(msg), [onLog]);

  const persistAgenticState = useCallback(
    async (
      pid: string,
      goal: string | null = null,
      overrides?: {
        plan?: typeof plan;
        inspection?: typeof inspection;
        selectedTestId?: string | null;
      },
    ) => {
      const nextPlan = overrides?.plan ?? plan;
      const nextInspection = overrides?.inspection ?? inspection;
      const nextTest = overrides?.selectedTestId !== undefined ? overrides.selectedTestId : selectedTestId;
      try {
        const saved = await saveAgenticState(pid, {
          user_goal: goal,
          latest_plan: nextPlan,
          latest_inspection: nextInspection,
          selected_test: nextTest,
          chat_summary: nextPlan?.agent_explanation ?? "",
          messages: useAssistantStore.getState().messages,
        });
        setPersistedState(saved);
      } catch (err) {
        log(`[Assistant][State] ${err instanceof Error ? err.message : String(err)}`);
      }
    },
    [plan, inspection, selectedTestId, setPersistedState, log],
  );

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading, loadingDetail]);

  useEffect(() => {
    if (selectedTestId) setToolsCollapsed(false);
  }, [selectedTestId]);

  useEffect(() => {
    if (!projectId) {
      setStepPreviewAvailable(false);
      return;
    }
    void getRecoverStatus(projectId)
      .then((s) => setStepPreviewAvailable(Boolean(s.available && (s.step_files?.length ?? 0) > 0)))
      .catch(() => setStepPreviewAvailable(false));
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      void getAgenticState(projectId).then(async (res) => {
        if (res.state) {
          setPersistedState(res.state);
          if (res.state.latest_plan) setPlan(res.state.latest_plan);
          if (res.state.latest_inspection) setInspection(res.state.latest_inspection);
          if (res.state.selected_test) setSelectedTestId(res.state.selected_test);
          if (res.state.messages?.length) {
            setMessages(res.state.messages);
          } else if (res.state.latest_plan) {
            const req = await getTestRequirements(projectId).catch(() => ({ specs: [], readiness: [] }));
            setSpecs(req.specs);
            setReadiness(req.readiness);
            setMessages((prev) => {
              if (prev.length > 1) return prev;
              return [welcomeMessage(), ...buildResumeMessages(res.state!.latest_plan!, res.state!.latest_inspection, req.specs)];
            });
          }
        }
      });
      void getTestRequirements(projectId).then((r) => {
        setSpecs(r.specs);
        setReadiness(r.readiness);
      });
    }
  }, [projectId, setPersistedState, setPlan, setInspection, setSelectedTestId, setMessages, setSpecs, setReadiness]);

  useEffect(() => {
    if (!welcomedRef.current && messages.length === 0 && !loading) {
      welcomedRef.current = true;
      setMessages([welcomeMessage()]);
    }
  }, [messages.length, setMessages]);

  async function handlePreflight(userGoal: string | null = null) {
    if (!projectId) {
      appendMessage(textMessage("Import or upload files first to create a project."));
      return;
    }
    beginLoading(ASSISTANT_LOADING_LABELS.planning_tests);
    try {
      const { inspectProject } = await import("@/lib/agentic/api");
      const { plan: p, specs: s } = await recommendTests(projectId, userGoal, log);
      setLoadingDetail(ASSISTANT_LOADING_LABELS.inspecting_robot);
      const insp = await inspectProject(projectId);
      setPlan(p);
      setInspection(insp);
      setSpecs(s);
      setLoadingDetail(ASSISTANT_LOADING_LABELS.loading_requirements);
      setReadiness(await getTestRequirements(projectId).then((r) => r.readiness));
      const msgs = userGoal
        ? buildGoalResponseMessages(userGoal, insp, p, s)
        : buildUploadSummaryMessages([], insp, p);
      setMessages((prev) => [...prev, ...msgs.slice(userGoal ? 0 : 1)]);
      await persistAgenticState(projectId, userGoal, { plan: p, inspection: insp });
      onPreflightComplete?.();
    } catch (err) {
      const detail = toAgenticError(err);
      appendMessage(errorMessage(detail));
      setModalError(detail);
      log(`[Assistant][Error] ${detail.explanation}`);
    } finally {
      endLoading();
    }
  }

  function addPendingFiles(files: File[]) {
    if (files.length === 0) return;
    setPendingFiles((prev) => {
      const seen = new Set(prev.map((f) => `${f.name}:${f.size}`));
      return [...prev, ...files.filter((f) => !seen.has(`${f.name}:${f.size}`))];
    });
  }

  function onComposerFilePick(list: FileList | null) {
    if (!list?.length) return;
    addPendingFiles(Array.from(list));
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleUpload(files: File[], userGoal: string | null = null) {
    if (files.length === 0) return;
    beginLoading(ASSISTANT_LOADING_LABELS.uploading);
    const names = files.map((f) => f.name);
    const goal = userGoal ?? (composer.trim() || null);
    try {
      const { projectId: pid, inspection: insp, plan: p } = await uploadAndPreflight(
        projectId,
        files,
        projectName,
        goal,
        log,
      );
      onProjectIdChange(pid);
      await activateProject(pid);
      setInspection(insp);
      setPlan(p);
      setLoadingDetail(ASSISTANT_LOADING_LABELS.loading_requirements);
      const req = await getTestRequirements(pid);
      setSpecs(req.specs);
      setReadiness(req.readiness);
      const msgs = buildUploadSummaryMessages(names, insp, p);
      setMessages((prev) => [...prev, ...msgs]);
      await persistAgenticState(pid, goal, { plan: p, inspection: insp });
      onPreflightComplete?.();
    } catch (err) {
      const detail = toAgenticError(err);
      appendMessage(errorMessage(detail));
      setModalError(detail);
      log(`[Assistant][Error] ${detail.explanation}`);
    } finally {
      endLoading();
    }
  }

  async function handleSend() {
    const text = composer.trim();
    const files = [...pendingFiles];
    if (!text && files.length === 0) return;

    if (files.length > 0) {
      const names = files.map((f) => f.name);
      appendMessage(userMessage(text || "Uploading additional files…", names));
      setComposer("");
      setPendingFiles([]);
      await handleUpload(files, text || null);
      return;
    }

    setComposer("");
    if (!projectId) {
      appendMessage(userMessage(text));
      appendMessage(
        textMessage("Upload your robot files first — I'll create a project and run preflight automatically."),
      );
      return;
    }
    beginLoading(ASSISTANT_LOADING_LABELS.planning_tests);
    try {
      const { inspectProject } = await import("@/lib/agentic/api");
      const { plan: p, specs: s } = await recommendTests(projectId, text, log);
      setLoadingDetail(ASSISTANT_LOADING_LABELS.inspecting_robot);
      const insp = await inspectProject(projectId);
      setPlan(p);
      setInspection(insp);
      setSpecs(s);
      setLoadingDetail(ASSISTANT_LOADING_LABELS.loading_requirements);
      const req = await getTestRequirements(projectId);
      setReadiness(req.readiness);
      setMessages((prev) => [...prev, ...buildGoalResponseMessages(text, insp, p, s)]);
      await persistAgenticState(projectId, text, { plan: p, inspection: insp });
      onPreflightComplete?.();
    } catch (err) {
      const detail = toAgenticError(err);
      appendMessage(errorMessage(detail));
      setModalError(detail);
    } finally {
      endLoading();
    }
  }

  function resolveActionLabel(actionId: string, actionTitle?: string): string {
    if (actionTitle) return actionTitle;
    const testLabel = selectedTestId
      ? specs.find((s) => s.test_id === selectedTestId)?.display_name ?? selectedTestId
      : null;
    if (actionId === "prepare_genesis_script") {
      return testLabel ? `Prepare script of last test (${testLabel})` : "Prepare script of last test";
    }
    if (actionId === "run_simulation") {
      return testLabel ? `Run simulation of last test (${testLabel})` : "Run simulation of last test";
    }
    return actionId;
  }

  async function handleAction(actionId: string, actionTitle?: string) {
    if (!projectId) return;
    if (actionId === "upload_zip") {
      appendMessage(userMessage("Upload robot zip"));
      fileInputRef.current?.click();
      return;
    }
    appendMessage(userMessage(resolveActionLabel(actionId, actionTitle)));
    beginLoading(ASSISTANT_LOADING_LABELS.planning_tests);
    try {
      switch (actionId) {
        case "run_preflight":
          await handlePreflight(composer.trim() || null);
          break;
        case "recover_step_preview": {
          setLoadingDetail(ASSISTANT_LOADING_LABELS.running_recovery);
          const r = await recoverFromStep(projectId, "preview", log);
          if (r.success) {
            const path = r.generated_files?.[0];
            appendMessage(
              textMessage(
                `${r.explanation}${path ? `\n\nPreview STL: ${path}\n(Open in a CAD viewer — STEP preview is not shown inline in chat.)` : ""}`,
              ),
            );
          } else {
            appendMessage(
              errorMessage({
                title: "STEP preview failed",
                explanation: r.explanation,
                suggested_actions: [
                  "Install FreeCAD and ensure freecadcmd is on PATH.",
                  "Upload STL/OBJ meshes or use Recover meshes from STEP instead.",
                ],
                copyable_debug_details: r.explanation,
              }),
            );
          }
          break;
        }
        case "recover_missing_meshes": {
          setLoadingDetail(ASSISTANT_LOADING_LABELS.running_recovery);
          const r = await recoverFromStep(projectId, "missing_meshes", log);
          if (r.success) {
            appendMessage(textMessage(r.explanation));
            await handlePreflight(null);
          } else {
            appendMessage(
              errorMessage({
                title: "STEP mesh recovery failed",
                explanation: r.explanation,
                suggested_actions: ["Install FreeCAD (freecadcmd on PATH) or upload a meshes/ zip."],
                copyable_debug_details: r.explanation,
              }),
            );
          }
          break;
        }
        case "cad_bridge": {
          const r = await askBuildablesCad(projectId, log);
          appendMessage(textMessage(r.explanation));
          break;
        }
        case "skeleton_fallback":
          setLoadingDetail(ASSISTANT_LOADING_LABELS.applying_defaults);
          await generateSafeDefaultsAction(projectId, "joint_sweep", { use_skeleton: true }, log);
          appendMessage(textMessage("Skeleton fallback defaults saved for joint sweep and gravity."));
          await handlePreflight("skeleton joint sweep gravity");
          break;
        case "prepare_genesis_script":
          if (selectedTestId) {
            await handleGenerateScript();
          } else {
            appendMessage(textMessage("Select a test first — use the test cards above, then prepare the script."));
          }
          break;
        case "run_simulation":
          await handleRunSimulation();
          break;
        case "view_engineering_report":
          onViewReport?.();
          break;
        case "copy_report_summary":
          onCopyReportSummary?.();
          break;
        case "download_report_md":
          await onDownloadReportMd?.();
          break;
        default:
          if (actionId.startsWith("select_test:")) {
            const tid = actionId.slice("select_test:".length);
            if (tid) {
              setSelectedTestId(tid);
              appendMessage(textMessage(`Selected test: ${tid}. Configure parameters and generate a script.`));
              await persistAgenticState(projectId, null, { selectedTestId: tid });
            }
          }
          break;
      }
    } catch (err) {
      const detail = toAgenticError(err);
      appendMessage(errorMessage(detail));
      setModalError(detail);
    } finally {
      endLoading();
    }
  }

  async function handleUseDefaults(testId: string) {
    if (!projectId) return;
    beginLoading(ASSISTANT_LOADING_LABELS.applying_defaults);
    try {
      await generateSafeDefaultsAction(projectId, testId, {}, log);
      appendMessage(textMessage(`Safe defaults applied for ${testId}.`));
      await handlePreflight(`run ${testId}`);
    } catch (err) {
      const detail = toAgenticError(err);
      setModalError(detail);
      appendMessage(errorMessage(detail));
    } finally {
      endLoading();
    }
  }

  async function handleRunSimulation() {
    if (!projectId || !selectedTestId || !codegenResult?.success || !codegenResult.script_id) {
      appendMessage(textMessage("Generate a valid Genesis script before running."));
      return;
    }
    const testReadiness = selectedReadiness;
    if (runBlocked && testReadiness) {
      const reason = testReadiness.blockers[0] ?? "This test is blocked until missing files are resolved.";
      appendMessage(textMessage(`Cannot run ${selectedTestId}: ${reason}`));
      setModalError({
        error_code: "test_blocked",
        title: `${selectedTestId} blocked`,
        explanation: reason,
        affected_files: [],
        suggested_actions: testReadiness.suggested_actions ?? [],
        copyable_debug_details: reason,
      });
      return;
    }
    if (!onRunAgentic) {
      appendMessage(textMessage("Run simulation is not connected to the viewport."));
      return;
    }
    beginLoading(ASSISTANT_LOADING_LABELS.starting_simulation);
    try {
      await onRunAgentic(codegenResult.script_id, selectedTestId);
      appendMessage(textMessage(`Simulation run started for ${selectedTestId}.`));
    } catch (err) {
      const detail = toAgenticError(err);
      appendMessage(errorMessage(detail));
      setModalError(detail);
    } finally {
      endLoading();
    }
  }

  async function handleGenerateScript() {
    if (!projectId || !selectedTestId) return;
    beginLoading(ASSISTANT_LOADING_LABELS.generating_script);
    try {
      const userParams: Record<string, unknown> = {
        duration_seconds: testConfig.duration_seconds,
      };
      if (testConfig.attach_link) userParams.attach_link = testConfig.attach_link;
      if (testConfig.sample_rate) userParams.sample_rate_hz = testConfig.sample_rate;
      if (testConfig.contact_links.trim()) {
        userParams.contact_links = testConfig.contact_links
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }
      if (selectedTestId === "depth_camera") {
        userParams.resolution = [testConfig.depth_width, testConfig.depth_height];
        userParams.fov = testConfig.depth_fov;
      }
      if (selectedTestId === "thermal_grid_readiness") {
        userParams.grid_resolution = testConfig.thermal_grid_resolution;
      }
      const result = await prepareGenesisScript(projectId, selectedTestId, log, {
        fallback_mode: testConfig.fallback_mode || null,
        user_parameters: userParams,
      });
      setCodegenResult(result);
      if (result.success && result.script_id) {
        const detail = await getGeneratedScript(projectId, result.script_id);
        setScriptDetail(detail);
        setViewerOpen(true);
        appendMessage(
          textMessage(
            `Generated ${result.template_id} script.\nPath: ${result.script_path}\nOutputs: ${result.expected_outputs.join(", ")}`,
          ),
        );
      } else {
        appendMessage(textMessage(`Script generation blocked: ${result.explanation}`));
        setViewerOpen(true);
      }
    } catch (err) {
      const detail = toAgenticError(err);
      setModalError(detail);
      appendMessage(errorMessage(detail));
    } finally {
      endLoading();
    }
  }

  async function handleConfigure(testId: string) {
    setSelectedTestId(testId);
    setTestConfig(defaultTestConfig());
    if (!projectId) return;
    try {
      const ex = await explainMissingRequirements(projectId, testId, log);
      appendMessage({
        id: `cfg-${Date.now()}`,
        role: "assistant",
        type: "missing_requirements",
        text: ex.explanation,
        timestamp: new Date().toISOString(),
        missingMeshes: ex.missingMeshes,
        missingMetadata: ex.missingMetadata,
      });
    } catch (err) {
      setModalError(toAgenticError(err));
    }
  }

  function copyReport() {
    const lines = [
      "=== Buildables Preflight Report ===",
      plan?.agent_explanation ?? "",
      ...(plan?.plan_steps ?? []),
      "",
      "Recommended:",
      ...(plan?.recommended_tests.map((t) => `  ${t.test_id}`) ?? []),
      "Blocked:",
      ...(plan?.blocked_tests.map((t) => `  ${t.test_id}: ${t.blockers[0] ?? ""}`) ?? []),
    ];
    void navigator.clipboard.writeText(lines.join("\n"));
    log("[Assistant] Report copied to clipboard.");
  }

  return (
    <div data-testid="buildables-assistant" className="flex h-full min-h-0 flex-col rounded-lg border border-slate-200 bg-slate-50">
      <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-3 py-2">
        <div>
          <div className={`text-xs font-semibold ${accent}`}>Buildables Assistant</div>
          <div className="text-[9px] text-slate-500">
            {projectId ? `Project: ${projectId}` : "No project — upload to start"}
            {ENABLE_LLM_ASSISTANT || llmBackendOn
              ? " · LLM assistant enabled (optional)"
              : " · Deterministic mode — OpenRouter optional"}
          </div>
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            disabled={loading || !projectId}
            className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100 disabled:opacity-40"
            onClick={() => void handlePreflight(null)}
          >
            Run preflight
          </button>
          <button
            type="button"
            className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100"
            onClick={copyReport}
          >
            Copy report
          </button>
        </div>
      </div>

      {!hideUpload ? (
        <div className="shrink-0 border-b border-slate-200 p-2">
          <UploadDropzone onFiles={(f) => void handleUpload(f)} disabled={loading} />
        </div>
      ) : null}

      <div ref={scrollRef} className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
        {messages.map((m) => (
          <AssistantMessageView
            key={m.id}
            message={m}
            selectedTestId={selectedTestId}
            onAction={(id, title) => void handleAction(id, title)}
            onSelectTest={setSelectedTestId}
            onConfigure={(id) => void handleConfigure(id)}
            onUseDefaults={(id) => void handleUseDefaults(id)}
            actionBusy={loading}
            hideStepPreview={!stepPreviewAvailable}
          />
        ))}
        {loading ? (
          <div
            data-testid="assistant-loading-status"
            className="rounded border border-slate-200/80 bg-slate-100 px-2.5 py-2 text-[10px] text-slate-600"
          >
            <div className="font-medium text-slate-700">{loadingDetail ?? "Working on your project…"}</div>
            <div className="mt-0.5 text-[9px] text-slate-500">
              Large imports and planning can take up to 2 minutes — stay on this screen.
            </div>
          </div>
        ) : null}
      </div>

      {projectId ? (
        <div className="shrink-0 border-t border-slate-200" data-testid="assistant-tools-drawer">
          <button
            type="button"
            data-testid="assistant-tools-toggle"
            className="flex w-full items-center justify-between gap-2 px-3 py-2 text-left text-[10px] text-slate-700 hover:bg-slate-100"
            onClick={() => setToolsCollapsed((prev) => !prev)}
          >
            <span>
              {toolsCollapsed ? "Show test tools" : "Hide test tools"}
              {selectedTestId
                ? ` · ${specs.find((s) => s.test_id === selectedTestId)?.display_name ?? selectedTestId}`
                : ""}
            </span>
            <span className="text-slate-500">{toolsCollapsed ? "▲" : "▼"}</span>
          </button>
          {!toolsCollapsed ? (
            <div className="max-h-[min(42vh,380px)] overflow-y-auto border-t border-slate-200/80 p-2">
              <GeneratedScriptsList
                projectId={projectId}
                onLog={log}
                onView={async (scriptId) => {
                  try {
                    const detail = await getGeneratedScript(projectId, scriptId);
                    setScriptDetail(detail);
                    const ctx = detail.context as Record<string, unknown> | undefined;
                    setCodegenResult({
                      success: true,
                      script_id: scriptId,
                      template_id: String(ctx?.template_id ?? "generated"),
                      script_path: detail.script_path,
                      context_path: detail.context_path,
                      expected_outputs: Array.isArray(ctx?.expected_outputs)
                        ? (ctx.expected_outputs as string[])
                        : [],
                      explanation: "",
                      next_step: "run_simulation",
                      validation: detail.validation ?? {
                        valid: true,
                        errors: [],
                        warnings: [],
                        blocked_reason: "",
                        unsafe_patterns_found: [],
                        required_files_present: true,
                        expected_outputs: [],
                      },
                    });
                    setViewerOpen(true);
                  } catch (err) {
                    setModalError(toAgenticError(err));
                  }
                }}
              />
              {selectedTestId ? (
                <>
                  <TestConfigPanel
                    testId={selectedTestId}
                    spec={specs.find((s) => s.test_id === selectedTestId)}
                    readiness={readiness.find((r) => r.test_id === selectedTestId)}
                    inspection={inspection}
                    values={testConfig}
                    onChange={setTestConfig}
                    onGenerate={() => void handleGenerateScript()}
                    generating={loading}
                  />
                  {codegenResult?.success ? (
                    <div className="mt-1 flex flex-col gap-1">
                      <button
                        type="button"
                        data-testid="run-simulation-button"
                        className={`w-full rounded px-2 py-1.5 text-[10px] font-medium text-white ${accentBg} ${accentHover} disabled:opacity-40`}
                        disabled={loading || runBusy || !onRunAgentic || runBlocked}
                        title={runBlocked ? selectedReadiness?.blockers[0] ?? "Test blocked" : undefined}
                        onClick={() => void handleRunSimulation()}
                      >
                        {runBusy ? "Running…" : "Run Simulation"}
                      </button>
                      <button
                        type="button"
                        data-testid="view-generated-code-button"
                        className="w-full rounded border border-slate-300 px-2 py-1 text-[9px] text-slate-700 hover:bg-slate-100"
                        onClick={() => setViewerOpen(true)}
                      >
                        View generated code
                      </button>
                    </div>
                  ) : null}
                  {agenticRun ? (
                    <div className="mt-2 space-y-2">
                      <RunExecutionCard
                        run={agenticRun}
                        logTail={agenticLogTail}
                        onCancel={onCancelAgenticRun}
                        cancelling={agenticCancelling}
                      />
                      {agenticLogTail ? (
                        <RunLogPanel
                          logs={agenticLogTail}
                          onCopy={() => void navigator.clipboard.writeText(agenticLogTail)}
                          onDownload={() => {
                            const blob = new Blob([agenticLogTail], { type: "text/plain" });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement("a");
                            a.href = url;
                            a.download = `${agenticRun.run_id}-combined.log`;
                            a.click();
                            URL.revokeObjectURL(url);
                          }}
                          onClearView={onClearAgenticLogView}
                        />
                      ) : null}
                    </div>
                  ) : null}
                </>
              ) : null}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="shrink-0 border-t border-slate-200 p-2">
        <AttachmentTray
          files={pendingFiles}
          onRemove={(index) => setPendingFiles((prev) => prev.filter((_, i) => i !== index))}
        />
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            data-testid="assistant-file-input"
            type="file"
            multiple
            accept={FILE_ACCEPT}
            className="hidden"
            onChange={(e) => onComposerFilePick(e.target.files)}
          />
          <button
            type="button"
            data-testid="assistant-attach-button"
            disabled={loading}
            className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded border border-slate-300 text-lg text-slate-700 hover:border-[#FF6A1A] hover:text-[#FF6A1A] disabled:opacity-40"
            aria-label="Attach files"
            onClick={() => fileInputRef.current?.click()}
          >
            +
          </button>
          <input
            type="text"
            value={composer}
            onChange={(e) => setComposer(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && void handleSend()}
            placeholder='e.g. "Can I run gravity, joint sweep, and IMU?"'
            className="min-w-0 flex-1 rounded border border-slate-300 bg-white px-2 py-1.5 text-xs text-slate-900 placeholder:text-slate-600"
            disabled={loading}
          />
          <button
            type="button"
            disabled={loading || (!composer.trim() && pendingFiles.length === 0)}
            className={`shrink-0 rounded px-3 py-1.5 text-xs font-medium text-white ${accentBg} ${accentHover} disabled:opacity-40`}
            onClick={() => void handleSend()}
          >
            Send
          </button>
        </div>
        {hideUpload ? (
          <p className="mt-1.5 text-[9px] text-slate-500">
            Use + to attach URDF, meshes, or zip — then Send to re-upload and refresh preflight.
          </p>
        ) : null}
      </div>

      <AssistantErrorModal open={Boolean(modalError)} error={modalError} onClose={() => setModalError(null)} />
      <GeneratedScriptViewer
        open={viewerOpen}
        result={codegenResult}
        detail={scriptDetail}
        onClose={() => setViewerOpen(false)}
        onRun={() => void handleRunSimulation()}
        runDisabled={loading || runBusy || !onRunAgentic}
      />
    </div>
  );
}
