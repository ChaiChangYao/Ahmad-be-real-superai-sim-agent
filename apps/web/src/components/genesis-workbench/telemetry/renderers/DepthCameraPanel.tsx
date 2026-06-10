"use client";

import type { TelemetryPanelProps } from "./types";
import { RawSensorTable } from "./RawSensorTable";

function resolveDepthEntry(
  entry: string | { dataUrl?: string; robot?: string; world?: string } | Record<string, string> | undefined,
): { robot?: string; world?: string } {
  if (!entry) return {};
  if (typeof entry === "string") return { robot: entry };
  if ("robot" in entry || "world" in entry) {
    return {
      robot: typeof entry.robot === "string" ? entry.robot : undefined,
      world: typeof entry.world === "string" ? entry.world : undefined,
    };
  }
  if ("dataUrl" in entry && typeof entry.dataUrl === "string") {
    return { robot: entry.dataUrl };
  }
  return {
    robot: typeof (entry as Record<string, string>).robot === "string" ? (entry as Record<string, string>).robot : undefined,
    world: typeof (entry as Record<string, string>).world === "string" ? (entry as Record<string, string>).world : undefined,
  };
}

function DepthImage({ src, label }: { src?: string; label: string }) {
  if (!src) {
    return (
      <div className="flex flex-1 items-center justify-center bg-white text-xs text-slate-600">{label} — no data</div>
    );
  }
  return (
    <div className="flex min-h-0 flex-1 flex-col bg-white p-2">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={src} alt={label} className="mx-auto max-h-full max-w-full object-contain" />
    </div>
  );
}

export function DepthCameraPanel(props: TelemetryPanelProps) {
  const frames = props.telemetry?.depth_frames;
  const frameIndex = props.frameIndex ?? 0;

  if (!frames || frames.length === 0) {
    return <RawSensorTable {...props} sensorType="depth_camera" />;
  }

  const entry = resolveDepthEntry(frames[Math.min(frameIndex, frames.length - 1)]);

  return (
    <div className={`flex h-full min-h-0 flex-col bg-white ${props.className ?? ""}`}>
      <DepthImage src={entry.robot} label="Depth - robot cam" />
      <div className="h-px bg-slate-200" />
      <DepthImage src={entry.world} label="Depth - world cam" />
    </div>
  );
}
