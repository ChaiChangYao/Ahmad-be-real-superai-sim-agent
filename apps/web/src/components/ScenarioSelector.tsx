"use client";

import { useEffect, useMemo, useState } from "react";
import { listScenarios } from "@/lib/api";
import { useSimStore } from "@/lib/state";

type ScenarioItem = {
  id: string;
  name: string;
  config?: Record<string, unknown>;
};

function scenarioGroup(item: ScenarioItem): string {
  const layer = item.config?.genesis_layer;
  if (layer === "physics") return "Genesis · Physics";
  if (layer === "rendering") return "Genesis · Rendering (Nyx)";
  if (layer === "simulation-interface") return "Genesis · Simulation Interface";
  if (item.id.startsWith("genesis-")) return "Genesis · Showcase";
  return "Buildables · Robot Dog";
}

export function ScenarioSelector() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const selectedScenarioId = useSimStore((s) => s.selectedScenarioId);
  const setSelectedScenarioId = useSimStore((s) => s.setSelectedScenarioId);
  const [scenarios, setScenarios] = useState<ScenarioItem[]>([]);

  useEffect(() => {
    if (!projectId) return;

    async function load() {
      try {
        const items = await listScenarios(projectId);
        setScenarios(items as ScenarioItem[]);
        if (items.length > 0 && !items.some((s) => s.id === selectedScenarioId)) {
          setSelectedScenarioId(items[0].id);
        }
      } catch {
        setScenarios([]);
      }
    }
    void load();
  }, [projectId, selectedScenarioId, setSelectedScenarioId]);

  const grouped = useMemo(() => {
    const map = new Map<string, ScenarioItem[]>();
    for (const item of scenarios) {
      const group = scenarioGroup(item);
      const arr = map.get(group) ?? [];
      arr.push(item);
      map.set(group, arr);
    }
    return [...map.entries()];
  }, [scenarios]);

  return (
    <label className="text-xs text-textMuted">
      <span className="mr-1">Scenario</span>
      <select
        className="max-w-[220px] rounded border border-border bg-white px-2 py-1 text-xs text-slate-800"
        value={selectedScenarioId}
        onChange={(e) => setSelectedScenarioId(e.target.value)}
      >
        {grouped.map(([group, items]) => (
          <optgroup key={group} label={group}>
            {items.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </label>
  );
}
