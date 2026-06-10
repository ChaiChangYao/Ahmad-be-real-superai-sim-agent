import type { Camera, Object3D } from "three";
import { Box3, PerspectiveCamera, Vector3 } from "three";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

const PADDING = 1.6;

export function frameObjectInView(
  camera: Camera,
  controls: OrbitControlsImpl | null,
  object: Object3D | null,
  fovDeg = 45
): void {
  if (!object) return;
  const box = new Box3().setFromObject(object as never);
  if (box.isEmpty()) return;

  const center = box.getCenter(new Vector3());
  const size = box.getSize(new Vector3());
  const maxDim = Math.max(size.x, size.y, size.z, 0.35);
  const fovRad = (fovDeg * Math.PI) / 180;
  const distance = (maxDim * PADDING) / (2 * Math.tan(fovRad / 2));
  const offset = new Vector3(distance * 0.75, distance * 0.55, distance * 0.85);

  camera.position.copy(center).add(offset);
  if (camera instanceof PerspectiveCamera) {
    camera.near = Math.max(0.01, distance / 200);
    camera.far = Math.max(100, distance * 20);
    camera.updateProjectionMatrix();
  }

  if (controls) {
    controls.target.copy(center);
    controls.minDistance = maxDim * 0.35;
    controls.maxDistance = maxDim * 8;
    controls.update();
  }
}

export function setCameraView(
  camera: Camera,
  controls: OrbitControlsImpl | null,
  position: [number, number, number],
  target: [number, number, number] = [0, 0.45, 0]
): void {
  camera.position.set(...position);
  if (camera instanceof PerspectiveCamera) {
    camera.updateProjectionMatrix();
  }
  if (controls) {
    controls.target.set(...target);
    controls.update();
  }
}
