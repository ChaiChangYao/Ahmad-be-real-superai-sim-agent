"use client";

import { useMemo } from "react";
import { getRunResult, runSelectedTest, runTestSuite } from "@/lib/api";
import { useSimStore } from "@/lib/state";

export function GenesisTestLab() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const tests = useSimStore((s) => s.availableTests);
  const genesisCatalog = useSimStore((s) => s.genesisCatalog);
  const selectedTestId = useSimStore((s) => s.selectedTestId);
  const setSelectedTestId = useSimStore((s) => s.setSelectedTestId);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const addLog = useSimStore((s) => s.addLog);

  const grouped = useMemo(() => {
    const map = new Map<string, typeof tests>();
    for (const test of tests) {
      const arr = map.get(test.category) ?? [];
      arr.push(test);
      map.set(test.category, arr);
    }
    return [...map.entries()];
  }, [tests]);

  async function onRunSelected() {
    if (!selectedTestId) return;
    try {
      const result = await runSelectedTest(projectId, selectedTestId);
      addLog(`[TestLab] ${result.test_name}: ${result.status}`);
      const maybeRun = useSimStore.getState().lastRun;
      if (maybeRun && maybeRun.run_id === result.run_id) return;
      const fullRun = await getRunResult(result.run_id);
      setRunResult(fullRun);
    } catch (error) {
      addLog(`[TestLab][Error] ${(error as Error).message}`);
    }
  }

  async function onRunSuite() {
    try {
      const suite = await runTestSuite(projectId);
      addLog(`[TestLab] Suite ${suite.suite_run_id} pass_rate=${suite.summary.suite_pass_rate ?? "n/a"}%`);
    } catch (error) {
      addLog(`[TestLab][Error] ${(error as Error).message}`);
    }
  }

  return (
    <div className="panel h-full overflow-auto p-2">
      <div className="mb-2 flex items-center justify-between">
        <div className="text-sm font-semibold">Genesis Test Lab</div>
        <div className="flex gap-1">
          <button className="rounded border border-border bg-white px-2 py-1 text-xs" onClick={onRunSelected} disabled={!selectedTestId}>
            Run Selected Test
          </button>
          <button className="rounded border border-border bg-white px-2 py-1 text-xs" onClick={onRunSuite}>
            Run Test Suite
          </button>
        </div>
      </div>
      <div className="space-y-2">
        {genesisCatalog ? (
          <section className="rounded border border-slate-300 bg-slate-50 p-2 text-xs">
            <div className="font-semibold">Genesis Capability Snapshot</div>
            <div>Physics implemented: {genesisCatalog.physics_capabilities.buildables_implemented.join(", ")}</div>
            <div>Not implemented yet: {genesisCatalog.physics_capabilities.not_yet_implemented.join(", ")}</div>
          </section>
        ) : null}
        {grouped.map(([category, items]) => (
          <section key={category} className="rounded border border-border bg-white p-2">
            <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-600">{category}</div>
            <div className="space-y-1">
              {items.map((test) => (
                <button
                  key={test.id}
                  onClick={() => setSelectedTestId(test.id)}
                  className={`w-full rounded border px-2 py-1 text-left text-xs ${selectedTestId === test.id ? "border-sky-400 bg-sky-50" : "border-slate-200 bg-white"}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{test.name}</span>
                    <span className={`rounded px-1.5 py-0.5 text-[10px] ${test.status === "available" ? "bg-emerald-100 text-emerald-700" : test.status === "not_applicable" ? "bg-slate-200 text-slate-700" : "bg-amber-100 text-amber-800"}`}>{test.status}</span>
                  </div>
                  <div className="text-[11px] text-slate-600">{test.description}</div>
                  {test.reasons && test.reasons.length > 0 ? <div className="text-[10px] text-amber-700">Reason: {test.reasons.join("; ")}</div> : null}
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}
