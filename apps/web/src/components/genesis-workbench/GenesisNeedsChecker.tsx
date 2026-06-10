"use client";

import type { UploadRequirements } from "@/lib/genesisWorkbenchApi";
import { useModalDismiss } from "./useModalDismiss";

type Props = {
  open: boolean;
  loading: boolean;
  data: UploadRequirements | null;
  onClose: () => void;
};

function statusColor(status: string) {
  if (status === "ok") return "text-[#FF6A1A]";
  if (status === "missing") return "text-rose-400";
  if (status === "warning") return "text-amber-400";
  if (status === "optional") return "text-violet-300";
  return "text-slate-600";
}

export function GenesisNeedsChecker({ open, loading, data, onClose }: Props) {
  useModalDismiss(open, onClose);
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-auto rounded-lg border border-slate-300 bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
      >
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div>
            <h2 className="text-sm font-semibold text-white">{data?.title ?? "What do I need?"}</h2>
            {data?.summary ? <p className="mt-0.5 text-[11px] text-slate-600">{data.summary}</p> : null}
          </div>
          <button type="button" className="text-slate-600 hover:text-slate-900" onClick={onClose}>
            Close
          </button>
        </div>

        <div className="space-y-3 p-4">
          {loading ? <div className="text-xs text-slate-600">Checking requirements…</div> : null}
          {data?.error ? <div className="text-xs text-rose-300">{data.error}</div> : null}

          {data?.items.map((item) => (
            <div key={item.id} className="rounded border border-slate-200 bg-slate-50 p-3">
              <div className="flex items-start justify-between gap-2">
                <span className="text-xs font-medium text-slate-900">{item.label}</span>
                <span className={`shrink-0 text-[10px] uppercase ${statusColor(item.status)}`}>{item.status}</span>
              </div>
              {item.detail ? <p className="mt-1 text-[11px] text-slate-600">{item.detail}</p> : null}
              {item.commands.length > 0 ? (
                <div className="mt-2 space-y-1">
                  {item.commands.map((cmd) => (
                    <code key={cmd} className="block rounded bg-black/40 px-2 py-1 text-[10px] text-[#c2410c]">
                      {cmd}
                    </code>
                  ))}
                </div>
              ) : null}
              {item.links.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {item.links.map((link) => (
                    <a
                      key={link.url}
                      href={link.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-[10px] text-sky-400 underline"
                    >
                      {link.label}
                    </a>
                  ))}
                </div>
              ) : null}
            </div>
          ))}

          {data?.upstream_url ? (
            <a href={data.upstream_url} target="_blank" rel="noreferrer" className="text-xs text-sky-400 underline">
              Upstream source
            </a>
          ) : null}
        </div>
      </div>
    </div>
  );
}
