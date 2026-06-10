import type { AgentActionCard } from "@/lib/agentic/types";
import { accentBg, accentHover } from "../buildablesTheme";

type Props = {
  actions: AgentActionCard[];
  onAction: (actionId: string, actionTitle: string) => void;
  busy?: boolean;
  hideStepPreview?: boolean;
};

export function RecoveryActions({ actions, onAction, busy, hideStepPreview }: Props) {
  const visible = hideStepPreview
    ? actions.filter((a) => a.actionId !== "recover_step_preview")
    : actions;

  return (
    <div className="flex flex-wrap gap-1.5">
      {visible.map((a) => {
        const disabled = a.disabled || busy;
        const cls =
          a.variant === "primary" && !disabled
            ? `${accentBg} ${accentHover} text-white`
            : a.variant === "disabled" || disabled
              ? "border-slate-200 text-slate-600 cursor-not-allowed"
              : "border-slate-300 text-slate-800 hover:bg-slate-100";
        return (
          <button
            key={a.id}
            type="button"
            disabled={disabled}
            title={a.disabledReason ?? a.description}
            className={`rounded border px-2 py-1 text-[9px] font-medium transition ${cls}`}
            onClick={() => onAction(a.actionId, a.title)}
          >
            {a.title}
          </button>
        );
      })}
    </div>
  );
}
