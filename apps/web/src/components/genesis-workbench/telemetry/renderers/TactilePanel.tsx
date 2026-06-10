"use client";

import { useMemo } from "react";
import type { TelemetryPanelProps } from "./types";
import { RawSensorTable } from "./RawSensorTable";

const MAX_MAGNITUDE = 0.01;

function magnitudeColor(value: number): string {
  const t = Math.max(0, Math.min(1, value / MAX_MAGNITUDE));
  const r = Math.round(68 + t * (255 - 68));
  const g = Math.round(1 + t * (200 - 1));
  const b = Math.round(84 + t * (50 - 84));
  return `rgb(${r}, ${g}, ${b})`;
}

export function TactilePanel(props: TelemetryPanelProps) {
  const frames = props.telemetry?.tactile_frames;
  const frameIndex = props.frameIndex ?? 0;

  const frame = useMemo(() => {
    if (!frames || frames.length === 0) return null;
    return frames[Math.min(frameIndex, frames.length - 1)];
  }, [frames, frameIndex]);

  const bounds = useMemo(() => {
    if (!frame?.positions?.length) return { minX: -0.05, maxX: 0.05, minY: -0.075, maxY: 0.075 };
    const xs = frame.positions.map((p) => p[0]);
    const ys = frame.positions.map((p) => p[1]);
    return {
      minX: Math.min(...xs),
      maxX: Math.max(...xs),
      minY: Math.min(...ys),
      maxY: Math.max(...ys),
    };
  }, [frame]);

  if (!frame?.positions?.length) {
    return <RawSensorTable {...props} sensorType="tactile" />;
  }

  const width = 420;
  const height = 320;
  const pad = 36;
  const plotW = width - pad * 2 - 24;
  const plotH = height - pad * 2;

  const toX = (x: number) => pad + ((x - bounds.minX) / Math.max(1e-6, bounds.maxX - bounds.minX)) * plotW;
  const toY = (y: number) => pad + plotH - ((y - bounds.minY) / Math.max(1e-6, bounds.maxY - bounds.minY)) * plotH;

  const magnitudes = frame.magnitudes ?? frame.displacements?.map((d) => Math.hypot(d[0], d[1], d[2])) ?? [];

  return (
    <div className={`flex h-full flex-col bg-white ${props.className ?? ""}`}>
      <div className="border-b border-slate-200 px-3 py-2 text-xs font-medium text-slate-700">
        Elastomer marker displacements (mm)
      </div>
      <div className="flex min-h-0 flex-1 items-center justify-center p-3">
        <svg viewBox={`0 0 ${width} ${height}`} className="h-full max-h-full w-full max-w-full" role="img">
          <rect x={0} y={0} width={width} height={height} fill="#ffffff" />
          <text x={width / 2} y={16} textAnchor="middle" fill="#334155" fontSize={11}>
            y [m]
          </text>
          <text x={width / 2} y={height - 8} textAnchor="middle" fill="#334155" fontSize={11}>
            x [m]
          </text>
          {frame.positions.map((pos, i) => {
            const mag = magnitudes[i] ?? 0;
            return (
              <circle
                key={i}
                cx={toX(pos[0])}
                cy={toY(pos[1])}
                r={2.2}
                fill={magnitudeColor(mag)}
                opacity={0.85}
              />
            );
          })}
          <g transform={`translate(${width - 28}, ${pad})`}>
            {[0, 0.25, 0.5, 0.75, 1].map((t, i) => {
              const y = (1 - t) * plotH;
              return (
                <rect key={i} x={0} y={y} width={10} height={plotH / 4 + 1} fill={magnitudeColor(t * MAX_MAGNITUDE)} />
              );
            })}
            <text x={14} y={plotH + 4} fill="#475569" fontSize={9}>
              0.000
            </text>
            <text x={14} y={10} fill="#475569" fontSize={9}>
              0.010
            </text>
            <text x={14} y={plotH / 2} fill="#475569" fontSize={8} transform={`rotate(90 14 ${plotH / 2})`}>
              displacement [mm]
            </text>
          </g>
        </svg>
      </div>
    </div>
  );
}
