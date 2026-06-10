"use client";

import { useSimStore } from "@/lib/state";

export function MetricsPanel({ compact = false }: { compact?: boolean }) {
  const metrics = useSimStore((s) => s.metrics);
  const entries = Object.entries(metrics);
  return (
    <section className={`h-full p-2 ${compact ? "" : "panel"}`}>
      <h3 className="mb-1 text-sm font-semibold">Metrics</h3>
      {entries.length === 0 ? (
        <div className="text-sm text-textMuted">No metrics yet.</div>
      ) : (
        <div className="grid grid-cols-2 gap-1 text-xs">
          {entries.map(([k, v]) => (
            <div key={k} className="rounded border border-border bg-white px-2 py-1">
              <div className="font-medium">{k}</div>
              <div>{typeof v === "object" ? JSON.stringify(v) : String(v)}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
