"use client";

import { useEffect, useMemo, useState } from "react";
import { getShowcaseCatalog, launchShowcaseDemo, listScenarios, runScenario } from "@/lib/api";
import { useSimStore } from "@/lib/state";
import type { ShowcaseCatalog, ShowcaseCatalogEntry } from "@/lib/types";

type ScenarioRow = {
  id: string;
  name: string;
  description?: string;
  config?: Record<string, unknown>;
};

const LAYER_META: Record<string, { label: string; note: string; extras?: string }> = {
  physics: {
    label: "Physics",
    note: "Rigid-body and manipulation demos recorded for the web viewer.",
  },
  rendering: {
    label: "Rendering",
    note: "Camera and path-traced rendering demos.",
    extras: "Some Nyx demos need optional GPU plugins (CUDA 12.9+, driver 575+).",
  },
  "simulation-interface": {
    label: "Simulation Interface",
    note: "Sensors, GUI, controllers, and parallel environment demos.",
  },
  buildables: {
    label: "Buildables Robot Dog",
    note: "Runs your default or imported robot inside Buildables (web replay + metrics).",
  },
};

function layerForScenario(scenario: ScenarioRow): string {
  const layer = scenario.config?.genesis_layer;
  if (typeof layer === "string") return layer;
  if (scenario.id.startsWith("genesis-")) {
    if (scenario.id.includes("simulation-interface")) return "simulation-interface";
    const parts = scenario.id.split("-");
    if (parts.length >= 2) return parts[1];
  }
  return "buildables";
}

function isGenesisShowcaseScenario(scenario: ScenarioRow): boolean {
  return scenario.id.startsWith("genesis-") && scenario.config?.showcase_launchable !== false;
}

export function GenesisShowcasePanel() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const selectedScenarioId = useSimStore((s) => s.selectedScenarioId);
  const setSelectedScenarioId = useSimStore((s) => s.setSelectedScenarioId);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const addLog = useSimStore((s) => s.addLog);
  const [scenarios, setScenarios] = useState<ScenarioRow[]>([]);
  const [catalog, setCatalog] = useState<ShowcaseCatalog | null>(null);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [layerFilter, setLayerFilter] = useState<string>("all");
  const [running, setRunning] = useState(false);
  const [launching, setLaunching] = useState(false);

  useEffect(() => {
    void getShowcaseCatalog()
      .then((data) => {
        setCatalog(data);
        setCatalogError(null);
      })
      .catch((error) => {
        setCatalog(null);
        setCatalogError((error as Error).message);
      });
  }, []);

  useEffect(() => {
    if (!projectId) return;
    void listScenarios(projectId)
      .then((items) => setScenarios(items as ScenarioRow[]))
      .catch(() => setScenarios([]));
  }, [projectId]);

  const catalogById = useMemo(() => {
    const map = new Map<string, ShowcaseCatalogEntry>();
    for (const entry of catalog?.entries ?? []) {
      map.set(entry.scenario_id, entry);
    }
    return map;
  }, [catalog]);

  const grouped = useMemo(() => {
    const map = new Map<string, ScenarioRow[]>();
    for (const scenario of scenarios) {
      const layer = layerForScenario(scenario);
      const arr = map.get(layer) ?? [];
      arr.push(scenario);
      map.set(layer, arr);
    }
    return map;
  }, [scenarios]);

  const filtered = useMemo(() => {
    if (layerFilter === "all") return scenarios;
    return scenarios.filter((s) => layerForScenario(s) === layerFilter);
  }, [layerFilter, scenarios]);

  const selected = scenarios.find((s) => s.id === selectedScenarioId);
  const selectedLayer = selected ? layerForScenario(selected) : null;
  const layerInfo = selectedLayer ? LAYER_META[selectedLayer] : null;
  const selectedCatalog = selectedScenarioId ? catalogById.get(selectedScenarioId) : undefined;
  const selectedIsNative = selected ? isGenesisShowcaseScenario(selected) : false;
  const canLaunchNative = Boolean(selectedIsNative && selectedCatalog?.available);
  const canRunBuildables = Boolean(selected && !selectedIsNative);

  async function onRunBuildables() {
    if (!selectedScenarioId) return;
    setRunning(true);
    try {
      const run = await runScenario(projectId, selectedScenarioId);
      setRunResult(run);
      addLog(`[Showcase] ${selectedScenarioId} → ${run.status} (steps=${run.step_count})`);
    } catch (error) {
      addLog(`[Showcase][Error] ${(error as Error).message}`);
    } finally {
      setRunning(false);
    }
  }

  async function onLaunchNative() {
    if (!selectedScenarioId) return;
    setLaunching(true);
    try {
      const launch = await launchShowcaseDemo(projectId, selectedScenarioId);
      addLog(`[Showcase] Launched native demo ${launch.demo_name} (pid=${launch.pid})`);
      addLog(`[Showcase] ${launch.note}`);
    } catch (error) {
      addLog(`[Showcase][Launch] ${(error as Error).message}`);
    } finally {
      setLaunching(false);
    }
  }

  return (
    <div className="space-y-2 p-2 text-[11px]">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-xs font-semibold">Genesis Showcase</div>
        <div className="flex gap-1">
          {selectedIsNative ? (
            <button
              type="button"
              className="rounded border border-emerald-700 bg-emerald-50 px-2 py-0.5 text-[10px] disabled:opacity-40"
              disabled={!selectedScenarioId || !canLaunchNative || launching}
              onClick={() => void onLaunchNative()}
            >
              {launching ? "Launching…" : "Launch native demo"}
            </button>
          ) : null}
          {canRunBuildables ? (
            <button
              type="button"
              className="rounded border border-border bg-white px-2 py-0.5 text-[10px] disabled:opacity-40"
              disabled={!selectedScenarioId || running}
              onClick={() => void onRunBuildables()}
            >
              {running ? "Running…" : "Run in Buildables"}
            </button>
          ) : null}
        </div>
      </div>

      <p className="text-[10px] text-textMuted">
        Bundled physics demos run in the background; motion plays in the web viewer. Use <strong>Run demo</strong> on
        each simulation to load it in the center panel.
      </p>

      {catalog ? (
        <div className="rounded border border-slate-200 bg-slate-50 p-2 text-[10px]">
          <div className="font-medium">
            Native demos ready: {catalog.available}/{catalog.total}
          </div>
          {catalog.available < catalog.total ? (
            <div className="mt-1 space-y-0.5 text-textMuted">
              <div>Some demos need extra packages or environment variables — see the session log for details.</div>
            </div>
          ) : (
            <div className="mt-1 text-emerald-800">All demo simulations are ready on this machine.</div>
          )}
        </div>
      ) : catalogError ? (
        <div className="rounded border border-amber-200 bg-amber-50 p-2 text-[10px] text-amber-900">{catalogError}</div>
      ) : null}

      <label className="block">
        <span className="text-textMuted">Layer filter</span>
        <select className="mt-0.5 w-full rounded border border-border bg-white px-2 py-1" value={layerFilter} onChange={(e) => setLayerFilter(e.target.value)}>
          <option value="all">All layers</option>
          <option value="buildables">Buildables robot dog</option>
          <option value="physics">Physics</option>
          <option value="rendering">Rendering (+ Nyx)</option>
          <option value="simulation-interface">Simulation interface</option>
        </select>
      </label>

      <div className="max-h-52 overflow-auto rounded border border-border bg-white">
        {filtered.map((scenario) => {
          const layer = layerForScenario(scenario);
          const entry = catalogById.get(scenario.id);
          const native = isGenesisShowcaseScenario(scenario);
          return (
            <button
              key={scenario.id}
              type="button"
              onClick={() => setSelectedScenarioId(scenario.id)}
              className={`block w-full border-b border-border px-2 py-1.5 text-left last:border-0 ${selectedScenarioId === scenario.id ? "bg-sky-50" : "hover:bg-slate-50"}`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="font-medium">{scenario.name}</div>
                {native && entry ? (
                  <span className={`shrink-0 text-[9px] ${entry.available ? "text-emerald-700" : "text-amber-700"}`}>
                    {entry.available ? "native ready" : "setup needed"}
                  </span>
                ) : null}
              </div>
              <div className="text-[10px] text-textMuted">{LAYER_META[layer]?.label ?? layer}</div>
            </button>
          );
        })}
      </div>

      {selected && layerInfo ? (
        <div className="rounded border border-border bg-panel p-2 text-[10px]">
          <div className="font-medium">{selected.name}</div>
          <div className="mt-1 text-textMuted">{layerInfo.note}</div>
          {layerInfo.extras ? <div className="mt-1 text-amber-800">{layerInfo.extras}</div> : null}
          {selectedIsNative && selectedCatalog ? (
            <div className="mt-2 space-y-1 border-t border-border pt-2">
              <div>
                Script: <span className="text-textMuted">{selectedCatalog.script_relpath}</span>
              </div>
              {selectedCatalog.script_path ? (
                <div className="text-emerald-800">Resolved at {selectedCatalog.script_path}</div>
              ) : (
                <ul className="list-disc pl-4 text-amber-800">
                  {selectedCatalog.missing.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </div>
      ) : null}

      {[...grouped.entries()].map(([layer, items]) => (
        <div key={layer} className="text-[10px] text-textMuted">
          {LAYER_META[layer]?.label ?? layer}: {items.length} scenarios
        </div>
      ))}
    </div>
  );
}
