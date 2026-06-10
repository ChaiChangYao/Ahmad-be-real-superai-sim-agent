"use client";

import { useEffect, useState } from "react";
import { applyJointTargets, getProjectDofs } from "@/lib/api";
import { useSimStore } from "@/lib/state";

type DofInfo = {
  index: number;
  joint_id: string;
  position: number;
  lower_limit: number;
  upper_limit: number;
};

type JointApplyResult = {
  genesis_used?: boolean;
  mocked?: boolean;
  step_count?: number;
  reached?: number[];
  state_timeseries?: Array<Record<string, unknown>>;
};

export function JointControlsPanel() {
  const projectId = useSimStore((s) => s.selectedProjectId);
  const setRunResult = useSimStore((s) => s.setRunResult);
  const setRunTimeseries = useSimStore((s) => s.setRunTimeseries);
  const addLog = useSimStore((s) => s.addLog);
  const [dofs, setDofs] = useState<DofInfo[]>([]);
  const [targets, setTargets] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    void (async () => {
      try {
        const data = await getProjectDofs(projectId);
        const list = (data.dofs as DofInfo[]) ?? [];
        setDofs(list);
        setTargets(list.map((d) => d.position));
      } catch (error) {
        addLog(`[DOFs] Load failed: ${(error as Error).message}`);
      }
    })();
  }, [projectId, addLog]);

  async function onApplyAll() {
    setLoading(true);
    try {
      const result = (await applyJointTargets(projectId, targets, 90)) as JointApplyResult;
      if (result.state_timeseries) {
        setRunTimeseries(result.state_timeseries as Array<Record<string, unknown>>);
      }
      setRunResult({
        run_id: `joint-${Date.now()}`,
        project_id: projectId,
        scenario_id: "joint_command",
        status: "pass",
        genesis_used: Boolean(result.genesis_used),
        mocked: Boolean(result.mocked),
        manifest_version_used: 0,
        step_count: Number(result.step_count ?? 0),
        started_at: new Date().toISOString(),
        ended_at: new Date().toISOString(),
        duration_s: 0,
        metrics: { joint_target_error: Object.fromEntries(dofs.map((d, i) => [d.joint_id, Math.abs((result.reached?.[i] ?? 0) - targets[i])])) },
        events: [],
        logs: ["[Genesis] Joint targets applied."],
        state_timeseries: (result.state_timeseries as Array<Record<string, unknown>>) ?? [],
        artifacts: {},
      });
      addLog(`[Genesis] Joint command stepped=${result.step_count} reached=${JSON.stringify(result.reached)}`);
    } catch (error) {
      addLog(`[DOFs] Apply failed: ${(error as Error).message}`);
    } finally {
      setLoading(false);
    }
  }

  if (dofs.length === 0) {
    return <div className="rounded border border-slate-200 bg-slate-50 p-2 text-[11px] text-slate-500">No controllable DOFs for this project.</div>;
  }

  return (
    <div className="space-y-2">
      {dofs.map((dof, idx) => (
        <label key={dof.joint_id} className="block rounded border border-slate-200 bg-slate-50 p-2">
          <div className="mb-1 flex justify-between text-[10px]">
            <span className="font-medium text-slate-800">{dof.joint_id}</span>
            <span className="text-slate-600">{targets[idx]?.toFixed(3) ?? "0.000"} rad</span>
          </div>
          <input
            type="range"
            min={dof.lower_limit}
            max={dof.upper_limit}
            step={0.01}
            value={targets[idx] ?? 0}
            onChange={(e) => {
              const next = [...targets];
              next[idx] = Number(e.target.value);
              setTargets(next);
            }}
            className="w-full"
          />
        </label>
      ))}
      <button type="button" className="w-full rounded bg-sky-600 px-2 py-1 text-[11px] text-white hover:bg-sky-500 disabled:opacity-50" disabled={loading} onClick={onApplyAll}>
        Apply Targets (Genesis)
      </button>
      <button
        type="button"
        className="w-full rounded border border-slate-300 py-1 text-[10px] text-slate-600 hover:bg-slate-200/50"
        onClick={() => setTargets(dofs.map((d) => d.position))}
      >
        Reset to current
      </button>
    </div>
  );
}
