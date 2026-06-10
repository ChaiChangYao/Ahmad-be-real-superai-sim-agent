"use client";

import type { ViewportMeshMode } from "@/lib/state";

type ViewportHudProps = {
  genesisMissing: boolean;
  replayLabel: string;
  meshMode: ViewportMeshMode;
  showCom: boolean;
  showJointAxes: boolean;
  showSensorRays: boolean;
  showWires: boolean;
  onMeshModeChange: (mode: ViewportMeshMode) => void;
  onToggleCom: () => void;
  onToggleJointAxes: () => void;
  onToggleSensorRays: () => void;
  onToggleWires: () => void;
  onResetCamera: () => void;
  onFrameModel: () => void;
  onTopView: () => void;
  onFrontView: () => void;
  onSideView: () => void;
};

function HudBtn({ label, onClick, active }: { label: string; onClick: () => void; active?: boolean }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded px-1.5 py-0.5 text-[10px] ${
        active ? "bg-accent text-white" : "bg-white/70 text-slate-800 hover:bg-slate-100/90"
      }`}
    >
      {label}
    </button>
  );
}

export function ViewportHud({
  genesisMissing,
  replayLabel,
  meshMode,
  showCom,
  showJointAxes,
  showSensorRays,
  showWires,
  onMeshModeChange,
  onToggleCom,
  onToggleJointAxes,
  onToggleSensorRays,
  onToggleWires,
  onResetCamera,
  onFrameModel,
  onTopView,
  onFrontView,
  onSideView,
}: ViewportHudProps) {
  return (
    <>
      <div className="pointer-events-none absolute left-2 top-2 z-10">
        <div className="rounded border border-slate-300/60 bg-slate-100 px-2 py-1 text-[10px] text-slate-800 backdrop-blur">
          <span className={genesisMissing ? "text-amber-300" : "text-emerald-300"}>{replayLabel}</span>
        </div>
      </div>

      <div className="absolute left-2 bottom-2 z-10 flex flex-wrap gap-1">
        <HudBtn label="Visual" active={meshMode === "visual"} onClick={() => onMeshModeChange("visual")} />
        <HudBtn label="Collision" active={meshMode === "collision"} onClick={() => onMeshModeChange("collision")} />
        <HudBtn label="Both" active={meshMode === "both"} onClick={() => onMeshModeChange("both")} />
        <HudBtn label="COM" active={showCom} onClick={onToggleCom} />
        <HudBtn label="Joints" active={showJointAxes} onClick={onToggleJointAxes} />
        <HudBtn label="Sensors" active={showSensorRays} onClick={onToggleSensorRays} />
        <HudBtn label="Wires" active={showWires} onClick={onToggleWires} />
      </div>

      <div className="absolute right-2 top-2 z-10 flex flex-wrap justify-end gap-1">
        <HudBtn label="Frame" onClick={onFrameModel} />
        <HudBtn label="Reset Cam" onClick={onResetCamera} />
        <HudBtn label="Top" onClick={onTopView} />
        <HudBtn label="Front" onClick={onFrontView} />
        <HudBtn label="Side" onClick={onSideView} />
      </div>
    </>
  );
}
