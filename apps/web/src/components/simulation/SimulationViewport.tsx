"use client";

import { Canvas } from "@react-three/fiber";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSimStore } from "@/lib/state";
import { ViewportHud } from "./ViewportHud";
import { RobotDogScene } from "./RobotDogScene";

type InputState = {
  forward: boolean;
  backward: boolean;
  left: boolean;
  right: boolean;
  jump: boolean;
  stop: boolean;
  resetTick: number;
};

function isTextInputTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName.toLowerCase();
  return target.isContentEditable || tag === "input" || tag === "textarea" || tag === "select";
}

export function SimulationViewport() {
  const setupError = useSimStore((s) => s.setupError);
  const manifest = useSimStore((s) => s.manifest);
  const projectId = useSimStore((s) => s.selectedProjectId);
  const controlMode = useSimStore((s) => s.controlMode);
  const viewMode = useSimStore((s) => s.viewMode);
  const setCurrentCommand = useSimStore((s) => s.setCurrentCommand);
  const addLog = useSimStore((s) => s.addLog);
  const containerRef = useRef<HTMLDivElement>(null);

  const viewportMeshMode = useSimStore((s) => s.viewportMeshMode);
  const showComOverlay = useSimStore((s) => s.showComOverlay);
  const showJointAxesOverlay = useSimStore((s) => s.showJointAxesOverlay);
  const showSensorRaysOverlay = useSimStore((s) => s.showSensorRaysOverlay);
  const showWireRoutesOverlay = useSimStore((s) => s.showWireRoutesOverlay);
  const setViewportMeshMode = useSimStore((s) => s.setViewportMeshMode);
  const setShowComOverlay = useSimStore((s) => s.setShowComOverlay);
  const setShowJointAxesOverlay = useSimStore((s) => s.setShowJointAxesOverlay);
  const setShowSensorRaysOverlay = useSimStore((s) => s.setShowSensorRaysOverlay);
  const setShowWireRoutesOverlay = useSimStore((s) => s.setShowWireRoutesOverlay);
  const [showInternals, setShowInternals] = useState(false);

  const showVisualMesh = viewportMeshMode === "visual" || viewportMeshMode === "both";
  const showCollisionMesh = viewportMeshMode === "collision" || viewportMeshMode === "both";
  const showJointAxes = showJointAxesOverlay;
  const showSensorRays = showSensorRaysOverlay;
  const showWires = showWireRoutesOverlay;
  const [input, setInput] = useState<InputState>({
    forward: false,
    backward: false,
    left: false,
    right: false,
    jump: false,
    stop: false,
    resetTick: 0,
  });
  const [cameraActions, setCameraActions] = useState<{
    reset: () => void;
    frame: () => void;
    top: () => void;
    front: () => void;
    side: () => void;
  }>({
    reset: () => {},
    frame: () => {},
    top: () => {},
    front: () => {},
    side: () => {},
  });

  const hasGenesis = !setupError?.toLowerCase().includes("genesis");
  const genesisMissing = !hasGenesis;
  const lastRun = useSimStore((s) => s.lastRun);
  const runTimeseries = useSimStore((s) => s.runTimeseries);
  const genesisReplayActive = Boolean(lastRun?.genesis_used && !lastRun?.mocked && runTimeseries.length > 0);
  const replayLabel = genesisReplayActive ? "Genesis Replay" : lastRun && !lastRun.genesis_used ? "No Genesis state replay available" : "Frontend Preview";
  const remoteControlEnabled = (manifest?.project_type ?? "generic") === "robot_dog" && controlMode === "remote_control";

  const keyMap = useMemo(
    () => ({
      w: "forward",
      s: "backward",
      a: "left",
      d: "right",
      " ": "jump",
      escape: "stop",
      r: "reset",
    }),
    []
  );

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (isTextInputTarget(event.target)) return;
      const key = event.key.toLowerCase();
      const action = keyMap[key as keyof typeof keyMap];
      if (!action || !remoteControlEnabled) return;
      event.preventDefault();

      if (action === "reset") {
        setInput((prev) => ({ ...prev, forward: false, backward: false, left: false, right: false, jump: false, stop: false, resetTick: prev.resetTick + 1 }));
        setCurrentCommand("reset");
        addLog("[Preview] Reset pose.");
        return;
      }
      if (action === "stop") {
        setInput((prev) => ({ ...prev, forward: false, backward: false, left: false, right: false, jump: false, stop: true }));
        setCurrentCommand("emergency_stop");
        return;
      }
      setInput((prev) => ({ ...prev, [action]: true, stop: false }));
      setCurrentCommand(action);
    }

    function onKeyUp(event: KeyboardEvent) {
      if (isTextInputTarget(event.target)) return;
      const key = event.key.toLowerCase();
      const action = keyMap[key as keyof typeof keyMap];
      if (!action || action === "reset" || action === "stop" || !remoteControlEnabled) return;
      setInput((prev) => ({ ...prev, [action]: false, jump: action === "jump" ? false : prev.jump }));
    }

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    return () => {
      window.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("keyup", onKeyUp);
    };
  }, [addLog, keyMap, remoteControlEnabled, setCurrentCommand]);

  const registerCameraActions = useCallback((actions: typeof cameraActions) => {
    setCameraActions(actions);
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const ro = new ResizeObserver(() => {
      useSimStore.getState().bumpViewportResize();
    });
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  const debugOverlays = viewMode === "debug";

  return (
    <div ref={containerRef} className="absolute inset-0 overflow-hidden rounded border border-slate-500 bg-slate-100">
      <Canvas
        key={`canvas-${projectId}`}
        shadows
        gl={{ antialias: true }}
        dpr={[1, 2]}
        style={{ width: "100%", height: "100%", display: "block" }}
        onPointerMissed={() => useSimStore.getState().setSelectedPartId(null)}
      >
        <RobotDogScene
          projectMode={manifest?.project_mode ?? "default_demo"}
          projectType={manifest?.project_type ?? "generic"}
          projectId={projectId}
          input={input}
          showVisualMesh={(showVisualMesh && viewMode !== "debug") || debugOverlays}
          showCollisionMesh={showCollisionMesh || debugOverlays}
          showJointAxes={showJointAxes || debugOverlays}
          showSensorRays={showSensorRays || debugOverlays}
          showComOverlay={showComOverlay || debugOverlays}
          showWires={showWires}
          showInternals={showInternals}
          registerCameraActions={registerCameraActions}
        />
      </Canvas>

      <ViewportHud
        genesisMissing={genesisMissing}
        replayLabel={replayLabel}
        meshMode={viewportMeshMode}
        showCom={showComOverlay}
        showJointAxes={showJointAxesOverlay}
        showSensorRays={showSensorRaysOverlay}
        showWires={showWireRoutesOverlay}
        onMeshModeChange={setViewportMeshMode}
        onToggleCom={() => setShowComOverlay(!showComOverlay)}
        onToggleJointAxes={() => setShowJointAxesOverlay(!showJointAxesOverlay)}
        onToggleSensorRays={() => setShowSensorRaysOverlay(!showSensorRaysOverlay)}
        onToggleWires={() => setShowWireRoutesOverlay(!showWireRoutesOverlay)}
        onResetCamera={cameraActions.reset}
        onFrameModel={cameraActions.frame}
        onTopView={cameraActions.top}
        onFrontView={cameraActions.front}
        onSideView={cameraActions.side}
      />
    </div>
  );
}
