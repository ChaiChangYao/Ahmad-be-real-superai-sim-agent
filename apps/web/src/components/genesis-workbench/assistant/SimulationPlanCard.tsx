import type { SimulationPlan } from "@/lib/agentic/types";
import { accent } from "../buildablesTheme";

type Props = {
  plan: SimulationPlan;
};

export function SimulationPlanCard({ plan }: Props) {
  return (
    <div className="mr-4 rounded border border-slate-200 bg-slate-50 p-2">
      <div className={`text-[10px] font-semibold ${accent}`}>Simulation plan</div>
      {plan.agent_explanation ? (
        <p className="mt-1 whitespace-pre-wrap text-[10px] leading-relaxed text-slate-700">{plan.agent_explanation}</p>
      ) : null}
      {plan.plan_steps.length > 0 ? (
        <ol className="mt-2 list-inside list-decimal space-y-0.5 text-[9px] text-slate-600">
          {plan.plan_steps.map((step, i) => (
            <li key={`${i}-${step.slice(0, 24)}`}>{step}</li>
          ))}
        </ol>
      ) : null}
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-0.5 text-[9px] text-slate-500">
        <span>Recommended: {plan.recommended_tests.length}</span>
        <span>Blocked: {plan.blocked_tests.length}</span>
        {plan.generation_tasks.length > 0 ? (
          <span className="col-span-2">Tasks: {plan.generation_tasks.join(", ")}</span>
        ) : null}
      </div>
    </div>
  );
}
