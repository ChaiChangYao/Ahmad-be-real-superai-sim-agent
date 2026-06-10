"use client";

import { useMemo } from "react";
import type { TelemetryBundle } from "../replay/types";

type Props = {
  telemetry: TelemetryBundle | null | undefined;
  currentTime?: number;
  onScrubTime?: (time: number) => void;
  className?: string;
  emptyMessage?: string;
  channelFilter?: (channel: string) => boolean;
  layout?: "default" | "stacked";
  title?: string;
};

const CHANNEL_COLORS: Record<string, string> = {
  lin_acc: "#FF6A1A",
  true_lin_acc: "#ff8f4d",
  ang_vel: "#60a5fa",
  true_ang_vel: "#93c5fd",
  contact_force: "#c084fc",
};

function pickChannels(
  channels: Record<string, { x: number[]; y: number[]; z: number[] }>,
  channelFilter?: (channel: string) => boolean,
): string[] {
  const preferred = ["lin_acc", "true_lin_acc", "ang_vel", "true_ang_vel", "contact_force"];
  const keys = Object.keys(channels).filter((k) => (channelFilter ? channelFilter(k) : true));
  const ordered = preferred.filter((k) => keys.includes(k));
  for (const key of keys) {
    if (!ordered.includes(key)) ordered.push(key);
  }
  return ordered.slice(0, channelFilter ? 6 : 4);
}

function seriesBounds(values: number[]): { min: number; max: number } {
  if (values.length === 0) return { min: -1, max: 1 };
  let min = values[0];
  let max = values[0];
  for (const v of values) {
    min = Math.min(min, v);
    max = Math.max(max, v);
  }
  if (Math.abs(max - min) < 1e-6) {
    min -= 1;
    max += 1;
  }
  return { min, max };
}

function buildPath(values: number[], width: number, height: number, min: number, max: number): string {
  if (values.length === 0) return "";
  const span = max - min;
  const stepX = values.length <= 1 ? 0 : width / (values.length - 1);
  const points = values.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / span) * height;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });
  return `M ${points.join(" L ")}`;
}

export function TelemetryChart({ telemetry, currentTime = 0, onScrubTime, className = "", emptyMessage, channelFilter, layout = "default", title }: Props) {
  const channels = telemetry?.channels ?? {};
  const timestamps = telemetry?.timestamps ?? [];
  const channelNames = useMemo(() => pickChannels(channels, channelFilter), [channels, channelFilter]);

  if (!telemetry || timestamps.length === 0 || channelNames.length === 0) {
    return (
      <div
        className={`flex h-full items-center justify-center border-t border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 ${className}`}
      >
        {emptyMessage ?? "No telemetry samples recorded for this run."}
      </div>
    );
  }

  const rowHeight = layout === "stacked" ? 100 : 120;
  const rowGap = layout === "stacked" ? 12 : 8;
  const width = 640;
  const height = rowHeight;
  const duration = timestamps[timestamps.length - 1] || 1;
  const playbackTime = currentTime ?? 0;
  const cursorX = duration > 0 ? (playbackTime / duration) * width : 0;

  let nearestIdx = 0;
  for (let i = 0; i < timestamps.length; i += 1) {
    if (timestamps[i] <= playbackTime) nearestIdx = i;
    else break;
  }

  const isConstant =
    timestamps.length > 1 &&
    channelNames.every((name) => {
      const series = channels[name];
      if (!series?.x?.length) return true;
      const first = series.x[0];
      return series.x.every((v) => Math.abs(v - first) < 1e-8);
    });

  return (
    <div className={`flex h-full min-h-[140px] flex-col border-t border-slate-200 bg-slate-50 ${className}`}>
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-1.5 text-[11px] text-slate-700">
        <span className="font-medium text-[#FF6A1A]">{title ?? "Telemetry"}</span>
        <span className="text-slate-500">
          {timestamps.length} samples · t={playbackTime.toFixed(2)}s · idx {nearestIdx + 1}
        </span>
      </div>
      {isConstant ? (
        <div className="px-3 py-2 text-[11px] text-amber-800">Telemetry is constant for this run.</div>
      ) : null}
      <div className="min-h-0 flex-1 overflow-auto p-2">
        <svg
          viewBox={`0 0 ${width} ${height * channelNames.length + (channelNames.length - 1) * rowGap}`}
          className="h-full w-full"
          role="img"
          aria-label="Telemetry chart"
          onClick={(event) => {
            if (!onScrubTime) return;
            const rect = event.currentTarget.getBoundingClientRect();
            const ratio = (event.clientX - rect.left) / rect.width;
            onScrubTime(Math.max(0, Math.min(duration, ratio * duration)));
          }}
        >
          {channelNames.map((name, row) => {
            const series = channels[name];
            const values = [...(series?.x ?? []), ...(series?.y ?? []), ...(series?.z ?? [])];
            const { min, max } = seriesBounds(values);
            const yOffset = row * (height + rowGap);
            const color = CHANNEL_COLORS[name] ?? "#a78bfa";
            return (
              <g key={name} transform={`translate(0, ${yOffset})`}>
                <text x={4} y={12} fill="#94a3b8" fontSize={10}>
                  {name}
                </text>
                <rect x={0} y={16} width={width} height={height - 16} fill="#f1f5f9" rx={4} />
                {(["x", "y", "z"] as const).map((axis, axisIdx) => {
                  const axisValues = series?.[axis] ?? [];
                  const axisColors = ["#f87171", "#4ade80", "#60a5fa"];
                  return (
                    <path
                      key={axis}
                      d={buildPath(axisValues, width, height - 20, min, max)}
                      transform="translate(0, 18)"
                      fill="none"
                      stroke={axisColors[axisIdx]}
                      strokeWidth={axisIdx === 0 ? 1.4 : 1}
                      opacity={0.85}
                    />
                  );
                })}
                <line
                  x1={cursorX}
                  x2={cursorX}
                  y1={16}
                  y2={height}
                  stroke={color}
                  strokeDasharray="3 3"
                  opacity={0.8}
                />
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

export function nearestTelemetryIndex(timestamps: number[] | undefined, time: number): number {
  if (!timestamps || timestamps.length === 0) return 0;
  let best = 0;
  for (let i = 0; i < timestamps.length; i += 1) {
    if (timestamps[i] <= time) best = i;
    else break;
  }
  return best;
}

export function telemetryDuration(timestamps: number[] | undefined): number {
  if (!timestamps || timestamps.length === 0) return 0;
  return timestamps[timestamps.length - 1] ?? 0;
}
