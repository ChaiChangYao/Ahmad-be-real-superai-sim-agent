"use client";

import { useMemo } from "react";
import { useSimStore } from "@/lib/state";

export function ImportedModelPreview() {
  const manifest = useSimStore((s) => s.manifest);
  const selectedPartId = useSimStore((s) => s.selectedPartId);
  const setSelectedPartId = useSimStore((s) => s.setSelectedPartId);

  const linkPositions = useMemo(() => {
    const links = manifest?.links ?? [];
    return links.map((link, idx) => ({
      id: link.id,
      x: link.transform.position.x || 0,
      y: (link.transform.position.z || 0.2) + 0.2,
      z: link.transform.position.y || 0,
      size: Math.max(0.06, Math.min(0.4, Math.cbrt(Math.max(0.001, link.mass_kg)) * 0.08)),
      color: selectedPartId === `link:${link.id}` ? "#60a5fa" : idx === 0 ? "#f4be2c" : "#334155",
    }));
  }, [manifest?.links, selectedPartId]);

  if (!manifest || linkPositions.length === 0) {
    return null;
  }

  return (
    <group>
      {linkPositions.map((link) => (
        <mesh key={link.id} position={[link.x, link.y, link.z]} castShadow onPointerDown={(e) => { e.stopPropagation(); setSelectedPartId(`link:${link.id}`); }}>
          <boxGeometry args={[link.size, link.size, link.size]} />
          <meshStandardMaterial color={link.color} />
        </mesh>
      ))}
    </group>
  );
}
