"use client";

import { useSimStore } from "@/lib/state";

export function ProjectTree() {
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);
  const manifest = useSimStore((s) => s.manifest);

  const nodes = [
    ...(manifest?.links.map((item) => `link:${item.id}`) ?? []),
    ...(manifest?.joints.map((item) => `joint:${item.id}`) ?? []),
    ...(manifest?.actuators.map((item) => `actuator:${item.id}`) ?? []),
    ...(manifest?.sensors.map((item) => `sensor:${item.id}`) ?? []),
  ];

  return (
    <div className="h-full overflow-auto p-2 text-[11px]">
      <div className="mb-1 font-semibold text-textMain">Entities</div>
      <ul className="space-y-0.5">
        {nodes.map((node) => (
          <li key={node}>
            <button
              type="button"
              className={`w-full rounded px-2 py-0.5 text-left font-mono text-[10px] ${
                selectedPartId === node
                  ? "bg-accent text-white"
                  : "text-textMuted hover:bg-slate-100 hover:text-textMain"
              }`}
              onClick={() => setSelectedPartId(node)}
            >
              {node.replace("link:", "").replace("joint:", "⚙ ")}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
