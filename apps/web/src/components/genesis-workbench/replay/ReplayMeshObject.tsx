"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { BufferGeometry, Float32BufferAttribute, MeshStandardMaterial, Uint32BufferAttribute } from "three";
import { showcaseMeshUrl } from "./types";

type Props = {
  projectId: string;
  launchId: string;
  meshPath: string;
  color?: string;
  fallback?: ReactNode;
};

export function ReplayMeshObject({ projectId, launchId, meshPath, color = "#8b95a5", fallback = null }: Props) {
  const [geometry, setGeometry] = useState<BufferGeometry | null>(null);
  const cacheKey = `${launchId}:${meshPath}`;

  useEffect(() => {
    const controller = new AbortController();
    setGeometry(null);
    void (async () => {
      try {
        const res = await fetch(showcaseMeshUrl(projectId, launchId, meshPath), { signal: controller.signal });
        if (!res.ok) return;
        const data = (await res.json()) as { positions?: number[]; indices?: number[] };
        if (controller.signal.aborted) return;
        const positions = data.positions ?? [];
        if (positions.length < 9) return;
        const geo = new BufferGeometry();
        geo.setAttribute("position", new Float32BufferAttribute(positions, 3));
        if (data.indices?.length) {
          geo.setIndex(new Uint32BufferAttribute(data.indices, 1));
        }
        geo.computeVertexNormals();
        setGeometry(geo);
      } catch {
        /* aborted or failed */
      }
    })();
    return () => {
      controller.abort();
      setGeometry((prev) => {
        prev?.dispose();
        return null;
      });
    };
  }, [cacheKey, projectId, launchId, meshPath]);

  const material = useMemo(
    () => new MeshStandardMaterial({ color, metalness: 0.25, roughness: 0.62 }),
    [color],
  );

  useEffect(() => () => material.dispose(), [material]);

  if (geometry) {
    return <mesh geometry={geometry} material={material} castShadow receiveShadow />;
  }
  if (fallback) return <>{fallback}</>;
  return null;
}
