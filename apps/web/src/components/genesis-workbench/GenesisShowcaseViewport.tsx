"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { analyzeReplayMotion, checkMotionAfterFrame, warnStalePreviewTail } from "./replay/replay_diagnostics";
import {
  clampFrameIndex,
  DEFAULT_PLAYBACK_FPS,
  frameIndexForRealtime,
  frameIndexForTelemetryTime,
  playbackTimeAtFrame,
  type PlaybackMode,
  tickEveryFramePlayback,
} from "./replay/replay_playback";
import { ReplayControls } from "./replay/ReplayControls";
import { ReplayDebugOverlay } from "./replay/ReplayDebugOverlay";
import { normalizeReplay, type ReplayBundle, type ReplayViewSource } from "./replay/types";
import { GenesisHorizontalSplit } from "./GenesisWorkbenchLayout";
import { JointControlPanel } from "./gui/JointControlPanel";
import { accent } from "./buildablesTheme";
import { resolveSensorRenderer } from "./telemetry/renderers";

const ReplayCanvasInner = dynamic(
  () => import("./replay/ReplayCanvasInner").then((m) => m.ReplayCanvasInner),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full items-center justify-center bg-slate-100 text-xs text-slate-600">Loading 3D viewer…</div>
    ),
  },
);

type Props = {
  replay: ReplayBundle | null;
  lifecycle?: string | null;
  replayComplete?: boolean;
  demoType?: string | null;
  catalogKind?: string | null;
  sensorType?: string | null;
  /** Agentic execution run id — clears stale replay when changed */
  runId?: string | null;
};

export function GenesisShowcaseViewport({
  replay,
  lifecycle,
  replayComplete = true,
  demoType,
  catalogKind,
  sensorType,
  runId = null,
}: Props) {
  const [playing, setPlaying] = useState(false);
  const [frameIndex, setFrameIndex] = useState(0);
  const [speed, setSpeed] = useState(1);
  const [playbackFps, setPlaybackFps] = useState(DEFAULT_PLAYBACK_FPS);
  const [playbackMode, setPlaybackMode] = useState<PlaybackMode>("every_frame");
  const [replayViewSource, setReplayViewSource] = useState<ReplayViewSource>("smooth");
  const [showDebugOverlay, setShowDebugOverlay] = useState(() => {
    if (typeof window === "undefined") return false;
    return (
      new URLSearchParams(window.location.search).get("debug") === "1" ||
      process.env.NEXT_PUBLIC_REPLAY_DEBUG === "1"
    );
  });
  const [fitCameraToken, setFitCameraToken] = useState(0);

  const accumRef = useRef(0);
  const elapsedRef = useRef(0);
  const rafRef = useRef<number | null>(null);
  const lastTickRef = useRef<number | null>(null);
  const frameIndexRef = useRef(0);

  const bundle = useMemo(() => {
    if (!replay) return null;
    const demoTypeHint = String(demoType ?? replay.meta?.demo_type ?? "");
    const viewSource =
      replay.viewSource ??
      (demoTypeHint === "telemetry" || demoTypeHint === "hybrid" ? "raw" : replayViewSource);
    return normalizeReplay(
      {
        launch_id: replay.launchId,
        project_id: replay.projectId,
        scene: replay.scene,
        objects: replay.objects,
        raw_frames: replay.rawFrames,
        preview_frames: replay.previewFrames,
        telemetry: replay.telemetry ?? undefined,
        meta: replay.meta,
      },
      replay.projectId,
      replay.launchId,
      viewSource === "smooth" || viewSource === "raw" || viewSource === "preserve_holds"
        ? viewSource
        : replayViewSource,
    );
  }, [replay, replayViewSource, demoType]);

  const totalFrames = bundle?.frames.length ?? 0;
  const safeFrameIndex = clampFrameIndex(frameIndex, totalFrames);
  frameIndexRef.current = safeFrameIndex;
  const telemetry = bundle?.telemetry ?? null;
  const telemetryTimestamps = telemetry?.timestamps;
  const resolvedCatalogKind = String(
    catalogKind ?? replay?.meta?.kind ?? bundle?.meta?.kind ?? "",
  );
  const resolvedSensorType = String(
    sensorType ?? replay?.meta?.sensor_type ?? bundle?.meta?.sensor_type ?? "",
  ) || null;
  const manifestTelemetry = Boolean(
    (replay?.meta?.manifest as { telemetry?: { hasTelemetry?: boolean } } | undefined)?.telemetry
      ?.hasTelemetry,
  );
  const isAgenticRun = Boolean(runId || replay?.meta?.agentic_run_id);
  const hasTelemetryData = Boolean(
    telemetry?.timestamps?.length ||
      telemetry?.samples?.length ||
      (telemetry?.channels && Object.keys(telemetry.channels).length > 0),
  );
  const showSensorSplit =
    resolvedSensorType !== "lidar" &&
    ((!isAgenticRun && resolvedCatalogKind === "sensor") ||
      (isAgenticRun && hasTelemetryData && (manifestTelemetry || hasTelemetryData)));
  const showGuiPanel = resolvedCatalogKind === "gui";
  const SensorPanel = resolveSensorRenderer(resolvedSensorType);
  const currentPlaybackTime = useMemo(() => {
    if (!bundle) return 0;
    return playbackTimeAtFrame({
      frames: bundle.frames,
      frameIndex: safeFrameIndex,
      telemetryTimestamps,
    });
  }, [bundle, safeFrameIndex, telemetryTimestamps]);
  const hasReplay =
    totalFrames > 0 &&
    (replayComplete || lifecycle === "receiving_frames" || (showSensorSplit && lifecycle === "running"));

  const motionAnalysis = useMemo(() => {
    if (!bundle || bundle.frames.length === 0) return null;
    const ids = bundle.objects.filter((o) => o.type === "robot_link").map((o) => o.id);
    return analyzeReplayMotion(bundle.frames, ids);
  }, [bundle]);

  const sampleObjectId = motionAnalysis?.sampledObjectId ?? null;

  const resetPlaybackState = useCallback(() => {
    setFrameIndex(0);
    setPlaying(false);
    setFitCameraToken(0);
    accumRef.current = 0;
    elapsedRef.current = 0;
    lastTickRef.current = null;
  }, []);

  useEffect(() => {
    if (!bundle) return;
    const sceneFps = bundle.scene.playback_fps;
    const metaFps = bundle.meta.playback_fps;
    const next =
      typeof sceneFps === "number" && sceneFps > 0
        ? sceneFps
        : typeof metaFps === "number" && metaFps > 0
          ? metaFps
          : DEFAULT_PLAYBACK_FPS;
    setPlaybackFps(next);
  }, [bundle?.launchId, bundle?.scene.playback_fps, bundle?.meta.playback_fps]);

  useEffect(() => {
    if (!bundle?.launchId) return;
    resetPlaybackState();
  }, [bundle?.launchId, runId, replayViewSource, resetPlaybackState]);

  useEffect(() => {
    if (!bundle) return;
    warnStalePreviewTail(bundle);
  }, [bundle?.launchId, bundle?.meta.preview_validation]);

  useEffect(() => {
    if (totalFrames > 0 && frameIndex >= totalFrames) {
      setFrameIndex(totalFrames - 1);
    }
  }, [frameIndex, totalFrames]);

  useEffect(() => {
    if (!playing || !hasReplay || !bundle) {
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      lastTickRef.current = null;
      return;
    }

    const tick = (now: number) => {
      const last = lastTickRef.current ?? now;
      lastTickRef.current = now;
      const delta = Math.min(0.1, Math.max(0, (now - last) / 1000));

      if (playbackMode === "every_frame") {
        const result = tickEveryFramePlayback({
          frameIndex: frameIndexRef.current,
          deltaSeconds: delta,
          accumulator: accumRef.current,
          playbackFps,
          speed,
          totalFrames,
          loop: true,
        });
        accumRef.current = result.accumulator;
        if (result.advanced) {
          frameIndexRef.current = result.frameIndex;
          setFrameIndex(result.frameIndex);
        }
      } else {
        elapsedRef.current += delta;
        const idx = frameIndexForRealtime({
          elapsedSeconds: elapsedRef.current,
          frames: bundle.frames,
          speed,
          loop: true,
          telemetryTimestamps,
        });
        if (idx !== frameIndexRef.current) {
          frameIndexRef.current = idx;
          setFrameIndex(idx);
        }
      }

      rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => {
      if (rafRef.current != null) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      lastTickRef.current = null;
    };
  }, [playing, hasReplay, bundle, playbackMode, playbackFps, speed, totalFrames, telemetryTimestamps]);

  function setFrameClamped(idx: number) {
    const clamped = clampFrameIndex(idx, totalFrames);
    frameIndexRef.current = clamped;
    setFrameIndex(clamped);
  }

  function handleRestart() {
    accumRef.current = 0;
    elapsedRef.current = 0;
    setFrameClamped(0);
    setPlaying(true);
  }

  function handleStep(delta: number) {
    setPlaying(false);
    setFrameClamped(safeFrameIndex + delta);
  }

  const rawCount = Number(bundle?.meta.source_frame_count ?? replay?.rawFrames.length ?? 0);
  const uniquePoses = Number(bundle?.meta.unique_pose_count ?? replay?.meta.unique_pose_count ?? 0);

  const statusLabel = !hasReplay
    ? !replayComplete && (lifecycle === "running" || lifecycle === "receiving_frames")
      ? "Recording frames…"
      : lifecycle === "launching"
        ? "Launching…"
        : replay && totalFrames > 0 && !replayComplete
          ? "Waiting for final replay…"
          : "Run a demo to see motion here"
    : playing
      ? `Playing · frame ${safeFrameIndex + 1} / ${totalFrames} · ${replayViewSource === "smooth" ? "smooth" : replayViewSource === "preserve_holds" ? "holds" : "raw"}`
      : rawCount > 0 && uniquePoses > 0 && uniquePoses < rawCount
        ? `${rawCount} raw · ${uniquePoses} unique poses · ${totalFrames} ${replayViewSource} frames`
        : `Frame ${safeFrameIndex + 1} / ${totalFrames}`;

  function handleScrubTelemetryTime(time: number) {
    if (!bundle) return;
    setPlaying(false);
    accumRef.current = 0;
    elapsedRef.current = time;
    const idx = frameIndexForTelemetryTime({ frames: bundle.frames, time });
    setFrameClamped(idx);
  }

  const viewerBody = (
    <div className="flex h-full min-h-0 flex-col">
      <div className="relative min-h-0 flex-1">
        {hasReplay && bundle ? (
          <>
            <ReplayCanvasInner
              replay={bundle}
              frameIndex={safeFrameIndex}
              fitCameraToken={fitCameraToken}
              sampleObjectId={sampleObjectId}
              debugMode={showDebugOverlay}
            />
          </>
        ) : (
          <div className="flex h-full items-center justify-center p-4 text-center text-xs text-slate-500">
            {lifecycle === "running" || lifecycle === "launching" || lifecycle === "receiving_frames" ? (
              <span>Compiling physics and recording link transforms… final replay plays when recording completes.</span>
            ) : (
              <span>Physics runs in the background. Robot links and objects render here — no native OpenGL window.</span>
            )}
          </div>
        )}
      </div>
      {hasReplay && bundle && showDebugOverlay ? (
        <ReplayDebugOverlay
          replay={bundle}
          frameIndex={safeFrameIndex}
          playing={playing}
          playbackMode={playbackMode}
          replayViewSource={replayViewSource}
          distinctVisualStates={motionAnalysis?.distinctVisualStates ?? null}
          usingFallback={Boolean(bundle.scene?.franka_fallback)}
          variant="panel"
        />
      ) : null}
      {hasReplay ? (
        <ReplayControls
          playing={playing}
          frameIndex={safeFrameIndex}
          totalFrames={totalFrames}
          speed={speed}
          playbackFps={playbackFps}
          playbackMode={playbackMode}
          replayViewSource={replayViewSource}
          showDebugOverlay={showDebugOverlay}
          onToggleDebugOverlay={() => setShowDebugOverlay((v) => !v)}
          onCheckMotionAfterFrame={() => {
            if (!bundle) return;
            const ids = bundle.objects.filter((o) => o.type === "robot_link").map((o) => o.id);
            const result = checkMotionAfterFrame(bundle.frames, ids, safeFrameIndex, 10);
            console.info("[replay-diagnostics] motion after frame", safeFrameIndex, result);
          }}
          onPlayPause={() => setPlaying((p) => !p)}
          onRestart={handleRestart}
          onStepBack={() => handleStep(-1)}
          onStepForward={() => handleStep(1)}
          onFitCamera={() => setFitCameraToken((t) => t + 1)}
          onScrub={(idx) => {
            setPlaying(false);
            accumRef.current = 0;
            if (bundle?.frames[idx]) {
              elapsedRef.current = bundle.frames[idx].t ?? 0;
            }
            setFrameClamped(idx);
          }}
          onSpeed={setSpeed}
          onPlaybackFps={setPlaybackFps}
          onPlaybackMode={setPlaybackMode}
          onReplayViewSource={setReplayViewSource}
        />
      ) : null}
    </div>
  );

  return (
    <div
      data-testid="replay-viewer"
      className="flex h-full min-h-[320px] flex-col rounded border border-slate-200 bg-slate-100"
    >
      <div className="flex items-center justify-between border-b border-slate-200 px-3 py-2 text-xs text-slate-700">
        <span className={`font-medium ${accent}`}>Web simulation viewer</span>
        <span data-testid="replay-viewer-status" data-viewport-status={statusLabel} className="text-slate-500">
          <span data-testid="viewport-run-status">{statusLabel}</span>
        </span>
      </div>
      {showSensorSplit ? (
        <GenesisHorizontalSplit
          storageKey="catalogue-viewer-telemetry"
          defaultLeft={55}
          left={viewerBody}
          right={
            <div data-testid="telemetry-panel" className="h-full">
              <SensorPanel
                telemetry={telemetry}
                currentTime={currentPlaybackTime}
                frameIndex={safeFrameIndex}
                onScrubTime={handleScrubTelemetryTime}
                className="h-full border-l border-slate-200"
                emptyMessage={
                  lifecycle === "running" || lifecycle === "receiving_frames" || lifecycle === "launching"
                    ? "Collecting sensor telemetry samples…"
                    : "No telemetry samples recorded for this run."
                }
                sensorType={resolvedSensorType ?? undefined}
              />
            </div>
          }
        />
      ) : showGuiPanel ? (
        <GenesisHorizontalSplit
          storageKey="catalogue-viewer-gui"
          defaultLeft={70}
          left={viewerBody}
          right={<JointControlPanel replay={bundle} frameIndex={safeFrameIndex} />}
        />
      ) : (
        <div className="flex min-h-0 flex-1 flex-col">{viewerBody}</div>
      )}
    </div>
  );
}
