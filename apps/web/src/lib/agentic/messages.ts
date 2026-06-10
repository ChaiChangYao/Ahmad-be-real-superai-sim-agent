/**
 * Deterministic assistant message generator from typed preflight data.
 * LLM mode may wrap these strings later — planner remains source of truth.
 */
import type {
  AgentActionCard,
  AgentMessage,
  AgentTimelineStep,
  AgentTimelineStepId,
  AgentTimelineStepStatus,
  EngineeringReport,
  ExecutionRun,
  MeshReference,
  ProjectInspectionReport,
  SimulationPlan,
  SimulationTestSpec,
  TestReadinessResult,
  UploadDiagnostics,
} from "./types";
import { createInitialTimelineSteps, ENTRY_PIPELINE_STEPS } from "./timeline";

function id(): string {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function ts(): string {
  return new Date().toISOString();
}

export function userMessage(text: string, attachments?: string[]): AgentMessage {
  let body = text;
  if (attachments?.length) {
    const list = attachments.map((f) => `• ${f}`).join("\n");
    body = text.trim() ? `${text}\n\nAttachments:\n${list}` : `Attachments:\n${list}`;
  }
  return { id: id(), role: "user", type: "user", text: body, attachments, timestamp: ts() };
}

export function buildTimelineMessage(steps?: AgentTimelineStep[]): AgentMessage {
  return {
    id: id(),
    role: "assistant",
    type: "agent_timeline",
    text: "Working on your request…",
    timelineSteps: steps ?? createInitialTimelineSteps(ENTRY_PIPELINE_STEPS),
    timestamp: ts(),
  };
}

export function updateTimelineStep(
  message: AgentMessage,
  stepId: AgentTimelineStepId,
  status: AgentTimelineStepStatus,
  detail?: string,
  error?: string,
): AgentMessage {
  const steps = message.timelineSteps ?? createInitialTimelineSteps(ENTRY_PIPELINE_STEPS);
  return {
    ...message,
    timelineSteps: steps.map((s) =>
      s.step_id === stepId ? { ...s, status, detail: detail ?? s.detail, error: error ?? s.error } : s,
    ),
  };
}

export function formatUploadDiagnosticsDetail(diag?: UploadDiagnostics | null): string {
  if (!diag) return "";
  const parts: string[] = [];
  if (diag.extracted_file_count != null) parts.push(`${diag.extracted_file_count} file(s) extracted`);
  if (diag.urdf_count != null) parts.push(`${diag.urdf_count} URDF/MJCF`);
  if (diag.mesh_count != null) parts.push(`${diag.mesh_count} mesh file(s)`);
  if (diag.matched_mesh_count != null) parts.push(`${diag.matched_mesh_count} mesh refs matched`);
  if (diag.missing_mesh_count != null) parts.push(`${diag.missing_mesh_count} missing`);
  if (diag.selected_robot_description) parts.push(`Robot description: ${diag.selected_robot_description}`);
  if (diag.skipped_files?.length) parts.push(`Skipped: ${diag.skipped_files.slice(0, 5).join(", ")}`);
  if (diag.zip_errors?.length) parts.push(`Zip errors: ${diag.zip_errors.join("; ")}`);
  return parts.join(" · ");
}

export function textMessage(text: string): AgentMessage {
  return { id: id(), role: "assistant", type: "text", text, timestamp: ts() };
}

export function errorMessage(detail: {
  title: string;
  explanation: string;
  affected_files?: string[];
  suggested_actions?: string[];
  copyable_debug_details?: string;
}): AgentMessage {
  return {
    id: id(),
    role: "assistant",
    type: "error",
    text: detail.explanation,
    timestamp: ts(),
    error: {
      error_code: "assistant_error",
      title: detail.title,
      explanation: detail.explanation,
      affected_files: detail.affected_files ?? [],
      suggested_actions: detail.suggested_actions ?? [],
      copyable_debug_details: detail.copyable_debug_details ?? detail.explanation,
    },
  };
}

function countByRole(assets: ProjectInspectionReport["assets"]) {
  const urdf = assets.filter((a) => a.role === "robot_description").length;
  const step = assets.filter((a) => a.file_type === "step" || a.file_type === "stp").length;
  const mesh = assets.filter((a) => a.role === "mesh").length;
  return { urdf, step, mesh, total: assets.length };
}

export function buildUploadSummaryMessages(
  fileNames: string[],
  inspection: ProjectInspectionReport,
  plan: SimulationPlan,
): AgentMessage[] {
  const messages: AgentMessage[] = [];
  const counts = countByRole(inspection.assets);
  const robot = inspection.robot_descriptions.find((r) => r.parsed);

  let intro = `Uploaded ${fileNames.length} file(s):\n${fileNames.map((f) => `• ${f}`).join("\n")}\n\n`;
  intro += `I found:\n`;
  if (counts.urdf) intro += `• ${counts.urdf} robot description(s)\n`;
  if (counts.step) intro += `• ${counts.step} STEP file(s)\n`;
  if (counts.mesh) intro += `• ${counts.mesh} mesh file(s)\n`;
  if (robot) {
    intro += `• ${robot.mesh_references.length} mesh references in URDF\n`;
    intro += `• ${inspection.missing_mesh_count} missing mesh file(s)\n`;
    intro += `• ${robot.movable_joints_count} movable joint(s)\n`;
    if (robot.detected_sensors.length === 0) {
      intro += `• no explicit sensor metadata in URDF\n`;
    }
  }
  if (counts.step > 0 && inspection.missing_mesh_count > 0) {
    intro += `\nThe STEP file does not automatically satisfy URDF mesh references.`;
  }

  messages.push(textMessage(intro));
  messages.push(assetSummaryMessage(inspection));
  if (inspection.missing_mesh_count > 0) {
    messages.push(missingRequirementsMessage(inspection));
  }
  messages.push(simulationPlanMessage(plan));
  messages.push(testRecommendationsMessage(plan.recommended_tests, plan.blocked_tests));
  messages.push(recoveryActionsMessage(inspection, plan));
  return messages;
}

export function buildGoalResponseMessages(
  userGoal: string,
  inspection: ProjectInspectionReport,
  plan: SimulationPlan,
  specs: SimulationTestSpec[],
): AgentMessage[] {
  const messages: AgentMessage[] = [userMessage(userGoal)];

  if (plan.goal_parse?.clarifying_questions?.length) {
    for (const q of plan.goal_parse.clarifying_questions) {
      messages.push({
        id: id(),
        role: "assistant",
        type: "clarification_question",
        text: q,
        timestamp: ts(),
      });
    }
  }

  const intro = plan.agent_explanation || plan.plan_steps.join("\n");
  messages.push(textMessage(intro));
  messages.push(testRecommendationsMessage(plan.recommended_tests, plan.blocked_tests, specs));
  if (inspection.missing_mesh_count > 0) {
    messages.push(missingRequirementsMessage(inspection));
  }
  messages.push(recoveryActionsMessage(inspection, plan));
  return messages;
}

export function assetSummaryMessage(inspection: ProjectInspectionReport): AgentMessage {
  return {
    id: id(),
    role: "assistant",
    type: "asset_summary",
    timestamp: ts(),
    inspection,
    text: `${inspection.assets.length} assets scanned.`,
  };
}

export function missingRequirementsMessage(inspection: ProjectInspectionReport): AgentMessage {
  const missingMeshes: MeshReference[] = inspection.robot_descriptions.flatMap((r) =>
    r.mesh_references.filter((m) => m.status === "missing"),
  );
  const missingMetadata: Array<{ key: string; label: string; status: string; action: string }> = [];
  if (!inspection.robot_descriptions.some((r) => r.parsed)) {
    missingMetadata.push({
      key: "robot_description",
      label: "Robot description (URDF/MJCF)",
      status: "missing",
      action: "Upload URDF or MJCF in motion files",
    });
  }
  return {
    id: id(),
    role: "assistant",
    type: "missing_requirements",
    text: `${missingMeshes.length} missing mesh reference(s).`,
    timestamp: ts(),
    missingMeshes,
    missingMetadata,
    inspection,
  };
}

export function testRecommendationsMessage(
  recommended: TestReadinessResult[],
  blocked: TestReadinessResult[],
  specs?: SimulationTestSpec[],
): AgentMessage {
  return {
    id: id(),
    role: "assistant",
    type: "test_recommendations",
    timestamp: ts(),
    tests: [...recommended, ...blocked],
    specs,
    text: `${recommended.length} test(s) you can explore, ${blocked.length} blocked.`,
  };
}

export function simulationPlanMessage(plan: SimulationPlan): AgentMessage {
  return {
    id: id(),
    role: "assistant",
    type: "simulation_plan",
    plan,
    timestamp: ts(),
    text: plan.agent_explanation,
  };
}

export function recoveryActionsMessage(
  inspection: ProjectInspectionReport,
  plan: SimulationPlan,
): AgentMessage {
  const hasStep = inspection.assets.some((a) => a.file_type === "step" || a.file_type === "stp");
  const actions: AgentActionCard[] = [
    {
      id: "upload-zip",
      title: "Upload robot zip",
      description: "Attach a zip with meshes/ folder via + below, then Send",
      actionId: "upload_zip",
      variant: "primary",
    },
    {
      id: "run-preflight",
      title: "Run preflight",
      description: "Re-scan, inspect, and update plan",
      actionId: "run_preflight",
      variant: "secondary",
    },
  ];
  if (hasStep) {
    actions.push({
      id: "step-preview",
      title: "Generate STEP preview",
      description: "Export whole-assembly STL via FreeCAD (requires freecadcmd on PATH)",
      actionId: "recover_step_preview",
      variant: "secondary",
    });
  }
  if (hasStep && inspection.missing_mesh_count > 0) {
    actions.push({
      id: "step-recover",
      title: "Recover meshes from STEP",
      description: "Primary Pillar 1 path — export per-part meshes via FreeCAD when installed",
      actionId: "recover_missing_meshes",
      variant: "primary",
    });
  }
  if (inspection.missing_mesh_count > 0) {
    actions.push({
      id: "skeleton",
      title: "Skeleton fallback",
      description: "Joint sweep / gravity with fallback collision (no visual meshes)",
      actionId: "skeleton_fallback",
      variant: "secondary",
    });
  }
  actions.push({
    id: "cad-bridge",
    title: "Pillar 1 CAD bridge (coming soon)",
    description: "Not connected yet — use STEP recovery or upload a meshes/ zip bundle",
    actionId: "cad_bridge",
    variant: "disabled",
    disabled: true,
    disabledReason: "Buildables CAD generation bridge is not connected. Use STEP recovery or upload meshes.",
  });
  actions.push({
    id: "prepare-script",
    title: "Prepare script of last test",
    description: "Generate a Genesis script for the currently selected test",
    actionId: "prepare_genesis_script",
    variant: "primary",
  });
  actions.push({
    id: "run-sim",
    title: "Run simulation of last test",
    description: "Execute the last generated script for the selected test",
    actionId: "run_simulation",
    variant: "secondary",
  });

  const steps = plan.generation_tasks.length
    ? `\nSuggested: ${plan.generation_tasks.join(", ")}`
    : "";
  return {
    id: id(),
    role: "assistant",
    type: "recovery_actions",
    text: `Recovery and next steps:${steps}`,
    timestamp: ts(),
    actions,
    plan,
  };
}

export function engineeringReportMessage(report: EngineeringReport): AgentMessage {
  const actions: AgentActionCard[] = [
    {
      id: "view-report",
      title: "View full report",
      description: "Open detailed issues, limitations, and recommendations",
      actionId: "view_engineering_report",
      variant: "primary",
    },
    {
      id: "copy-summary",
      title: "Copy summary",
      description: "Copy plain-language summary to clipboard",
      actionId: "copy_report_summary",
      variant: "secondary",
    },
    {
      id: "download-md",
      title: "Download Markdown",
      description: "Save report.md for sharing",
      actionId: "download_report_md",
      variant: "secondary",
    },
  ];
  if (report.recommendations[0]?.action_id === "run_simulation") {
    actions.push({
      id: "rerun",
      title: "Run simulation of last test",
      description: report.recommendations[0].description,
      actionId: "run_simulation",
      variant: "secondary",
    });
  }
  for (const tid of report.next_tests.slice(0, 1)) {
    actions.push({
      id: `next-${tid}`,
      title: `Run ${tid}`,
      description: "Suggested follow-up test",
      actionId: `select_test:${tid}`,
      variant: "secondary",
    });
  }
  return {
    id: id(),
    role: "assistant",
    type: "engineering_report",
    text: report.plain_language_summary || report.executive_summary,
    timestamp: ts(),
    engineeringReport: report,
    actions,
  };
}

export function welcomeMessage(): AgentMessage {
  return textMessage(
    "I'm the Buildables Assistant. Upload URDF, STEP, meshes, or a robot zip — I'll scan your project and tell you which simulations are ready, blocked, or need safe defaults.\n\nTry: \"Can I run gravity, joint sweep, and IMU?\"",
  );
}

export function executionStatusMessage(run: ExecutionRun, note?: string): AgentMessage {
  const label = run.status.replace(/_/g, " ");
  return {
    id: id(),
    role: "assistant",
    type: "execution_status",
    text: note ?? `Run ${run.run_id}: ${label}`,
    timestamp: ts(),
    executionRun: run,
  };
}

export function buildResumeMessages(
  plan: SimulationPlan,
  inspection: ProjectInspectionReport | null,
  specs?: SimulationTestSpec[],
): AgentMessage[] {
  const messages: AgentMessage[] = [
    textMessage("Welcome back — here's your latest simulation plan from the last session."),
    simulationPlanMessage(plan),
    testRecommendationsMessage(plan.recommended_tests, plan.blocked_tests, specs),
  ];
  if (inspection && inspection.missing_mesh_count > 0) {
    messages.push(missingRequirementsMessage(inspection));
  }
  const inv =
    inspection ??
    ({
      project_id: plan.project_id ?? "",
      assets: [],
      robot_descriptions: [],
      mesh_inspections: [],
      missing_mesh_count: 0,
      warnings: [],
      errors: [],
    } satisfies ProjectInspectionReport);
  messages.push(recoveryActionsMessage(inv, plan));
  return messages;
}
