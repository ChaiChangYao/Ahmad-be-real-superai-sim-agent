"use client";

import { useState } from "react";
import type { CodeGenResult, GeneratedScriptDetail } from "@/lib/agentic/types";
import { accent, accentBg } from "../buildablesTheme";
import { useModalDismiss } from "../useModalDismiss";

type Props = {
  open: boolean;
  result: CodeGenResult | null;
  detail: GeneratedScriptDetail | null;
  onClose: () => void;
  onRun?: () => void;
  runDisabled?: boolean;
};

type Tab = "script" | "context" | "validation";

export function GeneratedScriptViewer({ open, result, detail, onClose, onRun, runDisabled }: Props) {
  const [tab, setTab] = useState<Tab>("script");
  useModalDismiss(open, onClose);

  if (!open || !result) return null;

  const validation = detail?.validation ?? result.validation;
  const copyText =
    tab === "script"
      ? detail?.source ?? ""
      : tab === "context"
        ? JSON.stringify(detail?.context ?? result.context ?? {}, null, 2)
        : JSON.stringify(validation, null, 2);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" onClick={onClose} role="presentation">
      <div
        data-testid="generated-script-viewer"
        className="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-lg border border-slate-300 bg-slate-50 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
          <div>
            <div className={`text-sm font-semibold ${accent}`}>Generated Script</div>
            <div className="text-[10px] text-slate-500">
              {result.template_id} · {result.script_id}
              {result.success ? " · valid" : " · blocked"}
            </div>
          </div>
          <button
            type="button"
            data-testid="generated-script-close"
            className="rounded border border-slate-300 px-2 py-0.5 text-[10px] text-slate-700 hover:bg-slate-100"
            onClick={onClose}
          >
            Close
          </button>
        </div>

        <div className="border-b border-slate-200 px-4 py-2 text-[10px] text-slate-700">
          <p>{result.explanation}</p>
          {result.expected_outputs.length > 0 && (
            <p className="mt-1 text-slate-500">Outputs: {result.expected_outputs.join(", ")}</p>
          )}
          {validation.warnings?.map((w) => (
            <p key={w} className="mt-0.5 text-amber-400">
              {w}
            </p>
          ))}
          {validation.errors?.map((e) => (
            <p key={e} className="mt-0.5 text-red-400">
              {e}
            </p>
          ))}
        </div>

        <div className="flex gap-1 border-b border-slate-200 px-4 py-1">
          {(["script", "context", "validation"] as Tab[]).map((t) => (
            <button
              key={t}
              type="button"
              className={`rounded px-2 py-0.5 text-[9px] capitalize ${
                tab === t ? "bg-slate-200 text-slate-900" : "text-slate-600 hover:bg-slate-100"
              }`}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
          <button
            type="button"
            className="ml-auto rounded border border-slate-300 px-2 py-0.5 text-[9px] text-slate-700 hover:bg-slate-100"
            onClick={() => void navigator.clipboard.writeText(copyText)}
          >
            Copy
          </button>
        </div>

        <pre data-testid="generated-script-source" className="min-h-0 flex-1 overflow-auto p-4 text-[10px] leading-relaxed text-slate-700">
          {tab === "script" && (detail?.source ?? "Loading script…")}
          {tab === "context" && JSON.stringify(detail?.context ?? result.context ?? {}, null, 2)}
          {tab === "validation" && JSON.stringify(validation, null, 2)}
        </pre>

        <div className="flex items-center justify-between border-t border-slate-200 px-4 py-2">
          <span className="text-[9px] text-slate-500">Inspect generated code before executing.</span>
          {result.success && onRun ? (
            <button
              type="button"
              disabled={runDisabled}
              className={`rounded px-2 py-0.5 text-[9px] font-medium text-white ${accentBg} disabled:opacity-40`}
              onClick={onRun}
            >
              Run Simulation
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
