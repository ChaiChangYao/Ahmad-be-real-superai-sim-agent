"use client";

import type { EngineeringReport } from "@/lib/agentic/types";
import { useModalDismiss } from "../useModalDismiss";
import { EngineeringReportPanel } from "./EngineeringReportPanel";

type Props = {
  open: boolean;
  report: EngineeringReport | null;
  onClose: () => void;
  onCopyJson?: () => void;
  onDownloadMd?: () => void;
};

export function EngineeringReportModal({ open, report, onClose, onCopyJson, onDownloadMd }: Props) {
  useModalDismiss(open, onClose);
  if (!open || !report) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" onClick={onClose} role="presentation">
      <div
        className="flex max-h-[85vh] w-full max-w-2xl flex-col rounded-lg border border-slate-300 bg-slate-50 shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2">
          <h2 className="text-sm font-semibold text-slate-900">Engineering report — {report.test_name}</h2>
          <div className="flex gap-2">
            {onCopyJson ? (
              <button type="button" className="text-[10px] text-slate-600 hover:text-slate-900" onClick={onCopyJson}>
                Copy JSON
              </button>
            ) : null}
            {onDownloadMd ? (
              <button type="button" className="text-[10px] text-slate-600 hover:text-slate-900" onClick={onDownloadMd}>
                Download MD
              </button>
            ) : null}
            <button type="button" className="text-[10px] text-slate-600 hover:text-slate-900" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 overflow-hidden">
          <EngineeringReportPanel report={report} />
        </div>
      </div>
    </div>
  );
}
