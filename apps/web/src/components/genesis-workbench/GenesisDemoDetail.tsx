"use client";



import { useRef, useState } from "react";

import { isTransientPollError } from "@/lib/pollUtils";

import {
  getShowcaseLaunchLogs,

  getShowcaseLaunchStatus,

  getShowcaseLaunchTelemetry,

  getShowcaseLaunchTimeseries,

  launchShowcaseDemo,

  type ShowcaseCatalogEntry,

} from "@/lib/genesisWorkbenchApi";
import { normalizeReplay, normalizeTelemetryBundle, type ReplayBundle, type ReplayViewSource } from "./replay/types";

type Props = {
  entry: ShowcaseCatalogEntry | null;
  launchProjectId: string;
  onLog: (msg: string) => void;
  onReplay: (replay: ReplayBundle | null) => void;
  onLifecycle: (lifecycle: string | null) => void;
  onLaunchFailure?: (failure: import("./LaunchFailureModal").LaunchFailureInfo | null) => void;
  variant?: "default" | "sidebar";
};



const TERMINAL = new Set(["completed", "failed", "unknown"]);



const LIFECYCLE_LABEL: Record<string, string> = {

  idle: "Idle",

  launching: "Launching",

  running: "Running",

  receiving_frames: "Receiving frames",

  completed: "Completed",

  failed: "Failed",

};



export function GenesisDemoDetail({

  entry,

  launchProjectId,

  onLog,

  onReplay,

  onLifecycle,

  onLaunchFailure,

  variant = "default",

}: Props) {

  const [launching, setLaunching] = useState(false);

  const [launchId, setLaunchId] = useState<string | null>(null);

  const [lifecycle, setLifecycle] = useState<string | null>(null);

  const pollRef = useRef(0);
  const logOffsetRef = useRef({ stdout: 0, stderr: 0 });
  const lastFrameCountRef = useRef(0);
  const lastTelemetryCountRef = useRef(0);
  const lastReplayVersionRef = useRef(0);

  const isRunning = lifecycle === "launching" || lifecycle === "running" || lifecycle === "receiving_frames";



  function setLifecycleState(next: string | null) {

    setLifecycle(next);

    onLifecycle(next);

  }



  function shouldReloadReplay(replayVersion: number): boolean {
    if (replayVersion > lastReplayVersionRef.current) {
      lastReplayVersionRef.current = replayVersion;
      return true;
    }
    return false;
  }



  function resetLaunch() {

    pollRef.current += 1;

    setLaunchId(null);

    setLifecycleState("idle");

    setLaunching(false);

    logOffsetRef.current = { stdout: 0, stderr: 0 };
    lastFrameCountRef.current = 0;
    lastTelemetryCountRef.current = 0;
    lastReplayVersionRef.current = 0;

    onReplay(null);

    onLog("[Launch] Reset — you can run again.");

  }



  async function loadReplay(id: string, force = false, expectedFrames = 0) {
    const fetchTimeseries = () => getShowcaseLaunchTimeseries(launchProjectId, id);

    const applyBundle = async (data: Awaited<ReturnType<typeof fetchTimeseries>>) => {
      const demoType = String((data.meta as Record<string, unknown> | undefined)?.demo_type ?? entry?.demo_type ?? "");
      const viewSource: ReplayViewSource =
        demoType === "telemetry" || demoType === "hybrid" ? "raw" : "smooth";
      let bundle = normalizeReplay(
        {
          launch_id: data.launch_id,
          project_id: launchProjectId,
          scene: data.scene,
          objects: data.objects as Parameters<typeof normalizeReplay>[0]["objects"],
          state_timeseries: data.state_timeseries as Parameters<typeof normalizeReplay>[0]["state_timeseries"],
          raw_frames: data.raw_frames as Parameters<typeof normalizeReplay>[0]["raw_frames"],
          preview_frames: data.preview_frames as Parameters<typeof normalizeReplay>[0]["preview_frames"],
          telemetry: data.telemetry as Parameters<typeof normalizeReplay>[0]["telemetry"],
          meta: data.meta,
        },
        launchProjectId,
        id,
        viewSource,
      );

      const metaTeleCount = Number(bundle.meta.telemetry_sample_count ?? 0);
      const teleCount = bundle.telemetry?.timestamps?.length ?? 0;
      const isSensorDemo = demoType === "telemetry" || demoType === "hybrid";
      if (isSensorDemo && teleCount === 0 && (metaTeleCount > 0 || force)) {
        try {
          const telePayload = await getShowcaseLaunchTelemetry(launchProjectId, id);
          const resolved = normalizeTelemetryBundle(telePayload.telemetry);
          if (resolved?.timestamps?.length) {
            bundle = { ...bundle, telemetry: resolved };
          }
        } catch {
          /* telemetry endpoint may not exist until API restart */
        }
      }

      const frameCount = bundle.frames.length;
      const resolvedTeleCount = bundle.telemetry?.timestamps?.length ?? 0;
      if (
        !force &&
        frameCount > 0 &&
        frameCount <= lastFrameCountRef.current &&
        resolvedTeleCount <= lastTelemetryCountRef.current
      ) {
        return frameCount;
      }
      if (frameCount > lastFrameCountRef.current || resolvedTeleCount > lastTelemetryCountRef.current || force) {
        lastFrameCountRef.current = Math.max(lastFrameCountRef.current, frameCount);
        lastTelemetryCountRef.current = Math.max(lastTelemetryCountRef.current, resolvedTeleCount);
        onReplay(bundle);
        const diag = (bundle.meta.diagnostics ?? {}) as Record<string, unknown>;
        const motion = (bundle.meta.motion_diagnostics ?? {}) as Record<string, unknown>;
        const rawCount = Number(bundle.meta.source_frame_count ?? bundle.rawFrames.length ?? frameCount);
        const previewCount = Number(bundle.meta.preview_frame_count ?? bundle.previewFrames.length ?? 0);
        const uniquePoses = Number(bundle.meta.unique_pose_count ?? motion.unique_pose_count ?? 0);
        const longestFreeze = Number(motion.longest_freeze_run ?? 0);
        const recorderIssue = String(motion.recorder_issue ?? bundle.meta.recorder_issue ?? "");
        const previewMeta = (bundle.meta.preview_meta ?? {}) as Record<string, unknown>;
        const trimInfo = (previewMeta.trim_info ?? {}) as Record<string, unknown>;
        if (Number(trimInfo.frozen_head_length ?? 0) > 0) {
          onLog(`[Launch] Trimmed frozen head: ${String(trimInfo.frozen_head_length)} frames`);
        }
        if (Number(trimInfo.frozen_tail_length ?? 0) > 0) {
          onLog(`[Launch] Trimmed frozen tail: ${String(trimInfo.frozen_tail_length)} frames`);
        }
        if (Number(trimInfo.collapsed_frames ?? 0) > 0) {
          onLog(`[Launch] Collapsed interior frozen frames: ${String(trimInfo.collapsed_frames)}`);
        }
        const trimLog = trimInfo.trim_log;
        if (Array.isArray(trimLog)) {
          for (const line of trimLog) {
            if (typeof line === "string" && line.trim()) onLog(`[Launch] ${line}`);
          }
        }
        const demoType = String(bundle.meta.demo_type ?? "motion");
        const teleCount = Number(bundle.meta.telemetry_sample_count ?? bundle.telemetry?.timestamps?.length ?? 0);
        if (demoType !== "motion" || teleCount > 0) {
          onLog(
            `[Launch] demo_type=${demoType} visual_raw=${rawCount} telemetry_samples=${teleCount} playback=${frameCount}`,
          );
        }
        if (frameCount > 0) {
          onLog(
            `[Launch] Web replay loaded (${frameCount} playback frames, ${rawCount} raw, ${previewCount || frameCount} preview, ${bundle.objects.length} objects, ${String(diag.robot_links ?? 0)} robot links).`,
          );
          if (uniquePoses > 0) {
            onLog(
              `[Launch] Replay diagnostics: ${rawCount} raw frames, ${uniquePoses} unique poses, longest freeze ${longestFreeze} frames, issue=${recorderIssue || "none"}.`,
            );
          }
          if (recorderIssue === "repeated_transforms" || recorderIssue === "upstream_demo_hold" || recorderIssue === "sparse_motion_phases") {
            onLog(
              "[Launch] Recorder captured sparse or repeated motion; smooth preview is enabled by default.",
            );
          }
          const motionLink =
            (typeof motion.primary_motion_link === "string" && motion.primary_motion_link) ||
            bundle.objects.find((o) => o.type === "robot_link")?.id;
          if (motionLink) {
            const rawBundle = normalizeReplay(
              data as unknown as Parameters<typeof normalizeReplay>[0],
              launchProjectId,
              id,
              "raw",
            );
            let distinctRaw = 0;
            let prev: string | null = null;
            for (const frame of rawBundle.frames) {
              const tr = frame.transforms?.[motionLink];
              const key = tr ? JSON.stringify(tr) : null;
              if (key !== prev) {
                distinctRaw += 1;
                prev = key;
              }
            }
            let distinctPreview = 0;
            prev = null;
            for (const frame of bundle.frames) {
              const tr = frame.transforms?.[motionLink];
              const key = tr ? JSON.stringify(tr) : null;
              if (key !== prev) {
                distinctPreview += 1;
                prev = key;
              }
            }
            onLog(
              `[Launch] Motion check (${motionLink}): raw ${distinctRaw} distinct poses in ${rawCount} frames; preview ${distinctPreview} distinct in ${frameCount} frames.`,
            );
          }
        }
      }
      return frameCount;
    };

    try {
      return await applyBundle(await fetchTimeseries());
    } catch {
      if (expectedFrames > 0) {
        await new Promise((r) => setTimeout(r, 350));
        try {
          return await applyBundle(await fetchTimeseries());
        } catch {
          return 0;
        }
      }
      return 0;
    }
  }



  async function pollLogs(id: string) {

    try {

      const logs = await getShowcaseLaunchLogs(launchProjectId, id);

      const { stdout, stderr } = logs;

      if (stdout.length > logOffsetRef.current.stdout) {

        const chunk = stdout.slice(logOffsetRef.current.stdout);

        logOffsetRef.current.stdout = stdout.length;

        for (const line of chunk.split(/\r?\n/)) {

          if (line.trim()) onLog(`[stdout] ${line}`);

        }

      }

      if (stderr.length > logOffsetRef.current.stderr) {

        const chunk = stderr.slice(logOffsetRef.current.stderr);

        logOffsetRef.current.stderr = stderr.length;

        for (const line of chunk.split(/\r?\n/)) {

          if (line.trim()) onLog(`[stderr] ${line}`);

        }

      }

    } catch {

      /* logs not ready yet */

    }

  }



  async function pollStatus(id: string, pollToken: number) {

    for (let i = 0; i < 240; i++) {

      if (pollRef.current !== pollToken) return;

      await new Promise((r) => setTimeout(r, i === 0 ? 600 : 1200));

      if (pollRef.current !== pollToken) return;

      try {

        await pollLogs(id);

        const status = await getShowcaseLaunchStatus(launchProjectId, id);

        if (pollRef.current !== pollToken) return;

        const nextLifecycle = String(status.lifecycle ?? status.status ?? "running");

        setLifecycleState(nextLifecycle);

        if (status.replay_available || Number(status.replay_frames) > 0) {
          const replayVersion = Number(status.replay_version ?? 0);
          const replayReady = status.replay_ready !== false;
          const replayPartial = status.replay_partial === true;
          const terminal = TERMINAL.has(String(status.status));
          if ((replayReady || replayPartial) && (shouldReloadReplay(replayVersion) || terminal)) {
            await loadReplay(id, terminal, Number(status.replay_frames));
          }
        }

        if (Number(status.replay_robot_links) > 0) {

          onLog(`[Launch] Robot links in replay: ${String(status.replay_robot_links)}`);

        }

        if (Number(status.replay_tracked_objects) > 0) {

          onLog(`[Launch] Tracked objects: ${String(status.replay_tracked_objects)}`);

        }

        if (status.status === "failed") {
          await pollLogs(id);
          let logTail = "";
          try {
            const logPayload = await getShowcaseLaunchLogs(launchProjectId, id);
            logTail = [logPayload.stderr, logPayload.stdout].filter(Boolean).join("\n").trim();
          } catch {
            /* logs optional */
          }
          const detail = String(
            status.failure_detail ?? status.error_summary ?? logTail.slice(-2000) ?? "Launch failed",
          );
          onLog(`[Launch][Error] ${detail}`);
          onLaunchFailure?.({
            title: `Launch failed: ${entry?.demo_name ?? "demo"}`,
            scriptPath: entry?.script_path,
            failureCode: status.failure_code ? String(status.failure_code) : null,
            failureDetail: detail,
            suggestedFix: status.suggested_fix ? String(status.suggested_fix) : null,
            logs: logTail || undefined,
          });
        }

        if (status.opengl_hint) {

          onLog(`[Launch][Hint] ${String(status.opengl_hint)}`);

        }

        if (TERMINAL.has(String(status.status))) {

          await pollLogs(id);

          onLog(

            `[Launch] ${id} → ${status.status}${status.exit_code != null ? ` (exit ${status.exit_code})` : ""}`,

          );

          if (status.status === "completed") {
            const frames = await loadReplay(id, true);

            if (frames === 0) {

              onLog("[Launch][Error] Simulation finished but no replay frames were recorded.");

              setLifecycleState("failed");

            }

          }

          return;

        }

      } catch (error) {

        const msg = (error as Error).message;

        if (isTransientPollError(msg)) {

          onLog(`[Launch][Poll] ${msg} — simulation still running, retrying…`);

          continue;

        }

        onLog(`[Launch][Poll] ${msg}`);

        setLifecycleState("failed");

        return;

      }

    }

    if (pollRef.current !== pollToken) return;

    setLifecycleState("failed");

    onLog("[Launch] Timed out — use Reset if the button is stuck.");

  }



  async function onLaunch() {

    if (!entry || launching || isRunning) return;

    setLaunching(true);

    setLifecycleState("launching");

    onReplay(null);
    lastFrameCountRef.current = 0;
    lastTelemetryCountRef.current = 0;
    lastReplayVersionRef.current = 0;
    logOffsetRef.current = { stdout: 0, stderr: 0 };

    pollRef.current += 1;

    const pollToken = pollRef.current;

    try {

      const result = await launchShowcaseDemo(launchProjectId, entry.scenario_id, { viewMode: "web" });

      setLaunchId(result.launch_id);

      setLifecycleState(String(result.lifecycle ?? result.status ?? "running"));

      onLog(`[Launch] ${entry.demo_name} · web viewer`);

      onLog(`[Launch] id=${result.launch_id}`);

      onLog(`[Launch] ${result.note}`);

      if (Array.isArray(result.argv)) {

        onLog(`[Launch] argv=${result.argv.join(" ")}`);

      }

      void pollStatus(result.launch_id, pollToken);

    } catch (error) {

      onLog(`[Launch][Error] ${(error as Error).message}`);

      setLifecycleState("failed");

    } finally {

      setLaunching(false);

    }

  }



  if (!entry) {

    return <div className="text-sm text-slate-600">Select a demo simulation from the left.</div>;

  }

  const isSidebar = variant === "sidebar";



  const btn = "rounded border border-slate-300 bg-slate-100 px-3 py-1.5 text-xs font-medium hover:bg-slate-200 disabled:opacity-40";

  const primary = "rounded bg-[#FF6A1A] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#e55f15] disabled:opacity-40";

  const lifecycleLabel = lifecycle ? (LIFECYCLE_LABEL[lifecycle] ?? lifecycle) : null;



  return (

    <div className={`space-y-4 ${isSidebar ? "text-xs" : ""}`}>

      <div>

        <h1 className={`font-semibold text-slate-900 ${isSidebar ? "text-sm" : "text-lg"}`}>{entry.demo_name}</h1>

        <p className="mt-1 text-[11px] text-slate-600 capitalize">{entry.layer.replace(/-/g, " ")}</p>

      </div>



      <div className="rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
        <p className="font-medium text-slate-900">Web viewer</p>
        <p className="mt-1 text-slate-600">
          Physics runs in the background; motion and sensor data play in the center panel. Works on AMD and NVIDIA GPUs.
        </p>
      </div>



      <div className="flex flex-wrap gap-2">

        <button

          type="button"

          className={primary}

          disabled={!entry.available || launching || isRunning}

          onClick={() => void onLaunch()}

        >

          {launching ? "Starting…" : isRunning ? "Simulation running…" : "Run demo"}

        </button>

        {launchId ? (

          <button type="button" className={btn} onClick={resetLaunch}>

            Reset

          </button>

        ) : null}

      </div>



      {launchId ? (

        <div className="rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">

          Launch ID: {launchId}

          {lifecycleLabel ? ` · ${lifecycleLabel}` : null}

          {lifecycle === "running" ? (

            <p className="mt-2 text-slate-600">Compiling/running — replay appears in the viewer when frames arrive (1–2 min first time).</p>

          ) : null}

          {lifecycle === "receiving_frames" ? (

            <p className="mt-2 text-[#c2410c]">Frames streaming — check the web viewer on the right.</p>

          ) : null}

          {lifecycle === "completed" ? (

            <p className="mt-2 text-[#c2410c]">Done — animation should be playing in the web viewer.</p>

          ) : null}

          {lifecycle === "failed" ? (

            <p className="mt-2 text-red-700">Failed — scroll the session log below for the full error.</p>

          ) : null}

        </div>

      ) : null}



      {!entry.available && entry.missing.length > 0 ? (
        <ul className="list-disc space-y-1 rounded border border-amber-200 bg-amber-50 p-3 pl-5 text-xs text-amber-800">
          {entry.missing.map((m) => (
            <li key={m}>{m}</li>
          ))}
        </ul>
      ) : null}

    </div>

  );

}

