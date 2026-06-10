import { getTransform, type ReplayBundle, type ReplayFrame } from "./types";

export type ReplayFrameAnalysis = {
  totalFrames: number;
  firstIndex: number;
  lastIndex: number;
  firstTimestamp: number;
  lastTimestamp: number;
  sampledObjectId: string | null;
  distinctVisualStates: number;
  changeIndices: number[];
  identicalFrameRatio: number;
};

function transformKey(frame: ReplayFrame, objectId: string): string | null {
  const t = getTransform(frame, objectId);
  if (!t) return null;
  return JSON.stringify({
    p: t.position,
    q: t.quaternion ?? t.rotation_quat,
  });
}

export function analyzeReplayMotion(frames: ReplayFrame[], objectIds: string[]): ReplayFrameAnalysis {
  const totalFrames = frames.length;
  const firstIndex = 0;
  const lastIndex = Math.max(0, totalFrames - 1);
  const firstTimestamp = frames[firstIndex]?.t ?? 0;
  const lastTimestamp = frames[lastIndex]?.t ?? 0;

  let sampledObjectId: string | null = null;
  for (const id of objectIds) {
    if (frames.some((f) => getTransform(f, id))) {
      sampledObjectId = id;
      break;
    }
  }

  const changeIndices: number[] = [];
  let prev: string | null = null;
  if (sampledObjectId) {
    for (let i = 0; i < frames.length; i += 1) {
      const key = transformKey(frames[i], sampledObjectId);
      if (key !== prev) {
        changeIndices.push(i);
        prev = key;
      }
    }
  }

  const distinctVisualStates = Math.max(1, changeIndices.length);
  const identicalFrameRatio = totalFrames > 0 ? 1 - distinctVisualStates / totalFrames : 0;

  return {
    totalFrames,
    firstIndex,
    lastIndex,
    firstTimestamp,
    lastTimestamp,
    sampledObjectId,
    distinctVisualStates,
    changeIndices,
    identicalFrameRatio,
  };
}

export function logReplayDiagnostics(bundle: ReplayBundle): ReplayFrameAnalysis {
  const objectIds = bundle.objects
    .filter((o) => o.type === "robot_link" || o.type.includes("box") || o.id.includes("cube"))
    .map((o) => o.id);
  const analysis = analyzeReplayMotion(bundle.frames, objectIds);

  const manifest = bundle.meta.replay_manifest as { fps?: number; status?: string } | undefined;
  console.info("[replay-diagnostics] launch=", bundle.launchId, {
    frames: analysis.totalFrames,
    firstIndex: analysis.firstIndex,
    lastIndex: analysis.lastIndex,
    firstTimestamp: analysis.firstTimestamp,
    lastTimestamp: analysis.lastTimestamp,
    recordingFps: manifest?.fps ?? bundle.meta.replay_fps ?? null,
    status: manifest?.status ?? null,
    sampledObjectId: analysis.sampledObjectId,
    distinctVisualStates: analysis.distinctVisualStates,
    changeIndices: analysis.changeIndices.slice(0, 20),
    identicalFrameRatio: analysis.identicalFrameRatio.toFixed(3),
  });

  if (analysis.distinctVisualStates < analysis.totalFrames * 0.5) {
    console.warn(
      `[replay-diagnostics] Many frames share identical transforms (${analysis.distinctVisualStates} distinct visual states / ${analysis.totalFrames} frames). Scrubbing will still visit every frame index, but motion may look stepped.`,
    );
  }

  return analysis;
}

export function logAppliedFrame(
  frameIndex: number,
  totalFrames: number,
  sampledObjectId: string | null,
  frames: ReplayFrame[],
  debugMode = false,
): void {
  if (totalFrames === 0) return;
  if (!debugMode && frameIndex % 10 !== 0 && frameIndex !== totalFrames - 1) return;

  let suffix = "";
  if (sampledObjectId && frameIndex > 0) {
    const prev = transformKey(frames[frameIndex - 1], sampledObjectId);
    const cur = transformKey(frames[frameIndex], sampledObjectId);
    if (prev === cur) suffix = " (transform unchanged vs previous frame)";
  }

  console.info(`[replay-playback] Applied frame ${frameIndex} / ${totalFrames - 1}${suffix}`);
}

function posDelta(a: number[] | undefined, b: number[] | undefined): number {
  if (!a || !b || a.length < 3 || b.length < 3) return 0;
  return Math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[2] - a[2]) ** 2);
}

export function checkMotionAfterFrame(
  frames: ReplayFrame[],
  objectIds: string[],
  startIndex: number,
  lookahead = 10,
): { movingFrames: number; frozenFrames: number; maxDelta: number; sampleObjectId: string | null } {
  let movingFrames = 0;
  let frozenFrames = 0;
  let maxDelta = 0;
  let sampleObjectId: string | null = null;
  for (const id of objectIds) {
    if (frames.some((f) => getTransform(f, id))) {
      sampleObjectId = id;
      break;
    }
  }
  const end = Math.min(frames.length - 1, startIndex + lookahead);
  for (let i = startIndex + 1; i <= end; i += 1) {
    let frameMax = 0;
    for (const id of objectIds) {
      const prev = getTransform(frames[i - 1], id)?.position;
      const cur = getTransform(frames[i], id)?.position;
      frameMax = Math.max(frameMax, posDelta(prev, cur));
    }
    maxDelta = Math.max(maxDelta, frameMax);
    if (frameMax > 1e-4) movingFrames += 1;
    else frozenFrames += 1;
  }
  return { movingFrames, frozenFrames, maxDelta, sampleObjectId };
}

export function warnStalePreviewTail(bundle: ReplayBundle): void {
  const validation = (bundle.meta.preview_validation ?? {}) as Record<string, unknown>;
  const tail = validation.frozen_tail_starts_at;
  if (tail != null && typeof tail === "number") {
    console.warn(
      `[replay-diagnostics] Smooth preview still has frozen tail starting at frame ${tail}. Reload replay or regenerate preview.`,
    );
  }
}
