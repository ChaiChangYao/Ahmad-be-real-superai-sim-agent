"use client";

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type { Group } from "three";
import { Quaternion, Vector3 } from "three";
import { useSimStore } from "@/lib/state";

const ARM_BODY = "#e8eaed";
const JOINT_COLOR = "#2d3748";
const ACCENT = "#5b7fd1";
const BASE_COLOR = "#4a5568";
const GRIPPER_COLOR = "#cbd5e1";

const BASE_RADIUS = 0.18;
const BASE_HEIGHT = 0.12;
const SHOULDER_Y = 0.25;
const UPPER_ARM_LEN = 0.45;
const FOREARM_LEN = 0.4;
const WRIST_LEN = 0.15;
const GRIPPER_LEN = 0.12;

type CapsuleLinkProps = {
  start: Vector3;
  end: Vector3;
  radius: number;
  color: string;
  selected?: boolean;
  onSelect?: () => void;
};

function CapsuleLink({ start, end, radius, color, selected, onSelect }: CapsuleLinkProps) {
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
    <mesh
      position={midpoint}
      quaternion={quaternion}
      castShadow
      receiveShadow
      onPointerDown={(e) => {
        e.stopPropagation();
        onSelect?.();
      }}
    >
      <cylinderGeometry args={[radius, radius, length, 20]} />
      <meshStandardMaterial
        color={color}
        metalness={0.35}
        roughness={0.45}
        emissive={selected ? ACCENT : "#000000"}
        emissiveIntensity={selected ? 0.35 : 0}
      />
    </mesh>
  );
}

function JointHub({
  position,
  radius = 0.055,
  height = 0.09,
  selected,
  onSelect,
}: {
  position: [number, number, number];
  radius?: number;
  height?: number;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <mesh
      position={position}
      castShadow
      onPointerDown={(e) => {
        e.stopPropagation();
        onSelect?.();
      }}
    >
      <cylinderGeometry args={[radius, radius, height, 24]} />
      <meshStandardMaterial
        color={JOINT_COLOR}
        metalness={0.5}
        roughness={0.35}
        emissive={selected ? ACCENT : "#000000"}
        emissiveIntensity={selected ? 0.4 : 0}
      />
    </mesh>
  );
}

function SkeletonLine({ from, to }: { from: Vector3; to: Vector3 }) {
  return <CapsuleLink start={from} end={to} radius={0.008} color="#38bdf8" />;
}

type RobotArmPreviewProps = {
  showJointAxes?: boolean;
};

export function RobotArmPreview({ showJointAxes = false }: RobotArmPreviewProps) {
  const baseYawRef = useRef<Group>(null);
  const shoulderPitchRef = useRef<Group>(null);
  const elbowPitchRef = useRef<Group>(null);
  const wristPitchRef = useRef<Group>(null);
  const wristRollRef = useRef<Group>(null);
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);
  const showPayloadPreview = useSimStore((s) => s.showPayloadPreview);
  const showSkeleton = useSimStore((s) => s.showSkeleton);

  const isSelected = (id: string) => selectedPartId === `link:${id}`;

  useFrame((state) => {
    const t = state.clock.elapsedTime;
    if (baseYawRef.current) baseYawRef.current.rotation.y = Math.sin(t * 0.35) * 0.55;
    if (shoulderPitchRef.current) shoulderPitchRef.current.rotation.x = -0.35 + Math.sin(t * 0.5) * 0.2;
    if (elbowPitchRef.current) elbowPitchRef.current.rotation.x = 0.85 + Math.sin(t * 0.65) * 0.15;
    if (wristPitchRef.current) wristPitchRef.current.rotation.x = Math.sin(t * 0.9) * 0.25;
    if (wristRollRef.current) wristRollRef.current.rotation.z = Math.sin(t * 1.1) * 0.35;
  });

  const skeletonPoints = useMemo(() => {
    const base = new Vector3(0, SHOULDER_Y, 0);
    const shoulder = new Vector3(0, SHOULDER_Y, 0);
    const elbow = new Vector3(0, SHOULDER_Y, UPPER_ARM_LEN);
    const wrist = new Vector3(0, SHOULDER_Y - FOREARM_LEN * 0.55, UPPER_ARM_LEN + FOREARM_LEN * 0.45);
    const tool = new Vector3(0, SHOULDER_Y - FOREARM_LEN * 0.55 - WRIST_LEN, UPPER_ARM_LEN + FOREARM_LEN * 0.45);
    return { base, shoulder, elbow, wrist, tool };
  }, []);

  return (
    <group>
      {/* Base pedestal */}
      <mesh
        position={[0, BASE_HEIGHT / 2, 0]}
        castShadow
        receiveShadow
        onPointerDown={(e) => {
          e.stopPropagation();
          setSelectedPartId("link:arm_base");
        }}
      >
        <cylinderGeometry args={[BASE_RADIUS, BASE_RADIUS * 1.05, BASE_HEIGHT, 32]} />
        <meshStandardMaterial
          color={isSelected("arm_base") ? ACCENT : BASE_COLOR}
          metalness={0.4}
          roughness={0.5}
        />
      </mesh>
      <mesh position={[0, BASE_HEIGHT + 0.02, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[0.1, 0.12, 0.04, 24]} />
        <meshStandardMaterial color={JOINT_COLOR} metalness={0.55} roughness={0.35} />
      </mesh>

      {/* base_yaw */}
      <group ref={baseYawRef} position={[0, SHOULDER_Y, 0]}>
        <JointHub
          position={[0, 0, 0]}
          selected={isSelected("arm_shoulder")}
          onSelect={() => setSelectedPartId("link:arm_shoulder")}
        />

        {/* shoulder_pitch */}
        <group ref={shoulderPitchRef}>
          <CapsuleLink
            start={new Vector3(0, 0, 0)}
            end={new Vector3(0, 0, UPPER_ARM_LEN)}
            radius={0.055}
            color={isSelected("arm_upper") ? ACCENT : ARM_BODY}
            selected={isSelected("arm_upper")}
            onSelect={() => setSelectedPartId("link:arm_upper")}
          />

          {/* elbow_pitch */}
          <group ref={elbowPitchRef} position={[0, 0, UPPER_ARM_LEN]}>
            <JointHub
              position={[0, 0, 0]}
              radius={0.05}
              height={0.08}
              selected={isSelected("arm_elbow")}
              onSelect={() => setSelectedPartId("link:arm_elbow")}
            />

            <group rotation={[Math.PI / 2, 0, 0]}>
              <CapsuleLink
                start={new Vector3(0, 0, 0)}
                end={new Vector3(0, FOREARM_LEN, 0)}
                radius={0.048}
                color={isSelected("arm_forearm") ? ACCENT : ARM_BODY}
                selected={isSelected("arm_forearm")}
                onSelect={() => setSelectedPartId("link:arm_forearm")}
              />
            </group>

            {/* wrist_pitch */}
            <group ref={wristPitchRef} position={[0, -FOREARM_LEN * 0.55, FOREARM_LEN * 0.45]}>
              <JointHub
                position={[0, 0, 0]}
                radius={0.038}
                height={0.06}
                selected={isSelected("arm_wrist")}
                onSelect={() => setSelectedPartId("link:arm_wrist")}
              />

              <CapsuleLink
                start={new Vector3(0, 0, 0)}
                end={new Vector3(0, -WRIST_LEN, 0)}
                radius={0.035}
                color={isSelected("arm_wrist_link") ? ACCENT : ARM_BODY}
              />

              {/* wrist_roll + gripper */}
              <group ref={wristRollRef} position={[0, -WRIST_LEN, 0]}>
                <mesh
                  castShadow
                  onPointerDown={(e) => {
                    e.stopPropagation();
                    setSelectedPartId("link:arm_gripper");
                  }}
                >
                  <boxGeometry args={[0.1, 0.06, GRIPPER_LEN]} />
                  <meshStandardMaterial
                    color={isSelected("arm_gripper") ? ACCENT : GRIPPER_COLOR}
                    metalness={0.45}
                    roughness={0.4}
                  />
                </mesh>
                <mesh position={[0.055, 0, GRIPPER_LEN * 0.35]} castShadow>
                  <boxGeometry args={[0.018, 0.04, 0.07]} />
                  <meshStandardMaterial color={JOINT_COLOR} metalness={0.5} roughness={0.35} />
                </mesh>
                <mesh position={[-0.055, 0, GRIPPER_LEN * 0.35]} castShadow>
                  <boxGeometry args={[0.018, 0.04, 0.07]} />
                  <meshStandardMaterial color={JOINT_COLOR} metalness={0.5} roughness={0.35} />
                </mesh>

                {showPayloadPreview ? (
                  <mesh position={[0, -0.06, GRIPPER_LEN * 0.55]} castShadow>
                    <boxGeometry args={[0.08, 0.08, 0.08]} />
                    <meshStandardMaterial color="#94a3b8" metalness={0.2} roughness={0.6} />
                  </mesh>
                ) : null}
              </group>
            </group>
          </group>
        </group>
      </group>

      {(showSkeleton || showJointAxes) && (
        <group>
          <SkeletonLine from={skeletonPoints.base} to={skeletonPoints.elbow} />
          <SkeletonLine from={skeletonPoints.elbow} to={skeletonPoints.wrist} />
          <SkeletonLine from={skeletonPoints.wrist} to={skeletonPoints.tool} />
        </group>
      )}
    </group>
  );
}
