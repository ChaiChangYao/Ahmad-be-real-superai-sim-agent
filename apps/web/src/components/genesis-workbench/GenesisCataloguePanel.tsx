"use client";

import { useMemo, useState } from "react";
import type { ShowcaseCatalog } from "@/lib/genesisWorkbenchApi";
import type { BootStatus } from "./GenesisWorkbenchShell";

const SECTIONS: Array<{ id: string; label: string; filter: (layer: string, repo: string, name: string) => boolean }> = [
  { id: "physics", label: "Physics", filter: (layer) => layer === "physics" },
  {
    id: "rendering",
    label: "Rendering",
    filter: (layer, repo) => layer === "rendering" && repo === "genesis-world",
  },
  {
    id: "nyx",
    label: "Nyx",
    filter: (layer, repo) => layer === "rendering" && repo === "genesis-nyx",
  },
  {
    id: "simulation-interface",
    label: "Simulation Interface",
    filter: (layer) => layer === "simulation-interface",
  },
];

type Props = {
  catalog: ShowcaseCatalog | null;
  bootStatus?: BootStatus;
  selectedScenarioId: string | null;
  onSelect: (id: string) => void;
};

function catalogStatusLabel(catalog: ShowcaseCatalog | null, bootStatus?: BootStatus) {
  if (catalog) return `${catalog.available}/${catalog.total} native ready`;
  if (bootStatus === "error") return "API unavailable — use Retry above";
  return "Demo simulations unavailable — start API and click Retry";
}

export function GenesisCataloguePanel({ catalog, bootStatus, selectedScenarioId, onSelect }: Props) {
  const [section, setSection] = useState("physics");

  const entries = useMemo(() => {
    if (!catalog) return [];
    const sec = SECTIONS.find((s) => s.id === section);
    if (!sec) return catalog.entries;
    return catalog.entries.filter((e) => sec.filter(e.layer, e.repo, e.demo_name));
  }, [catalog, section]);

  return (
    <div className="flex h-full flex-col text-[11px]">
      <div className="border-b border-slate-200 p-2">
        <div className="font-semibold text-slate-800">Demo Simulations</div>
        <div className="mt-0.5 text-[10px] text-slate-600">
          {catalogStatusLabel(catalog, bootStatus)}
        </div>
      </div>
      <div className="flex flex-wrap gap-1 border-b border-slate-200 p-2">
        {SECTIONS.map((s) => (
          <button
            key={s.id}
            type="button"
            onClick={() => setSection(s.id)}
            className={`rounded px-1.5 py-0.5 text-[10px] ${section === s.id ? "bg-[#FF6A1A]/20 text-[#c2410c]" : "text-slate-600 hover:bg-slate-100"}`}
          >
            {s.label}
          </button>
        ))}
      </div>
      <div className="min-h-0 flex-1 overflow-auto">
        {entries.map((entry) => (
          <button
            key={entry.scenario_id}
            type="button"
            onClick={() => onSelect(entry.scenario_id)}
            className={`block w-full border-b border-slate-200 px-2 py-2 text-left hover:bg-slate-100/50 ${
              selectedScenarioId === entry.scenario_id ? "bg-slate-100" : ""
            }`}
          >
            <div className="flex items-start justify-between gap-1">
              <span className="font-medium text-slate-900">{entry.demo_name}</span>
              <span className={`shrink-0 text-[9px] ${entry.available ? "text-[#FF6A1A]" : "text-amber-400"}`}>
                {entry.available ? "ready" : "setup"}
              </span>
            </div>
            {entry.optional_extra ? (
              <div className="mt-0.5 text-[9px] text-violet-700">extra: {entry.optional_extra}</div>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
}
