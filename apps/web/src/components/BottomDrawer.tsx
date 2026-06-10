"use client";

import { useState } from "react";
import { useSimStore } from "@/lib/state";
import { MetricsPanel } from "./MetricsPanel";
import { TerminalLogs } from "./TerminalLogs";
import { TestResultsPanel } from "./TestResultsPanel";
import { TimelinePlayback } from "./TimelinePlayback";

type TabKey = "terminal" | "test-results" | "metrics" | "timeline" | "sensor-output" | "render-output" | "artifacts";

const TABS: { key: TabKey; label: string }[] = [
  { key: "terminal", label: "Terminal" },
  { key: "test-results", label: "Results" },
  { key: "metrics", label: "Metrics" },
  { key: "timeline", label: "Timeline" },
  { key: "sensor-output", label: "Sensors" },
  { key: "render-output", label: "Render" },
  { key: "artifacts", label: "Artifacts" },
];

const tabBtn = (active: boolean) =>
  `rounded px-1.5 py-0.5 text-[10px] ${
    active ? "bg-accent text-white" : "text-textMuted hover:bg-slate-100 hover:text-textMain"
  }`;

export function BottomDrawer() {
  const [activeTab, setActiveTab] = useState<TabKey>("terminal");
  const lastRun = useSimStore((s) => s.lastRun);
  const manifest = useSimStore((s) => s.manifest);
  const remoteControlEnabled = (manifest?.project_type ?? "generic") === "robot_dog";

  return (
    <div className="flex h-full min-h-0 flex-col bg-white">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-2 py-1">
        <div className="flex flex-wrap gap-0.5">
          {TABS.map((tab) => (
            <button key={tab.key} type="button" onClick={() => setActiveTab(tab.key)} className={tabBtn(activeTab === tab.key)}>
              {tab.label}
            </button>
          ))}
        </div>
        <span className="text-[10px] text-textMuted">Drag top edge to resize · double-click to collapse</span>
      </div>

      <div className="min-h-0 flex-1 overflow-hidden">
        {activeTab === "terminal" ? (
          <div className="flex h-full flex-col">
            {remoteControlEnabled ? (
              <div className="shrink-0 border-b border-border px-2 py-1 text-[10px] text-textMuted">
                WASD move · Space jump · R reset · Esc stop
              </div>
            ) : null}
            <TerminalLogs compact />
          </div>
        ) : null}
        {activeTab === "test-results" ? <TestResultsPanel compact /> : null}
        {activeTab === "metrics" ? <MetricsPanel compact /> : null}
        {activeTab === "timeline" ? (
          <div className="h-full overflow-auto p-2 text-[11px] text-textMuted">
            <TimelinePlayback />
          </div>
        ) : null}
        {activeTab === "sensor-output" ? (
          <pre className="h-full overflow-auto p-2 text-[10px] text-textMuted">{lastRun ? JSON.stringify(lastRun.metrics, null, 2) : "No sensor output."}</pre>
        ) : null}
        {activeTab === "render-output" ? (
          <pre className="h-full overflow-auto p-2 text-[10px] text-textMuted">{lastRun ? JSON.stringify(lastRun.artifacts, null, 2) : "No render output."}</pre>
        ) : null}
        {activeTab === "artifacts" ? (
          <div className="h-full overflow-auto p-2 text-[11px] text-textMuted">
            {!lastRun ? "No artifacts." : Object.entries(lastRun.artifacts).map(([k, v]) => <div key={k}>{k}: {String(v)}</div>)}
          </div>
        ) : null}
      </div>
    </div>
  );
}
