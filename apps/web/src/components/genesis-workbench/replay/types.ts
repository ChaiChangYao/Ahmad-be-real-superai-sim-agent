export type ReplayTransform = {
  position: number[];
  quaternion?: number[];
  rotation_quat?: number[];
};

export type ReplayVisual = {
  kind?: string;
  size?: number[];
  color?: string;
  meshPath?: string;
  radius?: number;
  length?: number;
  height?: number;
  geomType?: string;
};

export type ReplayObject = {
  id: string;
  type: string;
  parent?: string;
  link_name?: string;
  robot_model?: string;
  visual?: ReplayVisual;
};

export type ReplayFrame = {
  t: number;
  step: number;
  transforms?: Record<string, ReplayTransform>;
  entities?: Record<string, ReplayTransform>;
  qpos?: Record<string, number[]>;
  lidar_points?: number[][];
};

export type ReplayViewSource = "smooth" | "raw" | "preserve_holds";

export type TelemetryChannelSeries = {
  x: number[];
  y: number[];
  z: number[];
};

export type TelemetryBundle = {
  sampleRate?: number;
  playbackRate?: number;
  timestamps?: number[];
  channels?: Record<string, TelemetryChannelSeries>;
  samples?: Array<Record<string, unknown>>;
  depth_frames?: Array<string | { dataUrl?: string; robot?: string; world?: string } | Record<string, string>>;
  tactile_frames?: Array<{
    positions?: number[][];
    displacements?: number[][];
    magnitudes?: number[];
  }>;
  image_frames?: Array<string | { dataUrl?: string }>;
  source?: string;
  type?: string;
  imu?: {
    type?: string;
    sampleRate?: number;
    channels?: string[];
    samples?: Array<Record<string, unknown>>;
  };
};

const IMU_VECTOR_CHANNELS = ["lin_acc", "true_lin_acc", "ang_vel", "true_ang_vel"] as const;

function asNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) return [];
  return value.map((v) => Number(v));
}

export function normalizeTelemetryBundle(raw: unknown): TelemetryBundle | null {
  if (!raw || typeof raw !== "object") return null;
  const record = raw as Record<string, unknown>;

  const schema = record.schema as Record<string, unknown> | undefined;
  if (schema && typeof schema.type === "string" && Array.isArray(record.samples)) {
    return normalizeTelemetryBundle({
      type: schema.type,
      samples: record.samples,
      sampleRate: schema.sampleRate ?? schema.sample_rate,
    });
  }

  const nestedImu = record.imu;
  const imuSchema =
    record.type === "imu" && Array.isArray(record.samples)
      ? record
      : nestedImu && typeof nestedImu === "object"
        ? nestedImu
        : null;

  if (imuSchema && typeof imuSchema === "object") {
    const samples = (imuSchema as Record<string, unknown>).samples;
    if (Array.isArray(samples) && samples.length > 0) {
      const channels: Record<string, TelemetryChannelSeries> = {};
      const timestamps: number[] = [];
      for (const sample of samples) {
        if (!sample || typeof sample !== "object") continue;
        const row = sample as Record<string, unknown>;
        timestamps.push(Number(row.t ?? timestamps.length));
        for (const name of IMU_VECTOR_CHANNELS) {
          const vec = asNumberArray(row[name]);
          if (vec.length === 0) continue;
          const bucket = channels[name] ?? { x: [], y: [], z: [] };
          bucket.x.push(vec[0] ?? 0);
          bucket.y.push(vec[1] ?? 0);
          bucket.z.push(vec[2] ?? 0);
          channels[name] = bucket;
        }
      }
      if (timestamps.length > 0 && Object.keys(channels).length > 0) {
        return {
          sampleRate: Number((imuSchema as Record<string, unknown>).sampleRate ?? record.sampleRate ?? 100),
          timestamps,
          channels,
          samples: samples as Array<Record<string, unknown>>,
          type: "imu",
        };
      }
    }
  }

  const timestamps = record.timestamps;
  const channels = record.channels;
  const depthFrames = record.depth_frames;
  const tactileFrames = record.tactile_frames;
  if (Array.isArray(depthFrames) && depthFrames.length > 0) {
    return {
      ...(record as TelemetryBundle),
      depth_frames: depthFrames,
      type: typeof record.type === "string" ? record.type : "depth_camera",
    };
  }
  if (Array.isArray(tactileFrames) && tactileFrames.length > 0) {
    return {
      ...(record as TelemetryBundle),
      tactile_frames: tactileFrames,
      type: typeof record.type === "string" ? record.type : "tactile",
    };
  }
  if (Array.isArray(timestamps) && timestamps.length > 0 && channels && typeof channels === "object") {
    return record as TelemetryBundle;
  }
  return null;
}

export type ReplayBundle = {
  launchId: string;
  projectId: string;
  scene: Record<string, unknown>;
  objects: ReplayObject[];
  frames: ReplayFrame[];
  rawFrames: ReplayFrame[];
  previewFrames: ReplayFrame[];
  viewSource: ReplayViewSource;
  telemetry?: TelemetryBundle | null;
  meta: Record<string, unknown>;
};

export function getTransform(frame: ReplayFrame, objectId: string): ReplayTransform | undefined {
  const t = frame.transforms?.[objectId] ?? frame.entities?.[objectId];
  return t;
}

export function getQuaternion(t: ReplayTransform | undefined): [number, number, number, number] | null {
  if (!t) return null;
  const q = t.quaternion ?? t.rotation_quat;
  if (!q || q.length < 4) return null;
  return [q[0], q[1], q[2], q[3]];
}

export function normalizeReplay(
  raw: {
    launch_id?: string;
    project_id?: string;
    scene?: Record<string, unknown>;
    objects?: ReplayObject[];
    state_timeseries?: ReplayFrame[];
    raw_frames?: ReplayFrame[];
    preview_frames?: ReplayFrame[];
    telemetry?: TelemetryBundle | null;
    meta?: Record<string, unknown>;
  },
  projectId: string,
  launchId: string,
  viewSource: ReplayViewSource = "smooth",
): ReplayBundle {
  const rawFrames = (
    Array.isArray(raw.raw_frames) && raw.raw_frames.length > 0
      ? raw.raw_frames
      : viewSource === "raw" || viewSource === "preserve_holds"
        ? (raw.state_timeseries ?? [])
        : []
  ) as ReplayFrame[];
  const previewFrames = (raw.preview_frames ?? []) as ReplayFrame[];
  const defaultFrames = (raw.state_timeseries ?? []) as ReplayFrame[];

  let frames: ReplayFrame[];
  if (viewSource === "raw" || viewSource === "preserve_holds") {
    frames =
      rawFrames.length > 0
        ? rawFrames
        : defaultFrames.length > 0
          ? defaultFrames
          : previewFrames;
  } else {
    frames =
      previewFrames.length > 0
        ? previewFrames
        : defaultFrames.length > 0
          ? defaultFrames
          : rawFrames;
  }

  let objects = (raw.objects ?? []) as ReplayObject[];
  const meta = (raw.meta ?? {}) as Record<string, unknown>;

  if (objects.length === 0 && meta.entities && typeof meta.entities === "object") {
    objects = Object.entries(meta.entities as Record<string, ReplayVisual>).map(([id, visual]) => ({
      id,
      type: visual.kind === "plane" ? "plane" : visual.kind === "box" ? "box" : "entity",
      visual,
    }));
  }

  return {
    launchId: raw.launch_id ?? launchId,
    projectId: raw.project_id ?? projectId,
    scene: raw.scene ?? (meta.scene as Record<string, unknown>) ?? {},
    objects,
    frames,
    rawFrames:
      rawFrames.length > 0
        ? rawFrames
        : viewSource !== "smooth" && defaultFrames.length > 0
          ? defaultFrames
          : previewFrames.length > 0
            ? previewFrames
            : defaultFrames,
    previewFrames,
    viewSource,
    telemetry: normalizeTelemetryBundle(raw.telemetry) ?? null,
    meta,
  };
}

import { getApiBase } from "@/lib/apiBase";

export function showcaseMeshUrl(projectId: string, launchId: string, meshPath: string): string {
  const base = getApiBase();
  const safe = meshPath.replace(/^\//, "");
  return `${base}/projects/${projectId}/genesis/showcase/launch/${launchId}/mesh/${safe}`;
}
