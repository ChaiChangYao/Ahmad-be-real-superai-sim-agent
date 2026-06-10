"use client";

import type { ComponentType } from "react";
import { ContactForcePanel } from "./ContactForcePanel";
import { DepthCameraPanel } from "./DepthCameraPanel";
import { ImuTelemetryPanel } from "./ImuTelemetryPanel";
import { LidarPanel } from "./LidarPanel";
import { RawSensorTable } from "./RawSensorTable";
import { TactilePanel } from "./TactilePanel";
import { TemperatureGridPanel } from "./TemperatureGridPanel";
import type { TelemetryPanelProps } from "./types";

export const SENSOR_RENDERERS: Record<string, ComponentType<TelemetryPanelProps>> = {
  imu: ImuTelemetryPanel,
  depth_camera: DepthCameraPanel,
  temperature_grid: TemperatureGridPanel,
  contact_force: ContactForcePanel,
  lidar: LidarPanel,
  tactile: TactilePanel,
  surface_distance: RawSensorTable,
};

export function resolveSensorRenderer(sensorType: string | null | undefined) {
  if (!sensorType) return RawSensorTable;
  return SENSOR_RENDERERS[sensorType] ?? RawSensorTable;
}

export type { TelemetryPanelProps };
