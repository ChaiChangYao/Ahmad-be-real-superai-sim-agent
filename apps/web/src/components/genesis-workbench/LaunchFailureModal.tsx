"use client";

import { useState } from "react";
import { accent, accentBg, accentHover } from "./buildablesTheme";
import { useModalDismiss } from "./useModalDismiss";

export type LaunchFailureInfo = {
  title: string;
  scriptPath?: string | null;
  failureCode?: string | null;
  failureDetail?: string | null;
  suggestedFix?: string | null;
  logs?: string;
};

type Props = {
  open: boolean;
  failure: LaunchFailureInfo | null;
  onClose: () => void;
};

export function LaunchFailureModal({ open, failure, onClose }: Props) {
  const [copied, setCopied] = useState(false);
  useModalDismiss(open, onClose);
  if (!open || !failure) return null;

  async function copyLogs() {
    const text = [
      failure?.title,
      failure?.scriptPath ? `Script: ${failure.scriptPath}` : "",
      failure?.failureCode ? `Code: ${failure.failureCode}` : "",
      failure?.failureDetail ?? "",
      failure?.suggestedFix ? `Suggested fix: ${failure.suggestedFix}` : "",
      failure?.logs ?? "",
    ]
      .filter(Boolean)
      .join("\n\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose} role="presentation">
      <div
        data-testid="launch-failure-modal"
        className="max-h-[85vh] w-full max-w-lg overflow-auto rounded-lg border border-slate-300 bg-white p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className={`text-sm font-semibold ${accent}`}>{failure.title}</h2>
          <button type="button" className="text-slate-600 hover:text-slate-900" onClick={onClose}>
            Close
          </button>
        </div>
        {failure.scriptPath ? (
          <p className="mb-2 break-all text-[11px] text-slate-600">{failure.scriptPath}</p>
        ) : null}
        {failure.failureCode ? (
          <p className="mb-2 text-xs text-slate-700">
            Error type: <span className="font-mono">{failure.failureCode}</span>
          </p>
        ) : null}
        {failure.failureDetail ? (
          <pre className="mb-3 max-h-40 overflow-auto rounded border border-slate-200 bg-slate-200 p-2 text-[11px] text-red-200 whitespace-pre-wrap">
            {failure.failureDetail}
          </pre>
        ) : null}
        {failure.suggestedFix ? (
          <p className="mb-3 text-xs text-slate-800">
            <span className="font-medium text-slate-900">Suggested fix: </span>
            {failure.suggestedFix}
          </p>
        ) : null}
        {failure.logs ? (
          <pre className="mb-3 max-h-48 overflow-auto rounded border border-slate-200 bg-black/40 p-2 text-[10px] text-slate-700 whitespace-pre-wrap">
            {failure.logs}
          </pre>
        ) : null}
        <div className="flex gap-2">
          <button
            type="button"
            data-testid="failure-copy-logs"
            className={`rounded px-3 py-1.5 text-xs font-medium text-white ${accentBg} ${accentHover}`}
            onClick={() => void copyLogs()}
          >
            {copied ? "Copied" : "Copy logs"}
          </button>
          <button
            type="button"
            data-testid="failure-dismiss"
            className="rounded border border-slate-300 px-3 py-1.5 text-xs text-slate-800 hover:bg-slate-100"
            onClick={onClose}
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
