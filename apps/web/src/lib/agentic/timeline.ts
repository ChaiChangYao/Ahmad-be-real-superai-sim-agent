/** Agent pipeline step IDs — shared by entry flow and assistant timeline UI. */

export type AgentTimelineStepId =
  | "idle"
  | "user_submitted"
  | "uploading"
  | "extracting_zip"
  | "scanning_assets"
  | "inspecting_robot_description"
  | "checking_meshes"
  | "planning_tests"
  | "needs_clarification"
  | "ready_to_generate"
  | "generating_script"
  | "script_generated"
  | "running_simulation"
  | "replay_ready"
  | "telemetry_ready"
  | "generating_report"
  | "completed"
  | "failed";

export type AgentTimelineStepStatus = "pending" | "running" | "done" | "failed" | "skipped";

export type AgentTimelineStep = {
  step_id: AgentTimelineStepId;
  status: AgentTimelineStepStatus;
  label: string;
  detail?: string;
  error?: string;
};

export const ENTRY_PIPELINE_STEPS: Array<{ step_id: AgentTimelineStepId; label: string }> = [
  { step_id: "user_submitted", label: "Message received" },
  { step_id: "uploading", label: "Uploading files" },
  { step_id: "extracting_zip", label: "Extracting zip archive" },
  { step_id: "scanning_assets", label: "Scanning project assets" },
  { step_id: "inspecting_robot_description", label: "Inspecting URDF/MJCF" },
  { step_id: "checking_meshes", label: "Checking mesh references" },
  { step_id: "planning_tests", label: "Planning simulation tests" },
];

export const RUN_PIPELINE_STEPS: Array<{ step_id: AgentTimelineStepId; label: string }> = [
  { step_id: "ready_to_generate", label: "Ready to generate script" },
  { step_id: "generating_script", label: "Generating Genesis script" },
  { step_id: "script_generated", label: "Script generated" },
  { step_id: "running_simulation", label: "Running simulation" },
  { step_id: "replay_ready", label: "Loading replay" },
  { step_id: "telemetry_ready", label: "Loading telemetry" },
  { step_id: "generating_report", label: "Generating engineering report" },
  { step_id: "completed", label: "Completed" },
];

export function createInitialTimelineSteps(
  defs: Array<{ step_id: AgentTimelineStepId; label: string }> = ENTRY_PIPELINE_STEPS,
): AgentTimelineStep[] {
  return defs.map((d) => ({ ...d, status: "pending" as const }));
}

export function hasRunIntent(goal: string | null | undefined): boolean {
  if (!goal?.trim()) return false;
  return /\b(test|run|demo|check|try|see if|movement|sweep|works)\b/i.test(goal);
}

/** Human-readable labels for in-flight assistant operations (workbench composer area). */
export const ASSISTANT_LOADING_LABELS = {
  uploading: "Uploading files to project…",
  extracting_zip: "Extracting zip archive and mapping paths…",
  scanning_assets: "Scanning uploaded assets…",
  inspecting_robot: "Inspecting URDF/MJCF and mesh references…",
  planning_tests: "Planning simulation tests from your goal…",
  loading_requirements: "Evaluating test readiness and blockers…",
  generating_script: "Generating Genesis script for selected test…",
  running_recovery: "Running mesh recovery step…",
  applying_defaults: "Applying safe simulation defaults…",
  saving_state: "Saving assistant state…",
  starting_simulation: "Starting Genesis simulation run…",
} as const;
