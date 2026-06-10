"use client";

import type { AgenticErrorDetail } from "@/lib/agentic/types";
import { useModalDismiss } from "../useModalDismiss";

type Props = {
  open: boolean;
  error: AgenticErrorDetail | null;
  onClose: () => void;
};

export function AssistantErrorModal({ open, error, onClose }: Props) {
  useModalDismiss(open, onClose);
  if (!open || !error) return null;

  function copyDetails() {
    void navigator.clipboard.writeText(error?.copyable_debug_details ?? error?.explanation ?? "");
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose} role="presentation">
      <div
        className="max-h-[80vh] w-full max-w-md overflow-auto rounded-lg border border-red-200/60 bg-white p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <h3 className="text-sm font-semibold text-red-200">{error.title}</h3>
        <p className="mt-2 text-xs leading-relaxed text-slate-800">{error.explanation}</p>
        {error.affected_files.length > 0 ? (
          <ul className="mt-2 list-inside list-disc text-[10px] text-slate-600">
            {error.affected_files.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        ) : null}
        {error.suggested_actions.length > 0 ? (
          <div className="mt-3">
            <div className="text-[10px] font-semibold text-[#c2410c]">Suggested fixes</div>
            <ul className="mt-1 list-inside list-decimal text-[10px] text-slate-700">
              {error.suggested_actions.map((a) => (
                <li key={a}>{a}</li>
              ))}
            </ul>
          </div>
        ) : null}
        <div className="mt-4 flex gap-2">
          <button
            type="button"
            className="rounded border border-slate-300 px-3 py-1 text-xs text-slate-800 hover:bg-slate-100"
            onClick={copyDetails}
          >
            Copy details
          </button>
          <button
            type="button"
            className="rounded bg-[#FF6A1A] px-3 py-1 text-xs font-medium text-white hover:bg-[#e55f15]"
            onClick={onClose}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
