"use client";

import { useMemo } from "react";
import { useSimStore } from "@/lib/state";

function Leg({ x, z, color }: { x: number; z: number; color: string }) {
  return (
    <group position={[x, -0.1, z]}>
      <mesh position={[0, -0.12, 0]}>
        <capsuleGeometry args={[0.02, 0.12, 6, 10]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, -0.24, 0]}>
        <capsuleGeometry args={[0.018, 0.1, 6, 10]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
      <mesh position={[0, -0.32, 0]}>
        <sphereGeometry args={[0.025, 16, 16]} />
        <meshStandardMaterial color="#1f2937" />
      </mesh>
    </group>
  );
}

export function ThreeRobotDogScene({ showCollision, showWires }: { showCollision: boolean; showWires: boolean }) {
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const runTimeseries = useSimStore((s) => s.runTimeseries);
  const manifest = useSimStore((s) => s.manifest);
  const battery = manifest?.electronics?.find((e) => e.component_profile_id.toLowerCase().includes("battery"));
  const lastFrame = runTimeseries.length > 0 ? runTimeseries[runTimeseries.length - 1] : null;
  const bodyPos = (lastFrame?.links as Record<string, { position: [number, number, number] }> | undefined)?.body?.position ?? [0, 0, 0.18];
  const highlightColor = useMemo(() => (selectedPartId ? "#1f4ea3" : "#9ca3af"), [selectedPartId]);

  return (
    <group position={[bodyPos[0], bodyPos[1], bodyPos[2] - 0.18]}>
      <mesh position={[0, 0.2, 0]}>
        <boxGeometry args={[0.9, 0.22, 0.35]} />
        <meshStandardMaterial color="#f4c430" />
      </mesh>
      <mesh position={[0, 0.16, 0]}>
        <boxGeometry args={[0.88, 0.12, 0.33]} />
        <meshStandardMaterial color={highlightColor} />
      </mesh>
      <mesh position={[0, 0.23, 0.12]}>
        <boxGeometry args={[0.55, 0.02, 0.02]} />
        <meshStandardMaterial color="#111827" />
      </mesh>
      <mesh position={[0, 0.23, -0.12]}>
        <boxGeometry args={[0.55, 0.02, 0.02]} />
        <meshStandardMaterial color="#111827" />
      </mesh>
      <mesh position={[0.45, 0.2, 0]}>
        <boxGeometry args={[0.06, 0.08, 0.1]} />
        <meshStandardMaterial color="#0f172a" />
      </mesh>
      <mesh position={[battery?.transform.position.x ?? 0.0, (battery?.transform.position.z ?? 0.17), battery?.transform.position.y ?? 0.0]}>
        <boxGeometry args={[0.14, 0.08, 0.1]} />
        <meshStandardMaterial color="#f97316" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.34, 0]}>
        <planeGeometry args={[10, 10]} />
        <meshStandardMaterial color="#e5e7eb" />
      </mesh>
      <Leg x={0.34} z={0.18} color="#111827" />
      <Leg x={0.34} z={-0.18} color="#111827" />
      <Leg x={-0.34} z={0.18} color="#111827" />
      <Leg x={-0.34} z={-0.18} color="#111827" />
      {showCollision ? (
        <mesh position={[0, 0.2, 0]}>
          <boxGeometry args={[0.82, 0.18, 0.32]} />
          <meshStandardMaterial color="#22c55e" transparent opacity={0.2} />
        </mesh>
      ) : null}
      {showWires ? (
        <mesh position={[0.2, 0.19, 0.0]} rotation={[0.0, 0.3, 0]}>
          <cylinderGeometry args={[0.006, 0.006, 0.35, 12]} />
          <meshStandardMaterial color="#ef4444" />
        </mesh>
      ) : null}
    </group>
  );
}
