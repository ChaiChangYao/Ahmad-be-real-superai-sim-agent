"use client";

import { RoundedBox } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useMemo, useRef, useState } from "react";
import type { Group, Vector3Tuple } from "three";
import { Euler, Quaternion, Vector3 } from "three";
import { useSimStore } from "@/lib/state";

type PreviewInput = {
  forward: boolean;
  backward: boolean;
  left: boolean;
  right: boolean;
  jump: boolean;
  stop: boolean;
  resetTick: number;
};

type RobotDogPreviewProps = {
  input: PreviewInput;
  showVisualMesh: boolean;
  showCollisionMesh: boolean;
  showJointAxes: boolean;
  showSensorRays: boolean;
  showWires: boolean;
  showInternals: boolean;
};

type SegmentProps = {
  start: Vector3;
  end: Vector3;
  radius: number;
  color: string;
  selected: boolean;
  onSelect?: () => void;
};

type LegPose = {
  hip: Vector3;
  knee: Vector3;
  foot: Vector3;
  footName: string;
  upperName: string;
  lowerName: string;
};

const BODY_CENTER_Y = 0.58;
const BODY_HALF_HEIGHT = 0.11;
const HIP_Y = BODY_CENTER_Y - BODY_HALF_HEIGHT + 0.015;
const FOOT_Y = 0.03;
const WALK_SPEED = 0.8;
const ROTATE_SPEED = 1.35;

const BODY_COLOR = "#f4be2c";
const LEG_COLOR = "#1f2937";
const JOINT_COLOR = "#0f172a";
const FOOT_COLOR = "#111111";

const LEG_ANCHORS = [
  { name: "fl", x: -0.21, z: 0.33, phase: 0 },
  { name: "fr", x: 0.21, z: 0.33, phase: Math.PI },
  { name: "rl", x: -0.21, z: -0.33, phase: Math.PI },
  { name: "rr", x: 0.21, z: -0.33, phase: 0 }
] as const;

const PART_ALIASES: Record<string, string> = {
  body: "body",
  torso: "body",
  front_sensor: "sensor_panel",
  front_sensor_panel: "sensor_panel",
  fl_upper: "fl_upper",
  fr_upper: "fr_upper",
  rl_upper: "rl_upper",
  rr_upper: "rr_upper",
  fl_lower: "fl_lower",
  fr_lower: "fr_lower",
  rl_lower: "rl_lower",
  rr_lower: "rr_lower",
  fl_foot: "fl_foot",
  fr_foot: "fr_foot",
  rl_foot: "rl_foot",
  rr_foot: "rr_foot"
};

function Segment({ start, end, radius, color, selected, onSelect }: SegmentProps) {
  const direction = useMemo(() => new Vector3(), []);
  const midpoint = useMemo(() => new Vector3(), []);
  const quaternion = useMemo(() => new Quaternion(), []);
  const up = useMemo(() => new Vector3(0, 1, 0), []);

  direction.copy(end).sub(start);
  const length = Math.max(direction.length(), 0.001);
  direction.normalize();
  midpoint.copy(start).add(end).multiplyScalar(0.5);
  quaternion.setFromUnitVectors(up, direction);

  return (
    <mesh position={midpoint} quaternion={quaternion} onPointerDown={onSelect}>
      <cylinderGeometry args={[radius, radius, length, 16]} />
      <meshStandardMaterial color={color} emissive={selected ? "#1d4ed8" : "#000000"} emissiveIntensity={selected ? 0.55 : 0} />
    </mesh>
  );
}

function selectKey(selectedPartId: string | null): string | null {
  if (!selectedPartId) return null;
  const clean = selectedPartId.replace("link:", "");
  return PART_ALIASES[clean] ?? clean;
}

function makeLegPose(anchorX: number, anchorZ: number, phase: number, gait: number, jumpHeight: number): LegPose {
  const stride = gait * 0.055;
  const lift = Math.max(0, Math.sin(gait + phase)) * 0.02;
  const footZ = anchorZ + (anchorZ > 0 ? 0.03 : -0.03) + stride;
  const footX = anchorX + (anchorX > 0 ? 0.008 : -0.008);

  const hip = new Vector3(anchorX, HIP_Y + jumpHeight, anchorZ);
  const foot = new Vector3(footX, FOOT_Y + lift + jumpHeight * 0.28, footZ);

  const kneeBaseY = (hip.y + foot.y) * 0.5;
  const forwardKneeBend = anchorZ > 0 ? -0.065 : 0.065;
  const kneeWave = Math.sin(gait + phase + 0.2) * 0.02;
  const knee = new Vector3(anchorX, kneeBaseY + 0.05, anchorZ + forwardKneeBend + kneeWave);

  const prefix = anchorZ > 0 ? "f" : "r";
  const side = anchorX < 0 ? "l" : "r";
  const label = `${prefix}${side}`;
  return {
    hip,
    knee,
    foot,
    footName: `${label}_foot`,
    upperName: `${label}_upper`,
    lowerName: `${label}_lower`
  };
}

export function RobotDogPreview({
  input,
  showVisualMesh,
  showCollisionMesh,
  showJointAxes,
  showSensorRays,
  showWires,
  showInternals
}: RobotDogPreviewProps) {
  const rootRef = useRef<Group>(null);
  const [, setFrameTick] = useState(0);
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);
  const selected = selectKey(selectedPartId);

  const motionRef = useRef({
    x: 0,
    z: 0,
    yaw: 0,
    gait: 0,
    jumpVelocity: 0,
    jumpHeight: 0,
    resetSeen: input.resetTick
  });

  useFrame((_, delta) => {
    const state = motionRef.current;
    if (state.resetSeen !== input.resetTick || input.stop) {
      state.x = 0;
      state.z = 0;
      state.yaw = 0;
      state.gait = 0;
      state.jumpVelocity = 0;
      state.jumpHeight = 0;
      state.resetSeen = input.resetTick;
    }

    const move = (input.forward ? 1 : 0) - (input.backward ? 1 : 0);
    const turn = (input.left ? 1 : 0) - (input.right ? 1 : 0);

    if (input.jump && state.jumpHeight <= 0.001 && state.jumpVelocity <= 0.001) {
      state.jumpVelocity = 2.45;
    }
    state.jumpVelocity -= 6.0 * delta;
    state.jumpHeight = Math.max(0, state.jumpHeight + state.jumpVelocity * delta);
    if (state.jumpHeight <= 0) {
      state.jumpHeight = 0;
      state.jumpVelocity = Math.max(0, state.jumpVelocity);
    }

    state.yaw += turn * ROTATE_SPEED * delta;
    state.gait += move === 0 ? delta * 1.3 : delta * 5.8;

    const speed = move * WALK_SPEED;
    state.x += Math.sin(state.yaw) * speed * delta;
    state.z += Math.cos(state.yaw) * speed * delta;

    if (rootRef.current) {
      rootRef.current.position.set(state.x, state.jumpHeight, state.z);
      rootRef.current.rotation.set(0, state.yaw, 0);
    }
    setFrameTick((tick) => (tick + 1) % 10_000);
  });

  const hips = useMemo(
    () =>
      LEG_ANCHORS.map((anchor) => ({
        ...anchor,
        id: `hip_${anchor.name}`
      })),
    []
  );

  const activeMotion = motionRef.current;
  const legPoses = hips.map((hip) => makeLegPose(hip.x, hip.z, hip.phase, activeMotion.gait, activeMotion.jumpHeight));

  return (
    <group ref={rootRef}>
      {showVisualMesh ? (
        <group>
          <RoundedBox
            args={[0.38, 0.22, 0.95]}
            radius={0.035}
            smoothness={4}
            position={[0, BODY_CENTER_Y, 0]}
            castShadow
            onPointerDown={(event) => {
              event.stopPropagation();
              setSelectedPartId("link:body");
            }}
          >
            <meshStandardMaterial color={BODY_COLOR} roughness={0.52} metalness={0.18} emissive={selected === "body" ? "#1d4ed8" : "#000000"} emissiveIntensity={selected === "body" ? 0.48 : 0} />
          </RoundedBox>

          <mesh position={[0, 0.6, 0.49]} castShadow onPointerDown={(e) => { e.stopPropagation(); setSelectedPartId("link:front_sensor_panel"); }}>
            <boxGeometry args={[0.22, 0.1, 0.03]} />
            <meshStandardMaterial color="#0b1220" emissive={selected === "sensor_panel" ? "#1d4ed8" : "#000000"} emissiveIntensity={selected === "sensor_panel" ? 0.45 : 0} />
          </mesh>
          <mesh position={[-0.06, 0.6, 0.507]} castShadow>
            <sphereGeometry args={[0.016, 14, 14]} />
            <meshStandardMaterial color="#020617" metalness={0.25} roughness={0.4} />
          </mesh>
          <mesh position={[0.06, 0.6, 0.507]} castShadow>
            <sphereGeometry args={[0.016, 14, 14]} />
            <meshStandardMaterial color="#020617" metalness={0.25} roughness={0.4} />
          </mesh>

          <mesh position={[-0.085, 0.71, 0]} castShadow>
            <boxGeometry args={[0.03, 0.02, 0.54]} />
            <meshStandardMaterial color="#111827" />
          </mesh>
          <mesh position={[0.085, 0.71, 0]} castShadow>
            <boxGeometry args={[0.03, 0.02, 0.54]} />
            <meshStandardMaterial color="#111827" />
          </mesh>

          {showInternals ? (
            <group>
              <mesh position={[-0.06, 0.575, -0.12]} castShadow>
                <boxGeometry args={[0.1, 0.08, 0.2]} />
                <meshStandardMaterial color="#f97316" metalness={0.12} roughness={0.65} />
              </mesh>
              <mesh position={[0.06, 0.58, 0.1]} castShadow>
                <boxGeometry args={[0.09, 0.06, 0.16]} />
                <meshStandardMaterial color="#374151" />
              </mesh>
            </group>
          ) : null}
        </group>
      ) : null}

      {legPoses.map((leg, index) => {
        const selectedUpper = selected === leg.upperName;
        const selectedLower = selected === leg.lowerName;
        const selectedFoot = selected === leg.footName;
        const selectedHip = selected === hips[index].id;
        const upperArmorPos = leg.hip.clone().lerp(leg.knee, 0.38).add(new Vector3(0, 0.015, 0));

        return (
          <group key={hips[index].id}>
            <mesh
              position={leg.hip}
              castShadow
              onPointerDown={(event) => {
                event.stopPropagation();
                setSelectedPartId(`link:${hips[index].id}`);
              }}
            >
              <sphereGeometry args={[0.03, 18, 18]} />
              <meshStandardMaterial color={JOINT_COLOR} emissive={selectedHip ? "#1d4ed8" : "#000000"} emissiveIntensity={selectedHip ? 0.45 : 0} />
            </mesh>

            <Segment
              start={leg.hip}
              end={leg.knee}
              radius={0.022}
              color={LEG_COLOR}
              selected={selectedUpper}
              onSelect={() => setSelectedPartId(`link:${leg.upperName}`)}
            />
            {showVisualMesh ? (
              <mesh position={upperArmorPos} castShadow>
                <boxGeometry args={[0.035, 0.11, 0.05]} />
                <meshStandardMaterial color={BODY_COLOR} roughness={0.58} metalness={0.06} />
              </mesh>
            ) : null}

            <mesh position={leg.knee} castShadow onPointerDown={(event) => { event.stopPropagation(); setSelectedPartId(`link:${leg.lowerName}`); }}>
              <sphereGeometry args={[0.026, 14, 14]} />
              <meshStandardMaterial color={JOINT_COLOR} emissive={selectedLower ? "#1d4ed8" : "#000000"} emissiveIntensity={selectedLower ? 0.45 : 0} />
            </mesh>

            <Segment
              start={leg.knee}
              end={leg.foot}
              radius={0.018}
              color="#111827"
              selected={selectedLower}
              onSelect={() => setSelectedPartId(`link:${leg.lowerName}`)}
            />

            <mesh position={[leg.foot.x, leg.foot.y - 0.006, leg.foot.z]} castShadow onPointerDown={(event) => { event.stopPropagation(); setSelectedPartId(`link:${leg.footName}`); }}>
              <boxGeometry args={[0.16, 0.03, 0.09]} />
              <meshStandardMaterial color={FOOT_COLOR} emissive={selectedFoot ? "#2563eb" : "#000000"} emissiveIntensity={selectedFoot ? 0.45 : 0} />
            </mesh>

            {showJointAxes ? <axesHelper args={[0.08]} position={leg.hip.toArray() as Vector3Tuple} /> : null}
            {showJointAxes ? <axesHelper args={[0.08]} position={leg.knee.toArray() as Vector3Tuple} /> : null}
          </group>
        );
      })}

      {showWires
        ? hips.map((hip) => (
            <mesh
              key={`wire-${hip.id}`}
              position={[hip.x * 0.58, 0.57, hip.z * 0.58]}
              rotation={new Euler(0, hip.x < 0 ? 0.18 : -0.18, hip.z > 0 ? 0.88 : -0.88)}
            >
              <cylinderGeometry args={[0.007, 0.007, 0.24, 10]} />
              <meshStandardMaterial color="#05070b" />
            </mesh>
          ))
        : null}

      {showSensorRays ? (
        <group>
          <mesh position={[-0.06, 0.6, 0.66]} rotation={[Math.PI / 2.8, 0, 0]}>
            <coneGeometry args={[0.02, 0.32, 22, 1, true]} />
            <meshStandardMaterial color="#38bdf8" transparent opacity={0.18} side={2} />
          </mesh>
          <mesh position={[0.06, 0.6, 0.66]} rotation={[Math.PI / 2.8, 0, 0]}>
            <coneGeometry args={[0.02, 0.32, 22, 1, true]} />
            <meshStandardMaterial color="#38bdf8" transparent opacity={0.18} side={2} />
          </mesh>
        </group>
      ) : null}

      {showCollisionMesh ? (
        <group>
          <mesh position={[0, BODY_CENTER_Y, 0]}>
            <boxGeometry args={[0.41, 0.25, 0.98]} />
            <meshStandardMaterial color="#22c55e" transparent opacity={0.14} />
          </mesh>
          {legPoses.map((leg, index) => (
            <mesh key={`col-${index}`} position={[leg.foot.x, (HIP_Y + FOOT_Y) * 0.5, leg.foot.z]}>
              <boxGeometry args={[0.085, 0.5, 0.085]} />
              <meshStandardMaterial color="#22c55e" transparent opacity={0.14} />
            </mesh>
          ))}
        </group>
      ) : null}

    </group>
  );
}
