# URDF / MJCF Import

## Supported import files
- `.urdf`
- `.xml` / `.mjcf`
- geometry: `.step`, `.stp`, `.glb`, `.gltf`, `.obj`, `.stl`, `.dae`
- materials/textures: `.mtl`, `.png`, `.jpg`, `.jpeg`
- optional metadata/scripts: `.json`, `.yaml`, `.yml`, `.py`

## URDF parser extracts
- links
- joints (fixed/revolute/prismatic/continuous)
- mesh filename references
- inertial mass (when provided)
- basic material tags
- transmission names

## MJCF parser extracts
- bodies
- joints
- geom mesh references
- actuators

## Mesh path resolution
Resolver handles:
- `package://...`
- `file://...`
- relative paths
- basename matching fallback

Unresolved references are returned in import validation as `missing_mesh_references`.

## Limitations
- Not all advanced URDF/MJCF tags are fully mapped yet.
- Full Nyx and advanced renderer artifacts are scaffolded but not complete parity with all upstream demos.
- Missing inertial/collision tags are imported with warnings and default placeholders for iterative testing.
