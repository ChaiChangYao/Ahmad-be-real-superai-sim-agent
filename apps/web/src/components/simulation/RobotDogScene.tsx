"use client";

import { OrbitControls, PerspectiveCamera } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { useEffect, useRef } from "react";
import { useThree } from "@react-three/fiber";
import type { Group } from "three";
import { FloorGrid } from "./FloorGrid";
import { RobotDogPreview } from "./RobotDogPreview";
import { RobotArmPreview } from "./RobotArmPreview";
import { ImportedModelPreview } from "./ImportedModelPreview";
import { GenesisReplayLayer } from "./GenesisReplayLayer";
import { frameObjectInView, setCameraView } from "./cameraUtils";
import { useSimStore } from "@/lib/state";

const DEFAULT_CAMERA_POSITION: [number, number, number] = [2.8, 1.8, 3.2];
const DEFAULT_TARGET: [number, number, number] = [0, 0.45, 0];

type PreviewInput = {
  forward: boolean;
  backward: boolean;
  left: boolean;
  right: boolean;
  jump: boolean;
  stop: boolean;
  resetTick: number;
};

type RobotDogSceneProps = {
  projectMode: string;
  projectType: string;
  projectId: string;
  input: PreviewInput;
  showVisualMesh: boolean;
  showCollisionMesh: boolean;
  showJointAxes: boolean;
  showSensorRays: boolean;
  showWires: boolean;
  showInternals: boolean;
  showComOverlay?: boolean;
  registerCameraActions: (actions: {
    reset: () => void;
    frame: () => void;
    top: () => void;
    front: () => void;
    side: () => void;
  }) => void;
};

export function RobotDogScene({
  projectMode,
  projectType,
  projectId,
  input,
  showVisualMesh,
  showCollisionMesh,
  showJointAxes,
  showSensorRays,
  showWires,
  showInternals,
  showComOverlay = false,
  registerCameraActions,
}: RobotDogSceneProps) {
  const controlsRef = useRef<OrbitControlsImpl>(null);
  const modelRootRef = useRef<Group>(null);
  const { camera } = useThree();
  const runTimeseries = useSimStore((s) => s.runTimeseries);
  const lastRun = useSimStore((s) => s.lastRun);
  const viewportResizeKey = useSimStore((s) => s.viewportResizeKey);
  const showSkeleton = useSimStore((s) => s.showSkeleton);
  const viewMode = useSimStore((s) => s.viewMode);
  const genesisReplayActive = Boolean(lastRun?.genesis_used && !lastRun?.mocked && runTimeseries.length > 0);
  const debugOverlays = viewMode === "debug";

  function frameModel() {
    frameObjectInView(camera, controlsRef.current, modelRootRef.current, 45);
  }

  function resetCamera() {
    setCameraView(camera, controlsRef.current, DEFAULT_CAMERA_POSITION, DEFAULT_TARGET);
  }

  useEffect(() => {
    const timer = window.setTimeout(() => frameModel(), 80);
    return () => window.clearTimeout(timer);
  }, [projectId, projectType, projectMode, viewportResizeKey]);

  useEffect(() => {
    registerCameraActions({
      reset: resetCamera,
      frame: frameModel,
      top: () => setCameraView(camera, controlsRef.current, [0.001, 4.5, 0.001], DEFAULT_TARGET),
      front: () => setCameraView(camera, controlsRef.current, [0, 1.4, 4.0], DEFAULT_TARGET),
      side: () => setCameraView(camera, controlsRef.current, [4.0, 1.3, 0], DEFAULT_TARGET),
    });
  }, [registerCameraActions, camera]);

  const isRobotArm = projectType === "robot_arm";
  const isImported = projectMode === "imported_project" && !isRobotArm;

  return (
    <>
      <color attach="background" args={["#0a0f18"]} />
      <fog attach="fog" args={["#0a0f18", 8, 24]} />

      <PerspectiveCamera makeDefault fov={45} near={0.01} far={100} position={DEFAULT_CAMERA_POSITION} />
      <OrbitControls
        ref={controlsRef}
        makeDefault
        target={DEFAULT_TARGET}
        enablePan
        enableZoom
        enableRotate
        minDistance={0.8}
        maxDistance={12}
        maxPolarAngle={Math.PI * 0.49}
      />

      <ambientLight intensity={0.55} />
      <hemisphereLight intensity={0.35} groundColor="#1a1a2e" color="#ffffff" />
      <directionalLight position={[4, 6, 3]} intensity={1.15} castShadow shadow-mapSize-width={2048} shadow-mapSize-height={2048} />
      <directionalLight position={[-3, 3, -4]} intensity={0.25} />

      <FloorGrid />

      {genesisReplayActive ? (
        <GenesisReplayLayer
          showVisualMesh={showVisualMesh && viewMode !== "debug"}
          showCollisionMesh={showCollisionMesh || debugOverlays}
          showJointAxes={showJointAxes || debugOverlays}
          showSensorRays={showSensorRays || debugOverlays}
          showWires={showWires}
          showInternals={showInternals}
        />
      ) : null}

      {!genesisReplayActive ? (
        <group ref={modelRootRef} key={`${projectId}-${projectType}-${projectMode}`}>
          {isImported ? (
            <ImportedModelPreview />
          ) : isRobotArm ? (
            <RobotArmPreview showJointAxes={showJointAxes || showSkeleton} />
          ) : (
            <RobotDogPreview
              input={input}
              showVisualMesh={showVisualMesh}
              showCollisionMesh={showCollisionMesh}
              showJointAxes={showJointAxes || showSkeleton}
              showSensorRays={showSensorRays}
              showWires={showWires}
              showInternals={showInternals}
            />
          )}
          {showComOverlay ? (
            <mesh position={[0, 0.38, 0]}>
              <sphereGeometry args={[0.04, 12, 12]} />
              <meshStandardMaterial color="#f59e0b" emissive="#f59e0b" emissiveIntensity={0.5} />
            </mesh>
          ) : null}
        </group>
      ) : null}
    </>
  );
}
