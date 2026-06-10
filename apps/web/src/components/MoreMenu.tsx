"use client";

import Link from "next/link";
import { useState } from "react";

type MoreMenuProps = {
  dirty: boolean;
  onSave: () => Promise<void>;
  onRunSuite: () => Promise<void>;
  onRunGenesisScene: () => Promise<void>;
  onNativeViewer: () => Promise<void>;
  onSwitchProject: () => Promise<void>;
  onClearProject: () => Promise<void>;
  onError?: (message: string) => void;
};

export function MoreMenu({
  dirty,
  onSave,
  onRunSuite,
  onRunGenesisScene,
  onNativeViewer,
  onSwitchProject,
  onClearProject,
  onError,
}: MoreMenuProps) {
  const [open, setOpen] = useState(false);

  async function run(action: () => Promise<void>) {
    setOpen(false);
    try {
      await action();
    } catch (error) {
      const message = (error as Error).message || "Unknown action error.";
      onError?.(message);
    }
  }

  return (
    <div className="relative">
      <button type="button" className="rounded border border-border bg-white px-2 py-1 text-xs hover:bg-slate-50" onClick={() => setOpen((v) => !v)}>
        More ▾
      </button>
      {open ? (
        <>
          <button type="button" className="fixed inset-0 z-40" aria-label="Close menu" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full z-50 mt-1 min-w-[180px] rounded border border-border bg-white py-1 shadow-lg">
            <Link
              href="/genesis"
              className="block w-full px-3 py-1.5 text-left text-xs font-semibold text-[#c2410c] hover:bg-orange-50"
              onClick={() => setOpen(false)}
            >
              Tekong EMart (demo simulations) →
            </Link>
            <hr className="my-1 border-border" />
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50 disabled:opacity-40" disabled={!dirty} onClick={() => void run(onSave)}>
              Save Manifest
            </button>
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50" onClick={() => void run(onRunSuite)}>
              Run Test Suite
            </button>
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50" onClick={() => void run(onRunGenesisScene)}>
              Run Genesis Scene
            </button>
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50" onClick={() => void run(onNativeViewer)}>
              Native Viewer
            </button>
            <hr className="my-1 border-border" />
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50" onClick={() => void run(onSwitchProject)}>
              Switch Project
            </button>
            <button type="button" className="block w-full px-3 py-1.5 text-left text-xs hover:bg-slate-50" onClick={() => void run(onClearProject)}>
              Clear Active Project
            </button>
          </div>
        </>
      ) : null}
    </div>
  );
}
