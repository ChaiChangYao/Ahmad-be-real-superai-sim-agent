# Import Project Flow

Buildables Sim Sandbox now supports **Imported Project Mode** where uploaded robot/mechanism definitions become the active simulation target.

## Core rule
- `STEP/mesh` = what it looks like.
- `URDF/MJCF` = how it is assembled and moves.
- `manifest/component metadata` = mass/material/actuator/sensor/control semantics.
- `Genesis` = where it is physically tested.

## Flow
1. Open `Import Project`.
2. Choose import mode:
   - Robot/mechanism project
   - CAD geometry only
   - Existing Buildables package
3. Upload files (`URDF`/`MJCF` + meshes, optional STEP, optional script/metadata).
4. Review Import Validation:
   - links/joints counts
   - mesh references resolved/missing
   - inertial/material/collision metadata gaps
   - simulation readiness level
5. Click `Load Imported Project`.
6. The app activates the imported project and viewer switches away from default robot dog.

## Passive gravity behavior
If imported robot tips/falls, that can be a valid simulation outcome (e.g. COM/base/torque/control issues), not a UI error.

## Readiness levels
- Geometry only: visual inspection only until motion metadata is added.
- Passive ready: can run gravity/drop and collision tests.
- Joint ready: joints found, can run joint sweep/mechanism motion.
- Controlled ready: actuator/control metadata found.
