import type { ShowcaseCatalog, ShowcaseCatalogEntry, ShowcaseLaunchResult } from "./types";
import {
  apiFetch,
  getShowcaseCatalog,
  getShowcaseLaunchLogs,
  getShowcaseLaunchStatus,
  getShowcaseLaunchTelemetry,
  getShowcaseLaunchTimeseries,
  launchShowcaseDemo,
  runNativeGenesisViewer,
} from "./api";

export type GenesisWorkbenchReadiness = {
  platform: string;
  python_version: string;
  torch_version: string | null;
  genesis_world_pip: string | null;
  genesis_world_root: string | null;
  genesis_nyx_root: string | null;
  showcase: { total: number; available: number };
  optional_extras: Record<string, { installed: boolean; message: string | null }>;
  gpu: { available: boolean; detail?: string; gpu_name?: string; driver_version?: string; nyx_note?: string };
};

export type RequirementsItem = {
  id: string;
  label: string;
  status: "ok" | "missing" | "warning" | "optional" | "info";
  detail: string;
  commands: string[];
  links: Array<{ label: string; url: string }>;
};

export type UploadRequirements = {
  context: string;
  title?: string;
  summary?: string;
  items: RequirementsItem[];
  error?: string;
  scenario_id?: string;
  demo_name?: string;
  available?: boolean;
  upstream_url?: string;
  project_id?: string;
  simulation_readiness?: Record<string, unknown>;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function getGenesisWorkbenchReadiness(): Promise<GenesisWorkbenchReadiness> {
  const res = await apiFetch(`${API_BASE}/genesis/workbench/readiness`, {
    cache: "no-store",
    timeoutMs: 120_000,
  });
  if (!res.ok) throw new Error(`Readiness fetch failed: ${res.status}`);
  return res.json();
}

export async function getUploadRequirements(params: {
  context: "environment" | "demo" | "custom";
  scenarioId?: string;
  projectId?: string;
}): Promise<UploadRequirements> {
  const q = new URLSearchParams({ context: params.context });
  if (params.scenarioId) q.set("scenario_id", params.scenarioId);
  if (params.projectId) q.set("project_id", params.projectId);
  const res = await apiFetch(`${API_BASE}/genesis/workbench/upload-requirements?${q}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Requirements fetch failed: ${res.status}`);
  return res.json();
}

export async function getWorkbenchLaunchProject(): Promise<{ project_id: string; project_name: string }> {
  const res = await apiFetch(`${API_BASE}/genesis/workbench/launch-project`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Launch project fetch failed: ${res.status}`);
  return res.json();
}

export type LaunchReadiness = {
  project_id: string;
  can_launch_native: boolean;
  can_launch_web: boolean;
  can_preview_skeleton_web?: boolean;
  missing_mesh_count?: number;
  first_missing_mesh?: string | null;
  mesh_table?: Array<Record<string, unknown>>;
  reasons: string[];
  disabled_reason_native?: string | null;
  disabled_reason_web?: string | null;
  step_note?: string | null;
  simulation_readiness?: Record<string, unknown>;
  robot_description_candidates?: Array<{ type: string; path: string }>;
};

export async function getProjectLaunchReadiness(projectId: string): Promise<LaunchReadiness> {
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/workbench/launch-readiness`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Launch readiness fetch failed: ${res.status}`);
  return res.json();
}

export async function launchProjectWebViewer(
  projectId: string,
  steps = 400,
  options?: { skeleton?: boolean },
): Promise<ShowcaseLaunchResult> {
  const skeleton = options?.skeleton ? "&skeleton=true" : "";
  const res = await apiFetch(`${API_BASE}/projects/${projectId}/genesis/workbench/launch-web?steps=${steps}${skeleton}`, {
    method: "POST",
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { detail?: string }).detail ?? `Web launch failed: ${res.status}`);
  }
  return res.json();
}

export async function getProjectSensorValidation(projectId: string, test: string): Promise<Record<string, unknown>> {
  const q = new URLSearchParams({ test });
  const res = await apiFetch(`${API_BASE}/projects/${encodeURIComponent(projectId)}/genesis/workbench/sensor-validation?${q}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Sensor validation fetch failed: ${res.status}`);
  return res.json();
}

export { getShowcaseCatalog, launchShowcaseDemo, getShowcaseLaunchStatus, getShowcaseLaunchTelemetry, getShowcaseLaunchTimeseries, getShowcaseLaunchLogs, runNativeGenesisViewer };
export type { ShowcaseCatalog, ShowcaseCatalogEntry, ShowcaseLaunchResult };
