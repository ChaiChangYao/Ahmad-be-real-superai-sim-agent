# Import and Base Mode

## Import Priority

- URDF/MJCF defines assembly, joints, and articulated behavior.
- STEP is source CAD and visual reference only.
- GLB/OBJ/STL are visual/collision mesh sources.

## Base Modes

- `fixed_to_world`: bolted base, no gravity topple of base.
- `free_floating`: base can move/fall/topple.
- `ground_contact`: free base with ground contact tests.
- `anchored_mechanism`: constrained mounting behavior.

## Key Behavior

- Fixed-base robots do not topple under gravity-only conditions.
- Free-base robots can topple if unstable.
- Passive gravity tests should default to free base unless explicitly overridden.
