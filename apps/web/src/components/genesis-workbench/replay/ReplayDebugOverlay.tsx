"use client";

import { getTransform, type ReplayBundle, type ReplayViewSource } from "./types";
import { convertPosition, GENESIS_UP_AXIS, RENDERER_UP_AXIS } from "./replay_transforms";
import type { PlaybackMode } from "./replay_playback";

type Props = {
  replay: ReplayBundle;
  frameIndex: number;
  playing: boolean;
  playbackMode: PlaybackMode;
  replayViewSource: ReplayViewSource;
  distinctVisualStates: number | null;
  usingFallback: boolean;
  variant?: "overlay" | "panel";
};

export function ReplayDebugOverlay({
  replay,
  frameIndex,
  playing,
  playbackMode,
  replayViewSource,
  distinctVisualStates,
  usingFallback,
  variant = "panel",
}: Props) {
  const frame = replay.frames[frameIndex];
  const diagnostics = (replay.meta.diagnostics ?? {}) as Record<string, unknown>;
  const motion = (replay.meta.motion_diagnostics ?? diagnostics.motion_diagnostics ?? {}) as Record<string, unknown>;
  const previewMeta = (replay.meta.preview_meta ?? {}) as Record<string, unknown>;
  const validation = (replay.meta.preview_validation ?? previewMeta.validation ?? {}) as Record<string, unknown>;
  const sourceUpAxis = typeof replay.scene.upAxis === "string" ? replay.scene.upAxis : GENESIS_UP_AXIS;
  const rootLink = replay.objects.find((o) => o.type === "robot_link");
  const rootTransform = rootLink && frame ? getTransform(frame, rootLink.id) : undefined;
  const convertedRoot = rootTransform?.position ? convertPosition(rootTransform.position, sourceUpAxis) : null;

  const rawCount = Number(replay.meta.source_frame_count ?? replay.rawFrames.length ?? 0);
  const previewCount = Number(replay.meta.preview_frame_count ?? replay.previewFrames.length ?? 0);
  const uniquePoses = Number(replay.meta.unique_pose_count ?? motion.unique_pose_count ?? distinctVisualStates ?? 0);
  const longestFreeze = Number(motion.longest_freeze_run ?? diagnostics.longest_freeze_run ?? 0);
  const recorderIssue = String(motion.recorder_issue ?? diagnostics.recorder_issue ?? "");
  const longestPreviewFreeze = Number(validation.longest_frozen_run ?? validation.longest_freeze_run ?? 0);
  const maxPreviewJump = Number(validation.max_position_jump ?? 0);
  const movingPreviewFrames = Number(validation.moving_frames ?? previewCount);
  const previewValid = validation.valid !== false;

  const className =
    variant === "overlay"
      ? "pointer-events-none absolute bottom-2 left-2 z-10 max-w-[90%] rounded bg-black/70 px-2 py-1 font-mono text-[9px] leading-relaxed text-slate-700"
      : "rounded border border-slate-200 bg-slate-100 px-2 py-1 font-mono text-[9px] leading-relaxed text-slate-700";

  return (
    <div className={className}>
      <div>
        view: {replayViewSource} · step: {playbackMode} · playing: {playing ? "yes" : "no"} · upAxis: {String(sourceUpAxis)} · rendererUp:{" "}
        {RENDERER_UP_AXIS}
      </div>
      <div>
        mode: {replayViewSource === "smooth" ? "Smooth preview" : replayViewSource === "preserve_holds" ? "Preserve holds" : "Raw physics"}
        · frame {frameIndex + 1} / {replay.frames.length}
        {rawCount > 0 ? ` · raw: ${rawCount}` : ""}
        {previewCount > 0 ? ` · preview: ${previewCount}` : ""}
      </div>
      {uniquePoses > 0 ? (
        <div>
          distinct raw poses: {uniquePoses}
          {longestFreeze > 1 ? ` · longest raw freeze ${longestFreeze}` : ""}
        </div>
      ) : null}
      {replayViewSource === "smooth" && previewCount > 0 ? (
        <div>
          preview: {movingPreviewFrames} moving frames · freeze={longestPreviewFreeze} · max jump={maxPreviewJump.toFixed(4)}
          {!previewValid ? " · invalid cached preview" : ""}
        </div>
      ) : null}
      {recorderIssue === "repeated_transforms" || recorderIssue === "upstream_demo_hold" ? (
        <div className="text-amber-800">Raw replay contains long hold periods. Smooth preview trims holds by default.</div>
      ) : null}
      <div>links: {String(diagnostics.robot_links ?? "?")} · fallback: {usingFallback ? "yes" : "no"}</div>
      {convertedRoot ? <div>root (converted): [{convertedRoot.map((v) => v.toFixed(3)).join(", ")}]</div> : null}
    </div>
  );
}
