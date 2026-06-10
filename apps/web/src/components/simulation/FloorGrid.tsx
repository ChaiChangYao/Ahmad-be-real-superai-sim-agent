"use client";

import { ContactShadows, Grid } from "@react-three/drei";

export function FloorGrid() {
  return (
    <group>
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.001, 0]}>
        <planeGeometry args={[60, 60]} />
        <meshStandardMaterial color="#0c1018" metalness={0.08} roughness={0.92} />
      </mesh>
      <Grid
        args={[60, 60]}
        cellSize={0.25}
        cellThickness={0.6}
        cellColor="#1a2332"
        sectionSize={1}
        sectionThickness={1.2}
        sectionColor="#2f3f56"
        fadeDistance={28}
        fadeStrength={1.5}
        infiniteGrid
        position={[0, 0.002, 0]}
      />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.003, 0]}>
        <planeGeometry args={[60, 60, 1, 1]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      <ContactShadows position={[0, 0.004, 0]} opacity={0.42} scale={10} blur={2.2} far={3.2} />
    </group>
  );
}
