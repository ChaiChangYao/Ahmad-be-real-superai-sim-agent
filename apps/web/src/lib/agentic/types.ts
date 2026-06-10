/** Typed models matching backend agentic schemas */

export type AssetRole =
  | "robot_description"
  | "mesh"
  | "cad"
  | "texture"
  | "control_script"
  | "metadata"
  | "unknown";

export type UploadedAsset = {
  id: string;
  project_id: string;
  original_filename: string;
  stored_path: string;
  relative_path: string;
  file_type: string;
  size_bytes: number;
  sha256: string;
  role: AssetRole | string;
  source: string;
  status: string;
};

export type MeshReference = {
  source_file: string;
  usage: string;
  raw_path: string;
  resolved_path: string;
  package_name: string;
  file_type: string;
  exists: boolean;
  status: string;
  matched_uploaded_asset_id: string | null;
  action_needed: string;
};

export type RobotDescriptionInspection = {
  parsed: boolean;
  format: string;
  source_path: string;
  links_count: number;
  joints_count: number;
  movable_joints_count: number;
  fixed_joints_count: number;
  root_link: string;
  link_names: string[];
  joint_names: string[];
  mesh_references: MeshReference[];
  has_inertial_data: boolean;
  has_joint_limits: boolean;
  has_collision_geometry: boolean;
  has_visual_geometry: boolean;
  detected_sensors: Record<string, unknown>[];
  warnings: string[];
  errors: string[];
};

export type MeshInspection = {
  asset_id: string;
  path: string;
  parsed: boolean;
  file_type: string;
  watertight: boolean | null;
  volume: number | null;
  bounds: number[] | null;
  face_count: number | null;
  vertex_count: number | null;
  units_guess: string;
  errors: string[];
  warnings: string[];
};

export type SimulationTestSpec = {
  test_id: string;
  display_name: string;
  category: string;
  description: string;
  required_inputs: string[];
  optional_inputs: string[];
  generatable_inputs: string[];
  cannot_fake_inputs: string[];
  outputs: string[];
  viewer_layout: string;
  genesis_template: string;
  supported_asset_types: string[];
  status: string;
};

export type TestReadinessResult = {
  test_id: string;
  can_run: boolean;
  can_run_with_fallback: boolean;
  confidence: number;
  missing_required: string[];
  missing_optional: string[];
  generated_defaults_available: string[];
  blockers: string[];
  warnings: string[];
  suggested_actions: string[];
  required_user_questions: string[];
  fallback_modes: string[];
};

export type SimulationPlan = {
  project_id: string;
  user_goal: string | null;
  asset_summary: Record<string, unknown>;
  recommended_tests: TestReadinessResult[];
  blocked_tests: TestReadinessResult[];
  required_questions: string[];
  generation_tasks: string[];
  selected_test: string | null;
  plan_steps: string[];
  warnings: string[];
  agent_explanation: string;
  goal_parse?: GoalParseResult;
};

export type GoalParseResult = {
  raw_goal: string;
  candidate_tests: string[];
  unknown_terms: string[];
  needs_clarification: boolean;
  clarifying_questions: string[];
};

export type GeneratedSimulationScript = {
  script_id: string;
  project_id: string;
  test_id: string;
  script_path: string;
  template_used: string;
  inputs_used: Record<string, unknown>;
  generated_files: string[];
  safety_checks: string[];
  expected_outputs: string[];
};

export type ExecutionRun = {
  run_id: string;
  project_id: string;
  script_id: string;
  test_id: string;
  template_id: string;
  backend: string;
  status: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  run_dir: string;
  command: string[];
  pid: number | null;
  exit_code: number | null;
  timeout_seconds: number;
  stdout_path: string;
  stderr_path: string;
  combined_log_path: string;
  manifest_path: string;
  replay_path: string;
  telemetry_path: string;
  report_path: string;
  error_summary: string;
  warning_summary: string;
  failure: Record<string, unknown> | null;
};

export type ExecutionFailure = {
  error_code: string;
  title: string;
  explanation: string;
  traceback_path?: string;
  affected_files: string[];
  suggested_actions: string[];
  raw_excerpt?: string;
  copyable_debug_details?: string;
};

export type RunManifest = {
  runId: string;
  projectId: string;
  testId: string;
  status: string;
  visual?: { hasReplay?: boolean; frameCount?: number; fps?: number };
  telemetry?: { hasTelemetry?: boolean; sampleCount?: number; sensorTypes?: string[] };
  errors?: string[];
  warnings?: string[];
};

export type ExecutionResult = {
  run_id: string;
  status: string;
  command: string;
  stdout_path: string;
  stderr_path: string;
  replay_path: string;
  telemetry_path: string;
  report_path: string;
  exit_code: number | null;
  error_summary: string;
};

export type TestOutcome = {
  status: string;
  label: string;
  summary: string;
  run_status: string;
  exit_code: number | null;
};

export type DetectedIssue = {
  issue_id: string;
  severity: string;
  code: string;
  title: string;
  explanation: string;
  suggested_fix: string;
  source: string;
};

export type EngineeringRecommendation = {
  recommendation_id: string;
  title: string;
  description: string;
  priority: string;
  next_step_type: string;
  action_id: string;
  test_id?: string | null;
};

export type SimulationLimitation = {
  limitation_id: string;
  category: string;
  text: string;
  test_id: string;
};

export type MetricValue = {
  id: string;
  label: string;
  value: string | number | boolean;
  unit?: string;
  category?: string;
};

export type EngineeringReport = {
  report_id: string;
  run_id: string;
  project_id: string;
  test_id: string;
  test_name: string;
  generated_at: string;
  executive_summary: string;
  plain_language_summary: string;
  outcome: TestOutcome;
  key_metrics: MetricValue[];
  detected_issues: DetectedIssue[];
  limitations: SimulationLimitation[];
  recommendations: EngineeringRecommendation[];
  next_tests: string[];
  disclaimer: string;
  confidence: number;
  pass_fail: string;
  summary: string;
  observed_issues: string[];
  engineering_explanation: string;
  suggested_design_changes: string[];
  missing_data_limitations: string[];
};

export type ReporterResult = {
  success: boolean;
  report: EngineeringReport | null;
  report_path: string;
  markdown_path: string;
  error: string;
};

export type RunSummary = {
  project_id: string;
  run_id: string;
  run_status: string;
  test_id: string;
  outcome: TestOutcome | null;
  executive_summary: string;
  pass_fail: string;
  report_id: string | null;
};

export type ProjectInspectionReport = {
  project_id: string;
  assets: UploadedAsset[];
  robot_descriptions: RobotDescriptionInspection[];
  mesh_inspections: MeshInspection[];
  missing_mesh_count: number;
  warnings: string[];
  errors: string[];
};

export type RecoveryResult = {
  success: boolean;
  generated_files: string[];
  failed_files: string[];
  requires_user_mapping: boolean;
  explanation: string;
  dependency_status: string;
};

export type CadBridgeResult = {
  status: string;
  request_type: string;
  explanation: string;
  queued_items: string[];
};

export type GeneratedScriptValidation = {
  valid: boolean;
  errors: string[];
  warnings: string[];
  blocked_reason: string;
  unsafe_patterns_found: string[];
  required_files_present: boolean;
  expected_outputs: string[];
};

export type CodeGenResult = {
  success: boolean;
  script_id: string;
  script_path: string;
  context_path: string;
  template_id: string;
  context?: Record<string, unknown> | null;
  validation: GeneratedScriptValidation;
  expected_outputs: string[];
  next_step: string;
  explanation: string;
};

export type GeneratedScriptDetail = {
  script_id: string;
  script_path: string;
  context_path: string;
  source: string;
  context: Record<string, unknown>;
  validation: GeneratedScriptValidation | null;
};

export type AgenticProjectState = {
  project_id: string;
  updated_at: string;
  user_goal: string | null;
  selected_test: string | null;
  selected_fallback_mode: string | null;
  generated_defaults: Record<string, Record<string, unknown>>;
  latest_plan: SimulationPlan | null;
  latest_inspection: ProjectInspectionReport | null;
  candidate_tests: string[];
  chat_summary: string;
  messages?: AgentMessage[];
  last_codegen?: CodeGenResult | null;
  last_run_id?: string | null;
  latest_report_id?: string | null;
  latest_report_summary?: string | null;
};

export type AgenticErrorDetail = {
  error_code: string;
  title: string;
  explanation: string;
  affected_files: string[];
  suggested_actions: string[];
  copyable_debug_details: string;
};

export type AgentToolCall = {
  id: string;
  action: string;
  status: "pending" | "running" | "completed" | "failed";
  startedAt: string;
  completedAt?: string;
  error?: string;
};

export type AgentActionCard = {
  id: string;
  title: string;
  description: string;
  actionId: string;
  variant: "primary" | "secondary" | "disabled";
  disabled?: boolean;
  disabledReason?: string;
};

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

export type UploadDiagnostics = {
  zip_paths?: string[];
  extracted_file_count?: number;
  urdf_count?: number;
  mesh_count?: number;
  skipped_files?: string[];
  selected_robot_description?: string | null;
  zip_errors?: string[];
  matched_mesh_count?: number;
  missing_mesh_count?: number;
  unresolved_references?: string[];
};

export type AgentMessageType =
  | "text"
  | "asset_summary"
  | "missing_requirements"
  | "test_recommendations"
  | "recovery_actions"
  | "clarification_question"
  | "simulation_plan"
  | "execution_status"
  | "engineering_report"
  | "error"
  | "user"
  | "agent_timeline";

export type AgentMessage = {
  id: string;
  role: "user" | "assistant" | "system";
  type: AgentMessageType;
  text?: string;
  timestamp: string;
  attachments?: string[];
  timelineSteps?: AgentTimelineStep[];
  inspection?: ProjectInspectionReport;
  plan?: SimulationPlan;
  tests?: TestReadinessResult[];
  specs?: SimulationTestSpec[];
  missingMeshes?: MeshReference[];
  missingMetadata?: Array<{ key: string; label: string; status: string; action: string }>;
  actions?: AgentActionCard[];
  error?: AgenticErrorDetail;
  toolCall?: AgentToolCall;
  engineeringReport?: EngineeringReport;
  executionRun?: ExecutionRun;
};

export type TestCardStatus = "ready" | "ready_with_fallback" | "needs_user_choice" | "blocked";

export function testCardStatus(result: TestReadinessResult): TestCardStatus {
  if (result.can_run) return "ready";
  if (result.required_user_questions.length > 0 && result.can_run_with_fallback) return "needs_user_choice";
  if (result.can_run_with_fallback) return "ready_with_fallback";
  return "blocked";
}
