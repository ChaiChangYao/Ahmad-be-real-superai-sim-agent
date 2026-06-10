"use client";

import { useEffect, useState } from "react";
import {
  getActiveProject,
  getGenesisCatalog,
  getGenesisStatus,
  getManifest,
  getProjectTestsAvailable,
  getProjectTestsCatalog,
  listScenarios,
  loadDefaultRobotDog,
  waitForApiHealth,
} from "@/lib/api";
import { useSimStore } from "@/lib/state";
import { BottomDrawer } from "./BottomDrawer";
import { ErrorBoundary } from "./ErrorBoundary";
import { InspectorPanel } from "./InspectorPanel";
import { SetupErrorPanel } from "./SetupErrorPanel";
import { SimulationViewport } from "./simulation/SimulationViewport";
import { ViewportPlaceholder } from "./simulation/ViewportPlaceholder";
import { TopBar } from "./TopBar";
import { WorkbenchLayout } from "./WorkbenchLayout";
import { WorkbenchSidebar } from "./WorkbenchSidebar";

export function AppShell() {
  const [bootMessage, setBootMessage] = useState<string | null>("Connecting to API…");
  const setupError = useSimStore((s) => s.setupError);
  const setSetupError = useSimStore((s) => s.setSetupError);
  const setSelectedProjectId = useSimStore((s) => s.setSelectedProjectId);
  const setSelectedScenarioId = useSimStore((s) => s.setSelectedScenarioId);
  const setManifest = useSimStore((s) => s.setManifest);
  const setTestsCatalog = useSimStore((s) => s.setTestsCatalog);
  const setAvailableTests = useSimStore((s) => s.setAvailableTests);
  const setGenesisCatalog = useSimStore((s) => s.setGenesisCatalog);
  const addLog = useSimStore((s) => s.addLog);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        setBootMessage("Waiting for API (Genesis backend)…");
        await waitForApiHealth({ timeoutMs: 90_000, intervalMs: 1000 });
        if (cancelled) return;
        const active = await getActiveProject();
        const loaded = active.project_id ? { project_id: active.project_id } : await loadDefaultRobotDog();
        if (cancelled) return;
        setSelectedProjectId(loaded.project_id);
        const status = await getGenesisStatus();
        setSetupError(status.installed ? null : status.error ?? status.setup_instructions);
        const manifest = await getManifest(loaded.project_id);
        setManifest(manifest);
        const [testsCatalog, availableTests, genesisCatalog, scenarios] = await Promise.all([
          getProjectTestsCatalog(loaded.project_id),
          getProjectTestsAvailable(loaded.project_id),
          getGenesisCatalog(),
          listScenarios(loaded.project_id),
        ]);
        if (cancelled) return;
        setTestsCatalog(testsCatalog.tests);
        setAvailableTests(availableTests.tests);
        setGenesisCatalog(genesisCatalog);
        if (scenarios.length > 0) setSelectedScenarioId(scenarios[0].id);
        addLog("[Project] Ready — robot dog loaded.");
        setBootMessage(null);
      } catch (error) {
        if (cancelled) return;
        setSetupError((error as Error).message);
        setBootMessage(null);
      }
    }
    void init();
    return () => {
      cancelled = true;
    };
  }, [setSetupError, setManifest, setSelectedProjectId, setSelectedScenarioId, addLog, setTestsCatalog, setAvailableTests, setGenesisCatalog]);

  return (
    <div className="flex h-screen w-full flex-col overflow-hidden bg-panel text-textMain">
      <TopBar />

      {bootMessage ? (
        <div className="shrink-0 border-b border-border bg-sky-50 px-3 py-1 text-xs text-sky-900">{bootMessage}</div>
      ) : null}
      {setupError ? (
        <div className="shrink-0 px-2 py-1">
          <SetupErrorPanel message={setupError} />
        </div>
      ) : null}

      <WorkbenchLayout
        left={<WorkbenchSidebar />}
        center={
          <ErrorBoundary fallback={<ViewportPlaceholder message="3D viewer error — try refreshing." />}>
            <div className="relative h-full w-full" style={{ minHeight: 320 }}>
              <SimulationViewport />
            </div>
          </ErrorBoundary>
        }
        right={<InspectorPanel />}
        bottom={<BottomDrawer />}
      />
    </div>
  );
}
