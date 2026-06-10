"use client";

import { ReplayMeshObject } from "./ReplayMeshObject";
import type { ReplayObject as ReplayObjectType, ReplayVisual } from "./types";

function ProceduralShape({ visual }: { visual: ReplayVisual }) {
  const color = visual.color ?? "#8b95a5";
  const kind = visual.kind === "procedural" ? "capsule" : visual.kind ?? "box";

  if (kind === "sphere") {
    const r = visual.radius ?? 0.05;
    return (
      <mesh castShadow receiveShadow>
        <sphereGeometry args={[r, 16, 16]} />
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.5} />
      </mesh>
    );
  }

  if (kind === "capsule" || kind === "cylinder") {
    const r = visual.radius ?? 0.04;
    const h = visual.length ?? visual.height ?? 0.1;
    return (
      <mesh castShadow receiveShadow>
        {kind === "capsule" ? (
          <capsuleGeometry args={[r, h, 4, 12]} />
        ) : (
          <cylinderGeometry args={[r, r, h, 12]} />
        )}
        <meshStandardMaterial color={color} metalness={0.1} roughness={0.5} />
      </mesh>
    );
  }

  const sizeArr = visual.size ?? [0.12, 0.12, 0.12];
  const size: [number, number, number] = [sizeArr[0] ?? 0.12, sizeArr[1] ?? 0.12, sizeArr[2] ?? 0.12];
  return (
    <mesh castShadow receiveShadow scale={size}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={color} metalness={0.1} roughness={0.45} />
    </mesh>
  );
}

type Props = {
  obj: ReplayObjectType;
  projectId: string;
  launchId: string;
};

function robotLinkFallbackVisual(visual: ReplayVisual): ReplayVisual {
  if (visual.kind === "procedural" || visual.radius || visual.length) {
    return visual;
  }
  return {
    kind: "capsule",
    radius: 0.035,
    length: 0.1,
    color: visual.color ?? "#8b95a5",
  };
}

export function ReplayObjectMesh({ obj, projectId, launchId }: Props) {
  const visual = obj.visual ?? {};

  if (visual.meshPath) {
    const fallback =
      obj.type === "robot_link" ? <ProceduralShape visual={robotLinkFallbackVisual(visual)} /> : null;
    return (
      <ReplayMeshObject
        projectId={projectId}
        launchId={launchId}
        meshPath={visual.meshPath}
        color={visual.color ?? (obj.type === "robot_link" ? "#8b95a5" : "#c54b5d")}
        fallback={fallback}
      />
    );
  }

  if (visual.kind === "procedural" || obj.type === "robot_link") {
    return <ProceduralShape visual={robotLinkFallbackVisual(visual)} />;
  }

  if (visual.kind === "box" || obj.id === "manipuland/cube") {
    const s = visual.size ?? [0.04, 0.04, 0.04];
    const size: [number, number, number] = [s[0] ?? 0.04, s[1] ?? 0.04, s[2] ?? 0.04];
    return (
      <mesh castShadow receiveShadow scale={size}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={visual.color ?? "#c54b5d"} metalness={0.1} roughness={0.4} />
      </mesh>
    );
  }

  return <ProceduralShape visual={visual} />;
}
