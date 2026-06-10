import type { TelemetryBundle } from "../../replay/types";

export type TelemetryPanelProps = {
  telemetry: TelemetryBundle | null;
  currentTime?: number;
  frameIndex?: number;
  onScrubTime?: (time: number) => void;
  className?: string;
  emptyMessage?: string;
  channelFilter?: (channel: string) => boolean;
  layout?: "default" | "stacked";
  sensorType?: string;
};
