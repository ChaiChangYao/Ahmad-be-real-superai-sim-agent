# CAD Import Pipeline

## Supported Input
- STEP / STP
- STL
- OBJ
- GLB / GLTF

Default demo note:
- Uploads are optional. `default-robot-dog` runs without any imported CAD.

## Import Flow
1. Upload file into project assets.
2. Detect asset type.
3. For STEP:
   - store source CAD
   - try converter tools
   - if converter missing, show exact setup-blocking message with required tool.
4. For mesh files:
   - load as visual asset.
5. Generate collision primitives for physics.
6. Build or update links/joints/actuators metadata.
7. Generate URDF/MJCF artifacts.

## Visual vs Physics
- Visual mesh: high-quality rendering in viewport.
- Collision mesh/primitives: stable dynamics and fast local execution.
- Source CAD remains source-of-truth geometry metadata, not direct real-time collision.

## Joint Mapping
- Manual definition is always supported.
- Auto Guess Joints heuristic can propose candidates from names and proximity.
- Auto-guessed joints must be user confirmed.

Required UI copy:
- `STEP is source CAD. Genesis simulation uses generated visual mesh, collision primitives, and robot-description metadata.`
