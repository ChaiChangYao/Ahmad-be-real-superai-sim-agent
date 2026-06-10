"use client";

import { useMemo } from "react";
import type { TelemetryPanelProps } from "./types";
import { RawSensorTable } from "./RawSensorTable";

function heatColor(value: number, min: number, max: number): string {
  const t = max > min ? (value - min) / (max - min) : 0.5;
  const r = Math.round(80 + t * 175);
  const g = Math.round(20 + t * 80);
  const b = Math.round(180 - t * 140);
  return `rgb(${r},${g},${b})`;
}

export function TemperatureGridPanel(props: TelemetryPanelProps) {
  const grid = useMemo(() => {
    const samples = props.telemetry?.samples ?? [];
    if (!samples.length) return null;
    const idx = Math.min(props.frameIndex ?? 0, samples.length - 1);
    const sample = samples[idx] as Record<string, unknown>;
    const gridData = sample?.grid ?? sample?.temperature_grid;
    if (!Array.isArray(gridData)) return null;
    return gridData as number[][];
  }, [props.telemetry, props.frameIndex]);

  if (!grid) {
    return <RawSensorTable {...props} sensorType="temperature_grid" />;
  }

  const flat = grid.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);

  return (
    <div className="flex h-full flex-col p-3">
      <p className="mb-2 text-xs text-slate-600">Temperature grid ({grid.length}×{grid[0]?.length ?? 0})</p>
      <div
        className="grid gap-0.5"
        style={{ gridTemplateColumns: `repeat(${grid[0]?.length ?? 1}, minmax(0, 1fr))` }}
      >
        {grid.flatMap((row, ri) =>
          row.map((cell, ci) => (
            <div key={`${ri}-${ci}`} className="aspect-square rounded-sm" style={{ backgroundColor: heatColor(cell, min, max) }} title={`${cell.toFixed(2)}`} />
          )),
        )}
      </div>
    </div>
  );
}
