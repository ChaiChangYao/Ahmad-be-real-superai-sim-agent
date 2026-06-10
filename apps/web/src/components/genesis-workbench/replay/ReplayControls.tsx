"use client";

import { PLAYBACK_FPS_OPTIONS, type PlaybackMode } from "./replay_playback";
import type { ReplayViewSource } from "./types";

type Props = {
  playing: boolean;
  frameIndex: number;
  totalFrames: number;
  speed: number;
  playbackFps: number;
  playbackMode: PlaybackMode;
  replayViewSource: ReplayViewSource;
  showDebugOverlay: boolean;
  onPlayPause: () => void;
  onRestart: () => void;
  onStepBack: () => void;
  onStepForward: () => void;
  onFitCamera: () => void;
  onScrub: (idx: number) => void;
  onSpeed: (speed: number) => void;
  onPlaybackFps: (fps: number) => void;
  onPlaybackMode: (mode: PlaybackMode) => void;
  onReplayViewSource: (source: ReplayViewSource) => void;
  onToggleDebugOverlay: () => void;
  onCheckMotionAfterFrame: () => void;
};

const SPEEDS = [0.25, 0.5, 1, 2];

export function ReplayControls({
  playing,
  frameIndex,
  totalFrames,
  speed,
  playbackFps,
  playbackMode,
  replayViewSource,
  showDebugOverlay,
  onPlayPause,
  onRestart,
  onStepBack,
  onStepForward,
  onFitCamera,
  onScrub,
  onSpeed,
  onPlaybackFps,
  onPlaybackMode,
  onReplayViewSource,
  onToggleDebugOverlay,
  onCheckMotionAfterFrame,
}: Props) {
  const status =
    totalFrames === 0
      ? "No frames"
      : playing
        ? `Playing · frame ${frameIndex + 1} / ${totalFrames}`
        : `Frame ${frameIndex + 1} / ${totalFrames}`;

  return (
    <div data-testid="replay-controls" className="space-y-2 border-t border-slate-200 px-3 py-2 text-[10px] text-slate-700">
      <div className="flex flex-wrap items-center gap-2">
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onPlayPause}>
          {playing ? "Pause" : "Play"}
        </button>
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onRestart}>
          Restart
        </button>
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onStepBack} disabled={totalFrames === 0}>
          −1 frame
        </button>
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onStepForward} disabled={totalFrames === 0}>
          +1 frame
        </button>
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onFitCamera}>
          Fit view
        </button>
        <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onToggleDebugOverlay}>
          {showDebugOverlay ? "Hide debug" : "Show debug"}
        </button>
        {showDebugOverlay ? (
          <button type="button" className="rounded border border-slate-300 px-2 py-0.5 hover:bg-slate-100" onClick={onCheckMotionAfterFrame}>
            Check motion +10
          </button>
        ) : null}
        <span className="text-slate-600">{status}</span>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1 text-slate-600">
          Speed
          <select
            className="rounded border border-slate-300 bg-white px-1 py-0.5"
            value={speed}
            onChange={(e) => onSpeed(Number(e.target.value))}
          >
            {SPEEDS.map((s) => (
              <option key={s} value={s}>
                {s}x
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-slate-600">
          FPS
          <select
            className="rounded border border-slate-300 bg-white px-1 py-0.5"
            value={playbackFps}
            onChange={(e) => onPlaybackFps(Number(e.target.value))}
          >
            {PLAYBACK_FPS_OPTIONS.map((fps) => (
              <option key={fps} value={fps}>
                {fps}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1 text-slate-600">
          Replay
          <select
            className="rounded border border-slate-300 bg-white px-1 py-0.5"
            value={replayViewSource}
            onChange={(e) => onReplayViewSource(e.target.value as ReplayViewSource)}
          >
            <option value="smooth">Smooth preview</option>
            <option value="preserve_holds">Preserve holds</option>
            <option value="raw">Raw physics</option>
          </select>
        </label>
        <label className="flex items-center gap-1 text-slate-600">
          Step mode
          <select
            className="rounded border border-slate-300 bg-white px-1 py-0.5"
            value={playbackMode}
            onChange={(e) => onPlaybackMode(e.target.value as PlaybackMode)}
          >
            <option value="every_frame">Every frame</option>
            <option value="realtime">Realtime</option>
          </select>
        </label>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(0, totalFrames - 1)}
        value={frameIndex}
        disabled={totalFrames === 0}
        className="w-full accent-[#FF6A1A]"
        onChange={(e) => onScrub(Number(e.target.value))}
      />
    </div>
  );
}
