"use client";

import { useSimStore } from "@/lib/state";

export function TerminalLogs({ compact = false }: { compact?: boolean }) {
  const logs = useSimStore((s) => s.logs);
  return (
    <section className={`h-full p-2 ${compact ? "" : "panel"}`}>
      <h3 className="mb-1 text-sm font-semibold">Terminal Logs</h3>
      <div className="h-[78px] overflow-auto rounded border border-slate-200 bg-slate-50 p-2 font-mono text-xs text-slate-700">
        {logs.length === 0 ? <div>[Genesis] Waiting for run...</div> : logs.map((line, idx) => <div key={`${line}-${idx}`}>{line}</div>)}
      </div>
    </section>
  );
}
