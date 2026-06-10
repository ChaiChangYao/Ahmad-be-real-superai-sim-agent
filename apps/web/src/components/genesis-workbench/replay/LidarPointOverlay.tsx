"use client";

import { useMemo } from "react";
import { BufferGeometry, Float32BufferAttribute } from "three";
import { convertPosition } from "./replay_transforms";
import type { ReplayBundle } from "./types";

type Props = {
  replay: ReplayBundle;
  frameIndex: number;
  sourceUpAxis: string;
};

export function LidarPointOverlay({ replay, frameIndex, sourceUpAxis }: Props) {
  const geometry = useMemo(() => {
    if (replay.frames.length === 0) return null;
    const idx = Math.min(Math.max(0, frameIndex), replay.frames.length - 1);
    const raw = replay.frames[idx]?.lidar_points ?? [];
    const converted = raw
      .map((p) => convertPosition(p, sourceUpAxis))
      .filter((p) => p.every((v) => Number.isFinite(v)));
    if (converted.length === 0) return null;
    const positions = new Float32Array(converted.length * 3);
    converted.forEach((p, i) => {
      positions[i * 3] = p[0];
      positions[i * 3 + 1] = p[1];
      positions[i * 3 + 2] = p[2];
    });
    const geo = new BufferGeometry();
    geo.setAttribute("position", new Float32BufferAttribute(positions, 3));
    return geo;
  }, [replay.frames, frameIndex, sourceUpAxis]);

  if (!geometry) return null;

  return (
    <points geometry={geometry}>
      <pointsMaterial size={0.06} color="#ef4444" sizeAttenuation />
    </points>
  );
}
