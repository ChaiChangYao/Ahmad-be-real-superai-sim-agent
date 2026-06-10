"use client";

import type { GenesisWorkbenchReadiness, ShowcaseCatalog } from "@/lib/genesisWorkbenchApi";
import type { BootStatus } from "./GenesisWorkbenchShell";

type Props = {
  readiness: GenesisWorkbenchReadiness | null;
  catalog: ShowcaseCatalog | null;
  bootStatus?: BootStatus;
};

export function GenesisReadinessPanel({ readiness, catalog, bootStatus }: Props) {
  if (!readiness) {
    const msg =
      bootStatus === "error"
        ? "API unavailable — demo list not loaded"
        : "Environment data unavailable — start API and click Retry";
    return <div className="text-xs text-slate-500">{msg}</div>;
  }

  return (
    <div className="space-y-3 text-[11px]">
      <div>
        <div className="font-semibold text-slate-800">Environment</div>
        <div className="mt-1 space-y-1 text-slate-600">
          <div>Python {readiness.python_version}</div>
          {readiness.torch_version ? <div>PyTorch {readiness.torch_version}</div> : null}
          {readiness.genesis_world_pip ? <div>Physics engine {readiness.genesis_world_pip}</div> : null}
        </div>
      </div>

      <div>
        <div className="font-semibold text-slate-800">GPU</div>
        <div className="mt-1 text-slate-600">
          {readiness.gpu.available
            ? `${readiness.gpu.gpu_name}${readiness.gpu.driver_version ? ` · driver ${readiness.gpu.driver_version}` : ""}`
            : readiness.gpu.detail}
        </div>
      </div>

      {catalog ? (
        <div className="rounded border border-slate-200 bg-slate-50 p-2">
          <div className="font-medium text-[#c2410c]">
            {catalog.available}/{catalog.total} demos ready
          </div>
        </div>
      ) : null}
    </div>
  );
}
