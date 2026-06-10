"use client";

import { frameCount } from "@/lib/playback";
import { useSimStore } from "@/lib/state";
import { TimelinePlayback } from "./TimelinePlayback";

export function TestResultsPanel({ compact = false }: { compact?: boolean }) {
  const lastRun = useSimStore((s) => s.lastRun);
  const manifest = useSimStore((s) => s.manifest);
  const lastRunManifestVersion = useSimStore((s) => s.lastRunManifestVersion);
  const runTimeseries = useSimStore((s) => s.runTimeseries);
  const changedSinceRun = manifest && lastRunManifestVersion !== null && manifest.version !== lastRunManifestVersion;
  const frames = frameCount(runTimeseries);

  return (
    <section className={`h-full p-2 ${compact ? "" : "panel"}`}>
      <h3 className="mb-1 text-sm font-semibold">Test Results</h3>
      {!lastRun ? (
        <div className="text-sm text-textMuted">No run yet.</div>
      ) : (
        <div className="space-y-2 text-sm">
          <div className="space-y-1">
            <div>
              Status: <strong>{lastRun.status.toUpperCase()}</strong>
            </div>
            <div>Scenario: {lastRun.scenario_id}</div>
            <div>Run ID: {lastRun.run_id}</div>
            <div>Genesis: {lastRun.genesis_used ? "yes" : "no"} · Mocked: {lastRun.mocked ? "yes" : "no"}</div>
            <div>Steps: {lastRun.step_count}</div>
            <div>Simulation used manifest version: {lastRun.manifest_version_used}</div>
            {changedSinceRun ? <div className="text-amber-700">Current manifest has changed since last run.</div> : null}
          </div>
          {frames > 0 ? (
            <div className="border-t border-border pt-2 text-xs">
              <div className="mb-1 font-medium">Playback ({frames} frames)</div>
              <TimelinePlayback />
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
}
