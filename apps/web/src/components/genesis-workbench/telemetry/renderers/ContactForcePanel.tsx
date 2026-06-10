"use client";

import { TelemetryChart } from "../TelemetryChart";
import type { TelemetryPanelProps } from "./types";

export function ContactForcePanel(props: TelemetryPanelProps) {
  return (
    <div className={`flex h-full min-h-0 flex-col ${props.className ?? ""}`}>
      <div className="min-h-0 flex-1 border-b border-slate-200">
        <TelemetryChart
          {...props}
          title="Combined force"
          channelFilter={(name) => name === "force"}
          layout="stacked"
          className="h-full border-t-0"
        />
      </div>
      <div className="min-h-0 flex-1 border-b border-slate-200">
        <TelemetryChart
          {...props}
          title="RR_foot Force Sensor Data"
          channelFilter={(name) => name === "RR_foot"}
          layout="stacked"
          className="h-full border-t-0"
        />
      </div>
      <div className="min-h-0 flex-1">
        <TelemetryChart
          {...props}
          title="FL_foot Force Sensor Data"
          channelFilter={(name) => name === "FL_foot"}
          layout="stacked"
          className="h-full border-t-0"
        />
      </div>
    </div>
  );
}
