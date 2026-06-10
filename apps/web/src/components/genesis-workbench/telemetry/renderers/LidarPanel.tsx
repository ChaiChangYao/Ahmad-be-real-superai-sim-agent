"use client";

import type { TelemetryPanelProps } from "./types";
import { RawSensorTable } from "./RawSensorTable";

export function LidarPanel(props: TelemetryPanelProps) {
  const ranges = Object.keys(props.telemetry?.channels ?? {}).filter((c) => c.includes("range"));
  return <RawSensorTable {...props} sensorType="lidar" />;
}
