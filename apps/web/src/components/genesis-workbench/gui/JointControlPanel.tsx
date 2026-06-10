"use client";

import { useMemo } from "react";
import type { ReplayBundle } from "../replay/types";
import { accent } from "../buildablesTheme";

type Props = {
  replay: ReplayBundle | null;
  frameIndex: number;
};

export function JointControlPanel({ replay, frameIndex }: Props) {
  const joints = useMemo(() => {
    if (!replay?.frames.length) return [];
    const idx = Math.min(frameIndex, replay.frames.length - 1);
    const qpos = replay.frames[idx]?.qpos ?? {};
    return Object.entries(qpos).map(([name, values]) => ({
      name,
      value: Array.isArray(values) ? values[0] ?? 0 : 0,
    }));
  }, [replay, frameIndex]);

  return (
    <div className="flex h-full flex-col border-l border-slate-200 bg-slate-100">
      <div className={`border-b border-slate-200 px-3 py-2 text-xs font-medium ${accent}`}>
        Joint control (read-only preview)
      </div>
      <div className="flex-1 overflow-auto p-3">
        {joints.length === 0 ? (
          <p className="text-xs text-slate-500">Run the ImGui joint control demo to see joint positions here.</p>
        ) : (
          <ul className="space-y-3">
            {joints.map((joint) => (
              <li key={joint.name}>
                <div className="mb-1 flex justify-between text-[11px] text-slate-700">
                  <span className="truncate">{joint.name}</span>
                  <span className="font-mono text-slate-600">{joint.value.toFixed(3)}</span>
                </div>
                <input
                  type="range"
                  min={-3.14}
                  max={3.14}
                  step={0.01}
                  value={joint.value}
                  readOnly
                  className="w-full accent-[#FF6A1A]"
                />
              </li>
            ))}
          </ul>
        )}
        <p className="mt-4 text-[10px] text-slate-500">
          Web joint commanding is not yet wired; sliders mirror recorded qpos from the replay.
        </p>
      </div>
    </div>
  );
}
