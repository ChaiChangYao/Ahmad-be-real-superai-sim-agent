import type { ExecutionRun } from "@/lib/agentic/types";
import { accent, accentBg, accentHover } from "../buildablesTheme";

type Props = {
  run: ExecutionRun | null;
  logTail?: string;
  onCancel?: () => void;
  cancelling?: boolean;
};

const STATUS_LABEL: Record<string, string> = {
  queued: "Queued",
  preparing: "Preparing",
  validating: "Validating",
  running: "Running",
  recording: "Recording",
  completed: "Completed",
  failed: "Failed",
  cancelled: "Cancelled",
  timed_out: "Timed out",
};

export function RunExecutionCard({ run, logTail, onCancel, cancelling }: Props) {
  if (!run) return null;
  const active = ["queued", "preparing", "validating", "running", "recording"].includes(run.status);
  return (
    <div data-testid="run-execution-card" className="rounded border border-slate-200 bg-slate-100 p-2">
      <div className="flex items-center justify-between gap-2">
        <div>
          <div className={`text-xs font-semibold ${accent}`}>Agentic run</div>
          <div className="text-[9px] text-slate-500">
            {run.run_id} · {run.backend} · {STATUS_LABEL[run.status] ?? run.status}
          </div>
        </div>
        {active && onCancel ? (
          <button
            type="button"
            disabled={cancelling}
            className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100 disabled:opacity-40"
            onClick={onCancel}
          >
            {cancelling ? "Cancelling…" : "Cancel"}
          </button>
        ) : null}
      </div>
      {logTail ? (
        <pre className="mt-2 max-h-24 overflow-auto rounded bg-slate-200 p-1.5 text-[9px] text-slate-600 whitespace-pre-wrap">
          {logTail}
        </pre>
      ) : null}
    </div>
  );
}

export function RunLogPanel({
  logs,
  onCopy,
  onDownload,
  onClearView,
}: {
  logs: string;
  onCopy?: () => void;
  onDownload?: () => void;
  onClearView?: () => void;
}) {
  return (
    <div data-testid="run-log-panel" className="rounded border border-slate-200 bg-white/80 p-2">
      <div className="mb-1 flex items-center justify-between">
        <span className="text-[9px] font-medium text-slate-600">Run logs</span>
        <div className="flex gap-1">
          {onCopy ? (
            <button type="button" data-testid="run-log-copy" className="text-[9px] text-slate-500 hover:text-slate-700" onClick={onCopy}>
              Copy
            </button>
          ) : null}
          {onDownload ? (
            <button type="button" className="text-[9px] text-slate-500 hover:text-slate-700" onClick={onDownload}>
              Download
            </button>
          ) : null}
          {onClearView ? (
            <button type="button" className="text-[9px] text-slate-500 hover:text-slate-700" onClick={onClearView}>
              Clear view
            </button>
          ) : null}
        </div>
      </div>
      <pre className="max-h-48 overflow-auto text-[9px] leading-relaxed text-slate-600 whitespace-pre-wrap">{logs}</pre>
    </div>
  );
}
