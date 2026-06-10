"use client";

import { OrbitControls, PerspectiveCamera } from "@react-three/drei";
import { useEffect, useLayoutEffect, useMemo, useRef } from "react";
import {
  Box3,
  CanvasTexture,
  Group,
  RepeatWrapping,
  SRGBColorSpace,
  Vector3,
} from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { logAppliedFrame, logReplayDiagnostics } from "./replay_diagnostics";
import { LidarPointOverlay } from "./LidarPointOverlay";
import { ReplayObjectMesh } from "./ReplayObject";
import { applyTransformToObject3D, convertPosition, convertQuaternion, logTransformSamples } from "./replay_transforms";
import { getTransform, type ReplayBundle, type ReplayObject } from "./types";

function useCheckerTexture() {
  return useMemo(() => {
    const size = 256;
    const canvas = document.createElement("canvas");
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    const cells = 8;
    const cell = size / cells;
    for (let y = 0; y < cells; y += 1) {
      for (let x = 0; x < cells; x += 1) {
        ctx.fillStyle = (x + y) % 2 === 0 ? "#64748b" : "#334155";
        ctx.fillRect(x * cell, y * cell, cell, cell);
      }
    }
    const texture = new CanvasTexture(canvas);
    texture.wrapS = RepeatWrapping;
    texture.wrapT = RepeatWrapping;
    texture.repeat.set(6, 6);
    texture.colorSpace = SRGBColorSpace;
    return texture;
  }, []);
}

function CheckerFloor() {
  const map = useCheckerTexture();
  return (
    <group>
      <mesh receiveShadow rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]}>
        <planeGeometry args={[8, 8]} />
        <meshStandardMaterial map={map ?? undefined} color={map ? "#ffffff" : "#475569"} roughness={0.92} metalness={0.02} />
      </mesh>
      <gridHelper args={[8, 32, "#475569", "#1e293b"]} position={[0, 0.001, 0]} />
    </group>
  );
}

function resolveSourceUpAxis(scene: Record<string, unknown> | undefined): string {
  const axis = scene?.upAxis;
  return typeof axis === "string" && axis.length > 0 ? axis : "z";
}

function fitCameraToGroups(controls: OrbitControlsImpl | null, groups: Map<string, Group>) {
  if (!controls) return;
  const box = new Box3();
  for (const group of groups.values()) {
    box.expandByObject(group);
  }
  if (box.isEmpty()) {
    controls.target.set(0, 0.35, 0);
    controls.object.position.set(1.8, 1.1, 1.8);
  } else {
    const center = box.getCenter(new Vector3());
    const size = box.getSize(new Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 0.5);
    controls.target.copy(center);
    controls.object.position.set(center.x + maxDim * 1.6, center.y + maxDim * 0.8, center.z + maxDim * 1.6);
  }
  controls.update();
}

function applyFrameToGroups(
  groups: Map<string, Group>,
  objects: ReplayObject[],
  frameIndex: number,
  frames: ReplayBundle["frames"],
  sourceUpAxis: string,
) {
  if (frames.length === 0) return;
  const idx = Math.min(Math.max(0, frameIndex), frames.length - 1);
  const frame = frames[idx] ?? frames[0];
  for (const obj of objects) {
    const group = groups.get(obj.id);
    if (!group) continue;
    applyTransformToObject3D(group, getTransform(frame, obj.id), sourceUpAxis);
  }
}

type SceneObjectsProps = {
  replay: ReplayBundle;
  frameIndex: number;
  fitCameraToken: number;
  sourceUpAxis: string;
  debugReplay: boolean;
  debugMode: boolean;
  sampleObjectId: string | null;
};

function SceneObjects({ replay, frameIndex, fitCameraToken, sourceUpAxis, debugReplay, sampleObjectId, debugMode }: SceneObjectsProps) {
  const groupsRef = useRef<Map<string, Group>>(new Map());
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const loggedLaunchRef = useRef<string | null>(null);
  const lastAppliedFrameRef = useRef<number | null>(null);

  const renderObjects = useMemo(
    () => replay.objects.filter((o) => o.visual?.kind !== "checker_floor" && !o.type.includes("plane") && !o.id.startsWith("env/")),
    [replay.objects],
  );

  useEffect(() => {
    groupsRef.current.clear();
    lastAppliedFrameRef.current = null;
  }, [replay.launchId]);

  useEffect(() => {
    if (loggedLaunchRef.current === replay.launchId || renderObjects.length === 0) return;
    logReplayDiagnostics(replay);
    const frame = replay.frames[0];
    if (!frame) return;
    const samples = renderObjects.slice(0, 4).map((obj) => {
      const before = getTransform(frame, obj.id);
      const afterPos = before?.position ? convertPosition(before.position, sourceUpAxis) : [0, 0, 0];
      const afterQuat = convertQuaternion(before?.quaternion ?? before?.rotation_quat, sourceUpAxis);
      return { id: obj.id, before, after: { pos: afterPos, quat: afterQuat } };
    });
    logTransformSamples(replay.launchId, samples);
    loggedLaunchRef.current = replay.launchId;
  }, [replay, renderObjects, sourceUpAxis]);

  useLayoutEffect(() => {
    applyFrameToGroups(groupsRef.current, renderObjects, frameIndex, replay.frames, sourceUpAxis);
    if (lastAppliedFrameRef.current !== frameIndex) {
      logAppliedFrame(frameIndex, replay.frames.length, sampleObjectId, replay.frames, debugMode || debugReplay);
      if (debugMode || debugReplay) {
        const updated = renderObjects.filter((o) => getTransform(replay.frames[frameIndex], o.id)).length;
        console.info("[replay-playback] applyFrame", {
          frameIndex,
          objectsUpdated: updated,
          robotLinks: renderObjects.filter((o) => o.type === "robot_link").length,
        });
      }
      lastAppliedFrameRef.current = frameIndex;
    }
  }, [frameIndex, renderObjects, replay.frames, sourceUpAxis, sampleObjectId, debugMode, debugReplay]);

  useEffect(() => {
    fitCameraToGroups(controlsRef.current, groupsRef.current);
  }, [fitCameraToken]);

  return (
    <>
      {debugReplay ? <axesHelper args={[0.3]} /> : null}
      {renderObjects.map((obj) => (
        <group
          key={obj.id}
          ref={(node) => {
            if (node) {
              groupsRef.current.set(obj.id, node);
            } else {
              groupsRef.current.delete(obj.id);
            }
          }}
        >
          <ReplayObjectMesh obj={obj} projectId={replay.projectId} launchId={replay.launchId} />
        </group>
      ))}
      <OrbitControls
        ref={controlsRef}
        makeDefault
        target={new Vector3(0, 0.35, 0)}
        enableDamping
        maxPolarAngle={Math.PI * 0.48}
      />
    </>
  );
}

type Props = {
  replay: ReplayBundle;
  frameIndex: number;
  fitCameraToken?: number;
  sampleObjectId?: string | null;
  debugMode?: boolean;
};

export function ReplayScene({ replay, frameIndex, fitCameraToken = 0, sampleObjectId = null, debugMode = false }: Props) {
  const sourceUpAxis = resolveSourceUpAxis(replay.scene);
  const unsupportedTypes = useMemo(() => {
    const tokens = new Set<string>();
    for (const obj of replay.objects) {
      const t = `${obj.type} ${obj.visual?.kind ?? ""}`.toLowerCase();
      if (t.includes("particle") || t.includes("mpm") || t.includes("sph") || t.includes("fluid") || t.includes("pbd")) {
        tokens.add(obj.type || obj.visual?.kind || "particle");
      }
    }
    return [...tokens];
  }, [replay.objects]);
  const debugReplay =
    (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("debug") === "1") ||
    process.env.NEXT_PUBLIC_REPLAY_DEBUG === "1";

  const hasLidarPoints = replay.frames.some((frame) => (frame.lidar_points?.length ?? 0) > 0);

  return (
    <>
      <color attach="background" args={["#0f172a"]} />
      <fog attach="fog" args={["#0f172a", 5, 14]} />
      <PerspectiveCamera makeDefault position={[1.8, 1.1, 1.8]} fov={42} near={0.01} far={50} />
      <ambientLight intensity={0.35} />
      <hemisphereLight args={["#cbd5e1", "#1e293b", 0.45]} />
      <directionalLight castShadow position={[3, 5, 2]} intensity={1.25} shadow-mapSize={[1024, 1024]} />
      <directionalLight position={[-2, 2, -3]} intensity={0.35} />
      <CheckerFloor />
      {unsupportedTypes.length > 0 ? (
        <mesh position={[0, 1.2, 0]}>
          <planeGeometry args={[2.4, 0.35]} />
          <meshBasicMaterial color="#111827" transparent opacity={0.85} />
        </mesh>
      ) : null}
      <SceneObjects
        replay={replay}
        frameIndex={frameIndex}
        fitCameraToken={fitCameraToken}
        sourceUpAxis={sourceUpAxis}
        debugReplay={debugReplay}
        sampleObjectId={sampleObjectId}
        debugMode={debugMode}
      />
      {hasLidarPoints ? (
        <LidarPointOverlay replay={replay} frameIndex={frameIndex} sourceUpAxis={sourceUpAxis} />
      ) : null}
    </>
  );
}
