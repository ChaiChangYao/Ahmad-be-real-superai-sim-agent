import type { EngineeringReport } from "@/lib/agentic/types";
import { accent } from "../buildablesTheme";

type Props = {
  report: EngineeringReport | null;
  onClose?: () => void;
};

export function EngineeringReportPanel({ report, onClose }: Props) {
  if (!report) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-center text-[10px] text-slate-500">
        Run a simulation to generate an engineering report.
      </div>
    );
  }

  return (
    <div data-testid="engineering-report-panel" className="flex h-full min-h-0 flex-col rounded border border-slate-200 bg-slate-100">
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2">
        <span className={`text-xs font-medium ${accent}`}>Engineering report</span>
        {onClose ? (
          <button type="button" className="text-[9px] text-slate-500 hover:text-slate-700" onClick={onClose}>
            Close
          </button>
        ) : null}
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3 text-[10px] text-slate-700">
        <section>
          <div className="font-semibold text-slate-800">Outcome</div>
          <p>
            {report.outcome.label} ({report.outcome.status}) — {report.outcome.summary}
          </p>
        </section>
        {report.detected_issues.length > 0 ? (
          <section>
            <div className="font-semibold text-slate-800">Issues</div>
            <ul className="list-disc pl-4 space-y-1">
              {report.detected_issues.map((i) => (
                <li key={i.issue_id}>
                  <span className="text-slate-800">{i.title}</span> — {i.explanation}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
        {report.limitations.length > 0 ? (
          <section>
            <div className="font-semibold text-slate-800">Limitations</div>
            <ul className="list-disc pl-4 space-y-1">
              {report.limitations.map((l) => (
                <li key={l.limitation_id}>{l.text}</li>
              ))}
            </ul>
          </section>
        ) : null}
        {report.recommendations.length > 0 ? (
          <section>
            <div className="font-semibold text-slate-800">Recommendations</div>
            <ul className="list-disc pl-4 space-y-1">
              {report.recommendations.map((r) => (
                <li key={r.recommendation_id}>
                  <span className="text-slate-800">{r.title}</span> — {r.description}
                </li>
              ))}
            </ul>
          </section>
        ) : null}
        {report.next_tests.length > 0 ? (
          <section>
            <div className="font-semibold text-slate-800">Next tests</div>
            <p>{report.next_tests.join(", ")}</p>
          </section>
        ) : null}
        {report.disclaimer ? (
          <section className="text-[9px] text-slate-500">
            <div className="font-semibold">Disclaimer</div>
            <p>{report.disclaimer}</p>
          </section>
        ) : null}
      </div>
    </div>
  );
}
