import type { EngineeringReport } from "@/lib/agentic/types";
import { accent } from "../buildablesTheme";

const OUTCOME_STYLES: Record<string, string> = {
  passed: "border-emerald-700/50 bg-emerald-950/30 text-emerald-200",
  warning: "border-amber-700/50 bg-amber-50 text-amber-800",
  failed: "border-red-300/50 bg-red-50 text-red-200",
  blocked: "border-red-300/50 bg-red-50 text-red-200",
  inconclusive: "border-slate-300 bg-slate-50 text-slate-700",
  readiness_only: "border-slate-300 bg-slate-50 text-slate-700",
};

type Props = {
  report: EngineeringReport;
  onViewFull?: () => void;
  onCopy?: () => void;
  onDownload?: () => void;
};

export function EngineeringReportCard({ report, onViewFull, onCopy, onDownload }: Props) {
  const outcomeClass = OUTCOME_STYLES[report.outcome.status] ?? OUTCOME_STYLES.inconclusive;
  return (
    <div className="rounded border border-slate-200 bg-slate-100 p-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className={`text-xs font-semibold ${accent}`}>Engineering report</div>
          <div className="text-[9px] text-slate-500">
            {report.test_name || report.test_id} · {report.run_id}
          </div>
        </div>
        <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium border ${outcomeClass}`}>
          {report.outcome.label || report.outcome.status}
        </span>
      </div>
      <p className="mt-2 text-[10px] leading-relaxed text-slate-700">{report.executive_summary}</p>
      {report.key_metrics.length > 0 ? (
        <div className="mt-2 grid grid-cols-2 gap-1 text-[9px] text-slate-600">
          {report.key_metrics.slice(0, 6).map((m) => (
            <span key={m.id}>
              {m.label}: <span className="text-slate-800">{String(m.value)}</span>
            </span>
          ))}
        </div>
      ) : null}
      <div className="mt-2 flex flex-wrap gap-1">
        {onViewFull ? (
          <button
            type="button"
            className="rounded bg-[#FF6A1A] px-2 py-0.5 text-[9px] text-white hover:bg-[#e55f15]"
            onClick={onViewFull}
          >
            View full report
          </button>
        ) : null}
        {onCopy ? (
          <button type="button" className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100" onClick={onCopy}>
            Copy summary
          </button>
        ) : null}
        {onDownload ? (
          <button type="button" className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100" onClick={onDownload}>
            Download MD
          </button>
        ) : null}
      </div>
    </div>
  );
}
