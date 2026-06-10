"use client";

import { useState } from "react";
import type { AgentTimelineStep } from "@/lib/agentic/types";
import { accent } from "../buildablesTheme";

const STATUS_ICON: Record<string, string> = {
  pending: "○",
  running: "◐",
  done: "✓",
  failed: "✗",
  skipped: "—",
};

type Props = {
  steps: AgentTimelineStep[];
  headline?: string;
};

export function AgentTimelineCard({ steps, headline = "Agent progress" }: Props) {
  const [expanded, setExpanded] = useState(false);
  const failed = steps.find((s) => s.status === "failed");

  return (
    <div
      data-testid="agent-timeline"
      className="mr-4 rounded border border-slate-200/80 bg-white p-2 text-[10px] text-slate-700"
    >
      <div className={`mb-2 font-semibold ${accent}`}>{headline}</div>
      <ul className="space-y-1">
        {steps.map((step) => (
          <li
            key={step.step_id}
            data-testid={`agent-timeline-step-${step.step_id}`}
            className={
              step.status === "failed"
                ? "text-red-700"
                : step.status === "done"
                  ? "text-emerald-400/90"
                  : step.status === "running"
                    ? "text-amber-800"
                    : "text-slate-500"
            }
          >
            <span data-testid={`agent-timeline-step-status-${step.step_id}`} className="mr-1.5 inline-block w-3">
              {STATUS_ICON[step.status] ?? "○"}
            </span>
            <span className="font-medium">{step.label}</span>
            {step.detail ? <span className="ml-1 text-slate-500">— {step.detail}</span> : null}
            {step.error && step.status === "failed" ? (
              <div className="ml-4 mt-0.5 text-red-200/90">{step.error}</div>
            ) : null}
          </li>
        ))}
      </ul>
      {(failed?.error || steps.some((s) => s.detail && s.status === "failed")) && (
        <button
          type="button"
          className="mt-2 text-[9px] text-slate-500 underline hover:text-slate-700"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Hide technical details" : "Show technical details"}
        </button>
      )}
      {expanded ? (
        <pre className="mt-2 max-h-32 overflow-auto rounded bg-white/80 p-2 text-[9px] text-slate-600">
          {JSON.stringify(steps, null, 2)}
        </pre>
      ) : null}
    </div>
  );
}
