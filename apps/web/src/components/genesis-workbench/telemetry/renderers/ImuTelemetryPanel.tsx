"use client";

import { TelemetryChart } from "../TelemetryChart";
import type { TelemetryPanelProps } from "./types";

export function ImuTelemetryPanel(props: TelemetryPanelProps) {
  return <TelemetryChart {...props} />;
}
