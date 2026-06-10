"use client";

import { Canvas } from "@react-three/fiber";
import { ReplayScene } from "./ReplayScene";
import type { ReplayBundle } from "./types";

type Props = {
  replay: ReplayBundle;
  frameIndex: number;
  fitCameraToken?: number;
  sampleObjectId?: string | null;
  debugMode?: boolean;
};

export function ReplayCanvasInner({ replay, frameIndex, fitCameraToken = 0, sampleObjectId = null, debugMode = false }: Props) {
  return (
    <Canvas
      key={replay.launchId}
      shadows
      dpr={[1, 2]}
      gl={{ antialias: true, alpha: false }}
      style={{ width: "100%", height: "100%", background: "#0f172a" }}
    >
      <ReplayScene replay={replay} frameIndex={frameIndex} fitCameraToken={fitCameraToken} sampleObjectId={sampleObjectId} debugMode={debugMode} />
    </Canvas>
  );
}
