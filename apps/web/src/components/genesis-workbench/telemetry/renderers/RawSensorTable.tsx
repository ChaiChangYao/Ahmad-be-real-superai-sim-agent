"use client";

import type { TelemetryPanelProps } from "./types";

export function RawSensorTable({ telemetry, sensorType, emptyMessage }: TelemetryPanelProps) {
  const samples = telemetry?.samples ?? [];
  const channelList = telemetry?.channels
    ? Object.keys(telemetry.channels)
    : [];

  const hasChannelData = Boolean(
    telemetry?.timestamps?.length && telemetry?.channels && Object.keys(telemetry.channels).length > 0,
  );

  if (!telemetry || (samples.length === 0 && !hasChannelData)) {
    return (
      <div className="flex h-full items-center justify-center p-4 text-center text-xs text-slate-500">
        {emptyMessage ?? "No sensor samples recorded."}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col overflow-hidden">
      {sensorType ? (
        <div className="border-b border-amber-300/50 bg-amber-50 px-3 py-1.5 text-[10px] text-amber-800">
          Renderer for {sensorType} is not fully implemented — showing raw sample data.
        </div>
      ) : null}
      <div className="flex-1 overflow-auto p-2 text-[10px]">
        <p className="mb-2 text-slate-600">{samples.length} samples · channels: {channelList.join(", ") || "—"}</p>
        <pre className="whitespace-pre-wrap break-all text-slate-700">
          {JSON.stringify(samples.slice(0, 5), null, 2)}
          {samples.length > 5 ? "\n…" : ""}
        </pre>
      </div>
    </div>
  );
}
