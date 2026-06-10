"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import {
  activateProject,
  clearActiveProject,
  getGenesisStatus,
  getManifest,
  getProjectTestsAvailable,
  getProjectTestsCatalog,
  getRunResult,
  listProjects,
  listScenarios,
  loadDefaultRobotArm,
  loadDefaultRobotDog,
  importFromDownloadsRobotDog,
  runGenesisScene,
  runNativeGenesisViewer,
  runScenario,
  runSelectedTest,
  runTestSuite,
  saveManifest,
  validateManifest,
} from "@/lib/api";
import { useSimStore } from "@/lib/state";
import { ImportProjectModal } from "./ImportProjectModal";
import { MoreMenu } from "./MoreMenu";
import { ScenarioSelector } from "./ScenarioSelector";

export function TopBar() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const manifest = useSimStore((s) => s.manifest);
  const selectedTestId = useSimStore((s) => s.selectedTestId);
  const selectedScenarioId = useSimStore((s) => s.selectedScenarioId);
  const testsCatalog = useSimStore((s) => s.testsCatalog);
  const isRunning = useSimStore((s) => s.isSimulationRunning);
  const setupError = useSimStore((s) => s.setupError);
  const dirty = useSimStore((s) => s.dirty);
  const lastRunManifestVersion = useSimStore((s) => s.lastRunManifestVersion);
  const manifestVersion = manifest?.version ?? null;
  const manifestStaleForRun =
    dirty || (lastRunManifestVersion !== null && manifestVersion !== null && manifestVersion !== lastRunManifestVersion);

  const setSelectedProjectId = useSimStore((s) => s.setSelectedProjectId);
  const setSelectedScenarioId = useSimStore((s) => s.setSelectedScenarioId);
  const setManifest = useSimStore((s) => s.setManifest);
  const setTestsCatalog = useSimStore((s) => s.setTestsCatalog);
  const setAvailableTests = useSimStore((s) => s.setAvailableTests);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const setSetupError = useSimStore((s) => s.setSetupError);
  const setSelectedTestId = useSimStore((s) => s.setSelectedTestId);
  const setIsSimulationRunning = useSimStore((s) => s.setIsSimulationRunning);
  const markSaved = useSimStore((s) => s.markSaved);
  const setValidationErrors = useSimStore((s) => s.setValidationErrors);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);
  const addLog = useSimStore((s) => s.addLog);

  const [genesisReady, setGenesisReady] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [showLoadDemo, setShowLoadDemo] = useState(false);
  const loadDemoRef = useRef<HTMLDivElement>(null);

  const projectMode = manifest?.project_mode ?? "default_demo";
  const modeLabel = projectMode === "imported_project" ? "Imported Project" : "Default Demo";
  const genesisBadge = setupError ? "Setup Required" : !genesisReady ? "Visual Preview Only" : "Genesis Ready";

  async function refreshTests(targetProjectId: string) {
    const testsCatalogRes = await getProjectTestsCatalog(targetProjectId);
    setTestsCatalog(testsCatalogRes.tests);
    const available = await getProjectTestsAvailable(targetProjectId);
    setAvailableTests(available.tests);
  }

  async function loadProject(
    loader: () => Promise<{ project_id: string }>,
    label: string,
  ) {
    try {
      const loaded = await loader();
      setSelectedProjectId(loaded.project_id);
      setSelectedPartId(null);
      useSimStore.setState({ lastRun: null, runTimeseries: [] });
      const nextManifest = await getManifest(loaded.project_id);
      setManifest(nextManifest);
      await refreshTests(loaded.project_id);
      const scenarios = await listScenarios(loaded.project_id);
      if (scenarios.length > 0) setSelectedScenarioId(scenarios[0].id);
      addLog(`[Project] ${label} loaded.`);
    } catch (error) {
      addLog(`[Project] Load failed: ${(error as Error).message}`);
    }
  }

  async function onRun() {
    if (dirty) {
      addLog("[Run] Save manifest before running — you have unsaved edits.");
      return;
    }
    if (lastRunManifestVersion !== null && manifestVersion !== null && manifestVersion !== lastRunManifestVersion) {
      addLog("[Run] Manifest changed since last run — re-run after saving to use the latest version.");
    }
    setIsSimulationRunning(true);
    try {
      if (selectedTestId) {
        const result = await runSelectedTest(projectId, selectedTestId);
        const run = await getRunResult(result.run_id);
        setRunResult(run);
        addLog(`[Run] ${result.test_name} → ${result.status}`);
      } else if (selectedScenarioId) {
        const run = await runScenario(projectId, selectedScenarioId);
        setRunResult(run);
        addLog(`[Run] Scenario ${selectedScenarioId} → ${run.status} (steps=${run.step_count})`);
      } else {
        const run = await runGenesisScene(projectId, 180);
        setRunResult(run);
        addLog(`[Run] Genesis scene complete. steps=${run.step_count}`);
      }
      await refreshTests(projectId);
    } catch (error) {
      addLog(`[Run][Error] ${(error as Error).message}`);
    } finally {
      setIsSimulationRunning(false);
    }
  }

  function onStop() {
    setIsSimulationRunning(false);
    addLog("[Run] Stop requested.");
  }

  function onReset() {
    useSimStore.setState({ lastRun: null, runTimeseries: [], metrics: {} });
    addLog("[Run] Viewport reset.");
  }

  useEffect(() => {
    void (async () => {
      try {
        const status = await getGenesisStatus();
        setGenesisReady(status.installed);
      } catch {
        setGenesisReady(false);
      }
    })();
  }, [setupError]);

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (loadDemoRef.current && !loadDemoRef.current.contains(e.target as Node)) {
        setShowLoadDemo(false);
      }
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  const toolbarBtn =
    "rounded border border-border bg-white px-2.5 py-1 text-xs font-medium text-textMain transition hover:bg-slate-50 disabled:opacity-40";
  const primaryBtn = "rounded bg-accent px-2.5 py-1 text-xs font-medium text-white transition hover:bg-accent/90 disabled:opacity-40";

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-white px-3 text-textMain shadow-sm">
      {/* Left */}
      <div className="flex min-w-0 items-center gap-2">
        <span className="whitespace-nowrap text-sm font-semibold tracking-tight">Buildables Sim</span>
        <span className="hidden truncate text-xs text-textMuted sm:inline">{manifest?.project_name ?? "—"}</span>
        <span className="rounded border border-border bg-panel px-1.5 py-0.5 text-[10px] font-medium text-textMuted">{modeLabel}</span>
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ring-1 ${
            dirty
              ? "bg-amber-50 text-amber-800 ring-amber-200"
              : manifestStaleForRun
                ? "bg-orange-50 text-orange-800 ring-orange-200"
                : "bg-slate-50 text-textMuted ring-border"
          }`}
        >
          {dirty ? "Unsaved" : manifestStaleForRun ? "Stale run" : "Saved"}
        </span>
        <span
          className={`rounded px-1.5 py-0.5 text-[10px] font-medium ring-1 ${
            genesisBadge === "Genesis Ready"
              ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
              : genesisBadge === "Visual Preview Only"
                ? "bg-amber-50 text-amber-800 ring-amber-200"
                : "bg-rose-50 text-rose-700 ring-rose-200"
          }`}
        >
          {genesisBadge}
        </span>
      </div>

      {/* Center */}
      <div className="flex flex-1 items-center justify-center gap-1">
        <Link
          href="/genesis"
          className="rounded border-2 border-[#FF6A1A] bg-[#FF6A1A] px-3 py-1 text-xs font-semibold text-white shadow-sm transition hover:bg-[#e55f15]"
          title="Open Tekong EMart — demo simulations and web viewer"
        >
          Tekong EMart →
        </Link>
        <button type="button" className={toolbarBtn} onClick={() => setShowImport(true)}>
          Import
        </button>
        <div className="relative" ref={loadDemoRef}>
          <button type="button" className={toolbarBtn} onClick={() => setShowLoadDemo((v) => !v)}>
            Load Demo ▾
          </button>
          {showLoadDemo ? (
            <div className="absolute left-0 top-full z-50 mt-1 min-w-[160px] rounded border border-border bg-white py-1 shadow-lg">
              <button
                type="button"
                className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50"
                onClick={() => {
                  setShowLoadDemo(false);
                  void loadProject(async () => {
                    const result = await importFromDownloadsRobotDog();
                    return { project_id: String(result.project_id) };
                  }, "Robot Dog from Downloads");
                }}
              >
                My Robot Dog (Downloads URDF)
              </button>
              <button
                type="button"
                className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50"
                onClick={() => {
                  setShowLoadDemo(false);
                  void loadProject(loadDefaultRobotArm, "Robot Arm Demo");
                }}
              >
                Robot Arm Demo
              </button>
              <button
                type="button"
                className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50"
                onClick={() => {
                  setShowLoadDemo(false);
                  void loadProject(loadDefaultRobotDog, "Default Robot Dog");
                }}
              >
                Robot Dog Demo
              </button>
            </div>
          ) : null}
        </div>
        <button type="button" className={primaryBtn} disabled={isRunning || Boolean(setupError)} onClick={() => void onRun()}>
          {isRunning ? "Running…" : "Run"}
        </button>
        <button type="button" className={toolbarBtn} disabled={!isRunning} onClick={onStop}>
          Stop
        </button>
        <button type="button" className={toolbarBtn} onClick={onReset}>
          Reset
        </button>
      </div>

      {/* Right */}
      <div className="flex items-center gap-2">
        <ScenarioSelector />
        <select
          className="max-w-[160px] rounded border border-border bg-white px-2 py-1 text-xs text-textMain"
          value={selectedTestId ?? ""}
          onChange={(e) => setSelectedTestId(e.target.value || null)}
        >
          <option value="">Select test…</option>
          {testsCatalog.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </select>
        <MoreMenu
          onSave={async () => {
            if (!manifest) return;
            const validation = await validateManifest(projectId);
            setValidationErrors(validation.errors);
            if (!validation.valid) {
              addLog(`[Validation] ${validation.errors.join("; ")}`);
              return;
            }
            const saved = await saveManifest(projectId, manifest);
            const refreshed = (saved as { manifest?: typeof manifest }).manifest ?? manifest;
            markSaved(refreshed);
            addLog("[Save] Manifest saved.");
          }}
          onRunSuite={async () => {
            const suite = await runTestSuite(projectId);
            addLog(`[TestLab] Suite pass_rate=${suite.summary.suite_pass_rate ?? "n/a"}%`);
            await refreshTests(projectId);
          }}
          onRunGenesisScene={async () => {
            const run = await runGenesisScene(projectId, 240);
            setRunResult(run);
            addLog(`[Genesis] steps=${run.step_count}`);
          }}
          onNativeViewer={async () => {
            const result = await runNativeGenesisViewer(projectId, 600);
            addLog(`[Genesis] Native viewer: ${JSON.stringify(result)}`);
          }}
          onSwitchProject={async () => {
            const projects = await listProjects();
            const idx = projects.findIndex((p) => p.project_id === projectId);
            const next = projects[(idx + 1) % projects.length];
            if (!next) return;
            await activateProject(next.project_id);
            setSelectedProjectId(next.project_id);
            setManifest(await getManifest(next.project_id));
            await refreshTests(next.project_id);
            addLog(`[Project] Switched to ${next.project_name}`);
          }}
          onClearProject={async () => {
            await clearActiveProject();
            await loadProject(loadDefaultRobotDog, "Default Robot Dog");
          }}
          onError={(message) => {
            addLog(`[Menu][Error] ${message}`);
          }}
          dirty={dirty}
        />
      </div>

      {showImport ? <ImportProjectModal onClose={() => setShowImport(false)} /> : null}
    </header>
  );
}
