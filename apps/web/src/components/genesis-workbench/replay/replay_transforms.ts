import type { Object3D } from "three";
import type { ReplayTransform } from "./types";

export const GENESIS_UP_AXIS = "z" as const;
export const RENDERER_UP_AXIS = "y" as const;

/** Genesis Z-up → Three.js Y-up: (x, y, z) → (x, z, -y) */
export function convertPosition(pos: number[], sourceUpAxis: string = GENESIS_UP_AXIS): [number, number, number] {
  if (sourceUpAxis.toLowerCase() === RENDERER_UP_AXIS) {
    return [pos[0] ?? 0, pos[1] ?? 0, pos[2] ?? 0];
  }
  const x = pos[0] ?? 0;
  const y = pos[1] ?? 0;
  const z = pos[2] ?? 0;
  return [x, z, -y];
}

/** Fixed -90° rotation about X in w-first quaternion (Genesis Z-up → Three Y-up). */
const ZUP_TO_YUP_W = Math.sqrt(0.5);
const ZUP_TO_YUP_Q: [number, number, number, number] = [ZUP_TO_YUP_W, -ZUP_TO_YUP_W, 0, 0];

function multiplyQuatWFirst(
  a: [number, number, number, number],
  b: [number, number, number, number],
): [number, number, number, number] {
  const [aw, ax, ay, az] = a;
  const [bw, bx, by, bz] = b;
  return [
    aw * bw - ax * bx - ay * by - az * bz,
    aw * bx + ax * bw + ay * bz - az * by,
    aw * by - ax * bz + ay * bw + az * bx,
    aw * bz + ax * by - ay * bx + az * bw,
  ];
}

/** Genesis w-first quaternion → Three.js w-last (x, y, z, w). */
export function convertQuaternion(
  quat: number[] | undefined,
  sourceUpAxis: string = GENESIS_UP_AXIS,
): [number, number, number, number] | null {
  if (!quat || quat.length < 4) return null;
  let [w, x, y, z] = [quat[0], quat[1], quat[2], quat[3]];
  if (sourceUpAxis.toLowerCase() !== RENDERER_UP_AXIS) {
    [w, x, y, z] = multiplyQuatWFirst(ZUP_TO_YUP_Q, [w, x, y, z]);
  }
  return [x, y, z, w];
}

export function applyTransformToObject3D(
  object: Object3D,
  transform: ReplayTransform | undefined,
  sourceUpAxis: string = GENESIS_UP_AXIS,
): void {
  const pos = transform?.position;
  if (pos && pos.length >= 3) {
    const [tx, ty, tz] = convertPosition(pos, sourceUpAxis);
    object.position.set(tx, ty, tz);
  }
  const quat = transform?.quaternion ?? transform?.rotation_quat;
  const converted = convertQuaternion(quat, sourceUpAxis);
  if (converted) {
    object.quaternion.set(converted[0], converted[1], converted[2], converted[3]);
  }
}

export function logTransformSamples(
  launchId: string,
  samples: Array<{ id: string; before: ReplayTransform | undefined; after: { pos: number[]; quat: number[] | null } }>,
): void {
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_REPLAY_DEBUG !== "1") return;
  console.info(`[replay-transforms] launch=${launchId} upAxis=${GENESIS_UP_AXIS} rendererUp=${RENDERER_UP_AXIS}`);
  for (const s of samples) {
    console.info(`[replay-transforms] ${s.id}`, { before: s.before, after: s.after });
  }
}
