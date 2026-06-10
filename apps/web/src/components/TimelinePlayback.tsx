"use client";

import { useEffect } from "react";
import { clampFrameIndex, frameCount, frameRobotSummary, frameTime } from "@/lib/playback";
import { useSimStore } from "@/lib/state";

export function TimelinePlayback() {
  const series = useSimStore((s) => s.runTimeseries);
  const frameIndex = useSimStore((s) => s.playbackFrameIndex);
  const playing = useSimStore((s) => s.playbackPlaying);
  const setFrameIndex = useSimStore((s) => s.setPlaybackFrameIndex);
  const setPlaying = useSimStore((s) => s.setPlaybackPlaying);

  const count = frameCount(series);
  const frame = series[clampFrameIndex(frameIndex, count)];

  useEffect(() => {
    if (!playing || count <= 1) return;
    const id = window.setInterval(() => {
      const current = useSimStore.getState().playbackFrameIndex;
      const next = current + 1 >= count ? 0 : current + 1;
      useSimStore.getState().setPlaybackFrameIndex(next);
    }, 1000 / 30);
    return () => window.clearInterval(id);
  }, [playing, count]);

  if (count === 0) {
    return <span>No timeline yet. Run a Genesis test.</span>;
  }

  return (
    <div className="space-y-2 text-[11px]">
      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded border border-border bg-white px-2 py-0.5"
          onClick={() => setPlaying(!playing)}
        >
          {playing ? "Pause" : "Play"}
        </button>
        <button
          type="button"
          className="rounded border border-border bg-white px-2 py-0.5"
          onClick={() => {
            setPlaying(false);
            setFrameIndex(0);
          }}
        >
          Reset
        </button>
        <span className="text-textMuted">
          Frame {clampFrameIndex(frameIndex, count) + 1} / {count} · t={frameTime(frame).toFixed(3)}s
        </span>
      </div>
      <input
        type="range"
        min={0}
        max={Math.max(0, count - 1)}
        value={clampFrameIndex(frameIndex, count)}
        className="w-full"
        onChange={(e) => {
          setPlaying(false);
          setFrameIndex(Number(e.target.value));
        }}
      />
      <div className="font-mono text-[10px] text-textMuted">{frameRobotSummary(frame)}</div>
    </div>
  );
}
