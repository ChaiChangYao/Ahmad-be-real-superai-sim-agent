"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getGenesisWorkbenchReadiness,
  getShowcaseCatalog,
  getWorkbenchLaunchProject,
  type GenesisWorkbenchReadiness,
  type ShowcaseCatalog,
} from "@/lib/genesisWorkbenchApi";
import { waitForApiHealth } from "@/lib/api";

import { GenesisCataloguePanel } from "./GenesisCataloguePanel";
import { GenesisDemoDetail } from "./GenesisDemoDetail";
import { GenesisHorizontalSplit, GenesisWorkbenchLayout } from "./GenesisWorkbenchLayout";
import { GenesisLogTerminal } from "./GenesisLogTerminal";
import { GenesisProjectImport } from "./GenesisProjectImport";
import { GenesisReadinessPanel } from "./GenesisReadinessPanel";
import { GenesisShowcaseViewport } from "./GenesisShowcaseViewport";
import { LaunchFailureModal, type LaunchFailureInfo } from "./LaunchFailureModal";
import { accent, accentBg, accentHover } from "./buildablesTheme";
import { EngineeringReportPanel } from "./assistant/EngineeringReportPanel";
import type { EngineeringReport } from "@/lib/agentic/types";
import type { ReplayBundle } from "./replay/types";

type MainTab = "catalogue" | "projects";
export type BootStatus = "pending" | "ready" | "error";
type BootPhase = "api" | "data" | "done";

export function GenesisWorkbenchShell() {
  const [mainTab, setMainTab] = useState<MainTab>("catalogue");
  const [readiness, setReadiness] = useState<GenesisWorkbenchReadiness | null>(null);
  const [catalog, setCatalog] = useState<ShowcaseCatalog | null>(null);
  const [launchProjectId, setLaunchProjectId] = useState<string>("genesis-workbench");
  const [customProjectId, setCustomProjectId] = useState<string | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null);
  const [bootStatus, setBootStatus] = useState<BootStatus>("ready");
  const [bootPhase, setBootPhase] = useState<BootPhase>("api");
  const [bootError, setBootError] = useState<string | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [replay, setReplay] = useState<ReplayBundle | null>(null);
  const [lifecycle, setLifecycle] = useState<string | null>("idle");
  const [launchFailure, setLaunchFailure] = useState<LaunchFailureInfo | null>(null);
  const [agenticRunId, setAgenticRunId] = useState<string | null>(null);
  const [latestReport, setLatestReport] = useState<EngineeringReport | null>(null);

  const addLog = useCallback((msg: string) => {
    const stamp = new Date().toISOString();
    setLog((prev) => [...prev, `[${stamp}] ${msg}`]);
  }, []);

  const clearLog = useCallback(() => {
    setLog([]);
  }, []);

  const onReplay = useCallback((bundle: ReplayBundle | null) => {
    setReplay(bundle);
    if (!bundle) return;
    const rid = String(bundle.meta?.agentic_run_id ?? bundle.launchId ?? "");
    if (rid.startsWith("agentic-")) setAgenticRunId(rid);
  }, []);

  const activeProjectId = customProjectId ?? launchProjectId;

  const selectedEntry = useMemo(() => {
    if (!selectedScenarioId || !catalog) return null;
    return catalog.entries.find((e) => e.scenario_id === selectedScenarioId) ?? null;
  }, [catalog, selectedScenarioId]);

  useEffect(() => {
    setReplay(null);
    setLifecycle("idle");
    setLaunchFailure(null);
  }, [selectedScenarioId]);

  const loadWorkbench = useCallback(async () => {
    setBootPhase("api");
    setBootError(null);
    let apiReady = false;
    try {
      await waitForApiHealth({ timeoutMs: 12_000, intervalMs: 500 });
      apiReady = true;
      setBootStatus("ready");
      setBootPhase("data");
      const [r, c, lp] = await Promise.all([
        getGenesisWorkbenchReadiness(),
        getShowcaseCatalog(),
        getWorkbenchLaunchProject(),
      ]);
      setReadiness(r);
      setCatalog(c);
      setLaunchProjectId(lp.project_id);
      const minimal = c.entries.find((e) => e.scenario_id.includes("minimal-cube-motion"));
      setSelectedScenarioId(minimal?.scenario_id ?? c.entries[0]?.scenario_id ?? null);
      setBootPhase("done");
      setBootError(null);
    } catch (error) {
      const message = (error as Error).message;
      setBootStatus("ready");
      setBootPhase("done");
      if (apiReady) {
        setBootError(`Workbench data failed to load: ${message}`);
      } else {
        setBootError(message);
      }
    }
  }, []);

  useEffect(() => {
    void loadWorkbench();
  }, [loadWorkbench]);

  const catalogueDemoType = selectedEntry?.demo_type ?? null;
  const catalogueKind = selectedEntry?.kind ?? null;
  const catalogueSensorType = selectedEntry?.sensor_type ?? null;
  const projectsDemoType = String(replay?.meta?.demo_type ?? "");
  const projectsKind = String(replay?.meta?.kind ?? "");
  const projectsManifest = replay?.meta?.manifest as { telemetry?: { sensorTypes?: string[] } } | undefined;
  const projectsSensorType =
    String(
      replay?.meta?.sensor_type ??
        projectsManifest?.telemetry?.sensorTypes?.[0] ??
        (replay?.meta?.test_id === "imu_sensor" ? "imu" : replay?.meta?.test_id ?? ""),
    ) || null;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-slate-50 text-slate-900">
      <header className="flex shrink-0 items-center gap-2 border-b border-slate-200 bg-white px-3 py-2">
        <span className={`text-sm font-semibold tracking-tight ${accent}`}>Tekong EMart</span>
        <span className="text-[10px] text-slate-600">Physics engine · web viewer on all GPUs</span>
        <div className="flex-1" />
      </header>

      {bootPhase === "api" && !bootError ? (
        <div className="shrink-0 border-b border-slate-200 bg-slate-100 px-3 py-1.5 text-[10px] text-slate-600">
          Connecting to API…
        </div>
      ) : bootPhase === "data" ? (
        <div className="shrink-0 border-b border-slate-200 bg-slate-100 px-3 py-1.5 text-[10px] text-slate-600">
          Loading demo simulations and environment (first load may take a minute while PyTorch initializes)…
        </div>
      ) : null}
      {bootStatus === "error" && bootError ? (
        <div className="shrink-0 flex flex-wrap items-center gap-2 border-b border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-800">
          <span className="min-w-0 flex-1">{bootError}</span>
          <button
            type="button"
            className={`shrink-0 rounded px-2 py-0.5 text-[10px] text-white ${accentBg} ${accentHover}`}
            onClick={() => void loadWorkbench()}
          >
            Retry
          </button>
          <div className="w-full text-[10px]">
            {bootError.includes("404") ? (
              <>
                Restart the API: from the repo root run{" "}
                <code className="rounded bg-slate-200 px-1">npm run dev</code>, then refresh.
              </>
            ) : (
              <>
                First time? Run <code className="rounded bg-slate-200 px-1">npm run setup:api</code> then{" "}
                <code className="rounded bg-slate-200 px-1">npm run dev</code>. My Projects still works offline for
                browsing the entry screen.
              </>
            )}
          </div>
        </div>
      ) : null}
      {bootStatus === "ready" && bootError ? (
        <div className="shrink-0 flex flex-wrap items-center gap-2 border-b border-amber-300/60 bg-amber-50 px-3 py-1.5 text-[10px] text-amber-800">
          <span className="min-w-0 flex-1">{bootError}</span>
          <button
            type="button"
            className={`shrink-0 rounded px-2 py-0.5 text-[10px] text-white ${accentBg} ${accentHover}`}
            onClick={() => void loadWorkbench()}
          >
            Retry
          </button>
        </div>
      ) : null}

      <div className="flex shrink-0 gap-1 border-b border-slate-200 px-3 py-1">
        <button
          type="button"
          className={`rounded px-3 py-1 text-xs ${mainTab === "catalogue" ? "bg-slate-200 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
          onClick={() => setMainTab("catalogue")}
        >
          Demo Simulations
        </button>
        <button
          type="button"
          data-testid="tab-my-projects"
          className={`rounded px-3 py-1 text-xs ${mainTab === "projects" ? "bg-slate-200 text-slate-900" : "text-slate-600 hover:text-slate-900"}`}
          onClick={() => setMainTab("projects")}
        >
          My Projects
        </button>
      </div>

      {mainTab === "catalogue" ? (
        <GenesisWorkbenchLayout
          left={
            <GenesisCataloguePanel
              catalog={catalog}
              bootStatus={bootStatus}
              selectedScenarioId={selectedScenarioId}
              onSelect={setSelectedScenarioId}
            />
          }
          center={
            <GenesisShowcaseViewport
              replay={replay}
              lifecycle={lifecycle}
              replayComplete={lifecycle === "completed"}
              demoType={catalogueDemoType}
              catalogKind={catalogueKind}
              sensorType={catalogueSensorType}
            />
          }
          right={
            <div className="space-y-3">
              <GenesisDemoDetail
                entry={selectedEntry}
                launchProjectId={launchProjectId}
                onLog={addLog}
                onReplay={onReplay}
                onLifecycle={setLifecycle}
                onLaunchFailure={setLaunchFailure}
                variant="sidebar"
              />
              <GenesisReadinessPanel readiness={readiness} catalog={catalog} bootStatus={bootStatus} />
            </div>
          }
          bottom={<GenesisLogTerminal lines={log} onClear={clearLog} defaultExpanded={false} />}
        />
      ) : (
        <div className="min-h-0 flex-1">
          <GenesisHorizontalSplit
            storageKey="projects-import-viewer"
            defaultLeft={50}
            left={
              <div className="h-full min-h-0 overflow-hidden">
                <GenesisProjectImport
                  customProjectId={customProjectId}
                  onProjectImported={(id) => {
                    setCustomProjectId(id);
                    addLog(`[Import] Project ${id} ready`);
                  }}
                  onLaunchNative={addLog}
                  onReplay={onReplay}
                  onLifecycle={setLifecycle}
                  onLaunchFailure={setLaunchFailure}
                  onAgenticRunIdChange={setAgenticRunId}
                  onReportChange={setLatestReport}
                />
              </div>
            }
            right={
              <div className="flex h-full min-h-0 flex-col gap-2 p-2">
                <div className="min-h-0 flex-1">
                  <GenesisShowcaseViewport
                    replay={replay}
                    lifecycle={lifecycle}
                    replayComplete={lifecycle === "completed"}
                    demoType={projectsDemoType || null}
                    catalogKind={projectsKind || null}
                    sensorType={projectsSensorType}
                    runId={agenticRunId}
                  />
                </div>
                {latestReport ? (
                  <div className="max-h-[220px] shrink-0">
                    <EngineeringReportPanel report={latestReport} onClose={() => setLatestReport(null)} />
                  </div>
                ) : null}
              </div>
            }
          />
          <GenesisLogTerminal lines={log} onClear={clearLog} />
        </div>
      )}

      <LaunchFailureModal
        open={Boolean(launchFailure)}
        failure={launchFailure}
        onClose={() => setLaunchFailure(null)}
      />
    </div>
  );
}
