import type { BuildablesPhysicsManifest } from "@schemas/types";

export type GenesisStatus = {
  installed: boolean;
  version: string | null;
  backend: string | null;
  device: string | null;
  error: string | null;
  setup_instructions: string;
};

export type RunResult = {
  run_id: string;
  project_id: string;
  scenario_id: string;
  status: "pass" | "fail" | "warning" | "error";
  genesis_used: boolean;
  mocked: boolean;
  manifest_version_used: number;
  step_count: number;
  started_at: string;
  ended_at: string;
  duration_s: number;
  metrics: Record<string, unknown>;
  metric_sources?: Record<string, string>;
  events: Array<Record<string, unknown>>;
  logs: string[];
  state_timeseries: Array<Record<string, unknown>>;
  artifacts: Record<string, string | null>;
};

export type ManifestState = BuildablesPhysicsManifest & {
  version: number;
  updated_at?: string | null;
};

export type GenesisCatalog = {
  source: string;
  physics_capabilities: Record<string, string[]>;
  asset_format_capabilities: Record<string, string[]>;
  sensor_capabilities: Record<string, string[]>;
  rendering_capabilities: Record<string, string[]>;
  environment_capabilities: Record<string, string[]>;
  control_capabilities: Record<string, string[]>;
};

export type ShowcaseCatalogEntry = {
  scenario_id: string;
  demo_name: string;
  layer: string;
  repo: string;
  script_relpath: string;
  script_path: string | null;
  repo_root: string | null;
  optional_extra: string | null;
  optional_extra_available: boolean;
  available: boolean;
  missing: string[];
  upstream_url: string;
  launch_mode: string;
  demo_type?: string;
  telemetry_channels?: string[] | null;
  kind?: string;
  sensor_type?: string | null;
};

export type ShowcaseCatalog = {
  total: number;
  available: number;
  entries: ShowcaseCatalogEntry[];
  setup: Record<string, string>;
};

export type ShowcaseLaunchResult = {
  launch_id: string;
  project_id: string;
  scenario_id: string;
  demo_name: string;
  layer: string;
  repo: string;
  script_path: string;
  repo_root?: string;
  pid?: number;
  started_at: string;
  status: string;
  lifecycle?: string;
  view_mode?: string;
  argv?: string[];
  upstream_url?: string;
  note: string;
};

export type TestCatalogItem = {
  id: string;
  name: string;
  category: string;
  description: string;
  supported_project_types: string[];
  required_manifest_fields: string[];
  required_genesis_features: string[];
  run_endpoint: string;
  parameters: Record<string, unknown>;
  output_metrics: string[];
  artifact_outputs: string[];
  status?: "available" | "missing_metadata" | "missing_genesis_feature" | "not_applicable";
  reasons?: string[];
  implemented?: boolean;
};

export type TestRunResult = {
  test_id: string;
  test_name: string;
  category: string;
  status: "pass" | "fail" | "warning" | "error";
  run_id: string;
  project_id: string;
  metrics: Record<string, unknown>;
  logs: string[];
  artifacts: Record<string, string | null>;
  sensor_output: Record<string, unknown>;
  render_output: Record<string, unknown>;
};
