import type { ReplayFrame } from "./types";

export type PlaybackMode = "every_frame" | "realtime";

export const DEFAULT_PLAYBACK_FPS = 24;
export const PLAYBACK_FPS_OPTIONS = [12, 24, 30, 60] as const;

export function clampFrameIndex(index: number, totalFrames: number): number {
  if (totalFrames <= 0) return 0;
  return Math.min(Math.max(0, Math.floor(index)), totalFrames - 1);
}

/** Advance one integer frame when enough wall time has elapsed (every-frame mode). */
export function tickEveryFramePlayback(args: {
  frameIndex: number;
  deltaSeconds: number;
  accumulator: number;
  playbackFps: number;
  speed: number;
  totalFrames: number;
  loop: boolean;
}): { frameIndex: number; accumulator: number; advanced: boolean } {
  const { deltaSeconds, playbackFps, speed, totalFrames, loop } = args;
  if (totalFrames <= 0) {
    return { frameIndex: 0, accumulator: 0, advanced: false };
  }

  let frameIndex = args.frameIndex;
  let accumulator = args.accumulator + Math.max(0, deltaSeconds);
  const frameDuration = 1 / Math.max(1, playbackFps * Math.max(0.01, speed));
  let advanced = false;

  while (accumulator >= frameDuration) {
    accumulator -= frameDuration;
    if (frameIndex >= totalFrames - 1) {
      if (!loop) {
        accumulator = 0;
        return { frameIndex: totalFrames - 1, accumulator, advanced: true };
      }
      frameIndex = 0;
    } else {
      frameIndex += 1;
    }
    advanced = true;
  }

  return { frameIndex, accumulator, advanced };
}

/** Map elapsed replay time to frame index using recorded timestamps. */
export function frameIndexForRealtime(args: {
  elapsedSeconds: number;
  frames: ReplayFrame[];
  speed: number;
  loop: boolean;
  telemetryTimestamps?: number[];
}): number {
  const { elapsedSeconds, frames, speed, loop, telemetryTimestamps } = args;
  if (frames.length === 0 && (!telemetryTimestamps || telemetryTimestamps.length === 0)) return 0;

  const visualLast = frames[frames.length - 1]?.t ?? 0;
  const teleLast =
    telemetryTimestamps && telemetryTimestamps.length > 0
      ? telemetryTimestamps[telemetryTimestamps.length - 1]
      : 0;
  const lastT = Math.max(visualLast, teleLast, 0.001);
  const duration = lastT;

  let t = elapsedSeconds * Math.max(0.01, speed);
  if (loop) {
    t = t % duration;
  } else {
    t = Math.min(t, duration);
  }

  if (frames.length === 0) return 0;
  if (frames.length === 1) return 0;

  let bestIdx = 0;
  for (let i = 0; i < frames.length; i += 1) {
    if ((frames[i]?.t ?? 0) <= t) bestIdx = i;
    else break;
  }
  return bestIdx;
}

/** Resolve playback time from frame index and optional telemetry timeline. */
export function playbackTimeAtFrame(args: {
  frames: ReplayFrame[];
  frameIndex: number;
  telemetryTimestamps?: number[];
}): number {
  const { frames, frameIndex, telemetryTimestamps } = args;
  const visualTime = frames[frameIndex]?.t ?? 0;
  if (!telemetryTimestamps || telemetryTimestamps.length === 0) return visualTime;
  const teleDuration = telemetryTimestamps[telemetryTimestamps.length - 1] ?? 0;
  if (teleDuration <= visualTime || frames.length <= 1) {
    return Math.max(visualTime, telemetryTimestamps[Math.min(frameIndex, telemetryTimestamps.length - 1)] ?? 0);
  }
  return visualTime;
}

/** Frame index for a scrubbed telemetry time (visual sync). */
export function frameIndexForTelemetryTime(args: {
  frames: ReplayFrame[];
  time: number;
}): number {
  const { frames, time } = args;
  if (frames.length === 0) return 0;
  let bestIdx = 0;
  for (let i = 0; i < frames.length; i += 1) {
    if ((frames[i]?.t ?? 0) <= time) bestIdx = i;
    else break;
  }
  return bestIdx;
}
