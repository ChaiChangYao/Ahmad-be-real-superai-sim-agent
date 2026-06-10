import type { SimulationTestSpec, TestReadinessResult } from "@/lib/agentic/types";
import { testCardStatus } from "@/lib/agentic/types";
import { accent, accentBg, accentHover } from "../buildablesTheme";

const STATUS_LABEL: Record<string, string> = {
  ready: "Ready",
  ready_with_fallback: "Ready with fallback",
  needs_user_choice: "Needs user choice",
  blocked: "Blocked",
};

const STATUS_STYLE: Record<string, string> = {
  ready: "border-emerald-700/50 bg-emerald-950/30",
  ready_with_fallback: "border-amber-700/50 bg-amber-50",
  needs_user_choice: "border-[#FF6A1A]/40 bg-[#FF6A1A]/10",
  blocked: "border-red-200 bg-red-950/25",
};

type Props = {
  tests: TestReadinessResult[];
  specs?: SimulationTestSpec[];
  selectedTestId?: string | null;
  onSelectTest?: (testId: string) => void;
  onConfigure?: (testId: string) => void;
  onUseDefaults?: (testId: string) => void;
};

export function TestRecommendationCards({
  tests,
  specs = [],
  selectedTestId,
  onSelectTest,
  onConfigure,
  onUseDefaults,
}: Props) {
  if (tests.length === 0) return <div className="text-[10px] text-slate-500">No test recommendations yet.</div>;

  return (
    <div className="grid gap-2">
      {tests.map((t) => {
        const spec = specs.find((s) => s.test_id === t.test_id);
        const status = testCardStatus(t);
        const reason = t.blockers[0] ?? t.warnings[0] ?? spec?.description ?? "";
        const selected = selectedTestId === t.test_id;
        return (
          <div
            key={t.test_id}
            className={`rounded border p-2 ${STATUS_STYLE[status]} ${selected ? "ring-1 ring-[#FF6A1A]" : ""}`}
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className={`text-xs font-semibold ${accent}`}>{spec?.display_name ?? t.test_id}</div>
                <div className="text-[9px] text-slate-600">{spec?.category ?? ""}</div>
              </div>
              <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[9px] text-slate-800">
                {STATUS_LABEL[status]}
              </span>
            </div>
            <p className="mt-1 text-[10px] leading-snug text-slate-700">{reason}</p>
            {t.generated_defaults_available.length > 0 ? (
              <p className="mt-1 text-[9px] text-slate-500">
                Defaults: {t.generated_defaults_available.join(", ")}
              </p>
            ) : null}
            {spec?.outputs?.length ? (
              <p className="mt-0.5 text-[9px] text-slate-600">Outputs: {spec.outputs.join(", ")}</p>
            ) : null}
            <div className="mt-2 flex flex-wrap gap-1">
              {status !== "blocked" ? (
                <>
                  <button
                    type="button"
                    data-testid={`test-configure-${t.test_id}`}
                    className={`rounded px-2 py-0.5 text-[9px] font-medium text-white ${accentBg} ${accentHover}`}
                    onClick={() => onConfigure?.(t.test_id)}
                  >
                    Configure
                  </button>
                  {(status === "needs_user_choice" || t.generated_defaults_available.length > 0) && (
                    <button
                      type="button"
                      className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-800 hover:bg-slate-100"
                      onClick={() => onUseDefaults?.(t.test_id)}
                    >
                      Use defaults
                    </button>
                  )}
                </>
              ) : (
                <button
                  type="button"
                  className="rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100"
                  onClick={() => onSelectTest?.(t.test_id)}
                >
                  Show required inputs
                </button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
