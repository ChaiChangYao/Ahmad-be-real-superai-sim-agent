"use client";

import { useState } from "react";
import { getRunResult, runSelectedTest } from "@/lib/api";
import { useSimStore } from "@/lib/state";

export function ForcesLoadsPanel() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const manifest = useSimStore((s) => s.manifest);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const setShowPayloadPreview = useSimStore((s) => s.setShowPayloadPreview);
  const addLog = useSimStore((s) => s.addLog);

  const [selectedBody, setSelectedBody] = useState("target");
  const [forceDir, setForceDir] = useState<"x" | "y" | "z">("x");
  const [forceN, setForceN] = useState(150);
  const [payloadKg, setPayloadKg] = useState(5);
  const [loading, setLoading] = useState(false);

  const links = manifest?.links ?? [];

  async function runTest(testId: string, label: string) {
    setLoading(true);
    try {
      if (testId.includes("payload")) setShowPayloadPreview(true);
      const result = await runSelectedTest(projectId, testId);
      const run = await getRunResult(result.run_id);
      setRunResult(run);
      addLog(`[Forces] ${label} → ${result.status}`);
    } catch (error) {
      addLog(`[Forces][Error] ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2 p-2 text-[11px] text-slate-300">
      <div className="text-xs font-semibold text-slate-100">Forces / Loads</div>

      <label className="block">
        <span className="text-slate-500">Body / link</span>
        <select className="mt-0.5 w-full rounded border border-slate-600 bg-[#141c2b] px-2 py-1" value={selectedBody} onChange={(e) => setSelectedBody(e.target.value)}>
          <option value="target">target (box / end effector)</option>
          <option value="robot">robot base</option>
          {links.slice(0, 8).map((l) => (
            <option key={l.id} value={l.id}>
              {l.name ?? l.id}
            </option>
          ))}
        </select>
      </label>

      <div className="grid grid-cols-2 gap-2">
        <label className="block">
          <span className="text-slate-500">Force dir</span>
          <select className="mt-0.5 w-full rounded border border-slate-600 bg-[#141c2b] px-2 py-1" value={forceDir} onChange={(e) => setForceDir(e.target.value as "x" | "y" | "z")}>
            <option value="x">+X lateral</option>
            <option value="y">+Y vertical</option>
            <option value="z">+Z forward</option>
          </select>
        </label>
        <label className="block">
          <span className="text-slate-500">Force (N)</span>
          <input type="number" className="mt-0.5 w-full rounded border border-slate-600 bg-[#141c2b] px-2 py-1" value={forceN} onChange={(e) => setForceN(Number(e.target.value))} />
        </label>
      </div>

      <button type="button" className="w-full rounded bg-orange-600/90 py-1 text-xs text-white hover:bg-orange-500 disabled:opacity-50" disabled={loading} onClick={() => void runTest("lateral_push_topple", "Lateral push topple")}>
        Apply Push / Topple Test
      </button>

      <label className="block">
        <span className="text-slate-500">Payload mass (kg)</span>
        <input type="number" step="0.5" className="mt-0.5 w-full rounded border border-slate-600 bg-[#141c2b] px-2 py-1" value={payloadKg} onChange={(e) => setPayloadKg(Number(e.target.value))} />
      </label>

      <button type="button" className="w-full rounded bg-slate-700 py-1 text-xs hover:bg-slate-600 disabled:opacity-50" disabled={loading} onClick={() => void runTest("payload_failure", "Payload load")}>
        Run Payload Load Test
      </button>

      <button
        type="button"
        className="w-full rounded border border-slate-600 py-1 text-xs hover:bg-slate-700/60"
        onClick={() => {
          const current = useSimStore.getState().showPayloadPreview;
          setShowPayloadPreview(!current);
        }}
      >
        Toggle payload preview in viewport
      </button>
    </div>
  );
}
