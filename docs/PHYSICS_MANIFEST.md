# Buildables Physics Manifest

The manifest defines a simulation-ready package for robot behavior validation.

## Core Sections
- `assets`: source CAD/mesh files and generated assets.
- `materials`: density, friction, restitution, plus optional strength/thermal placeholders.
- `links`: physical body parts with mass, transform, and collision references.
- `joints`: kinematic relationships, limits, damping, friction.
- `actuators`: motor/servo mapping and limits.
- `electronics`: internal component blocks (battery, controller, IMU, sensors).
- `sensors`: mounted sensors and update settings.
- `wires`: cable routes with mass and bend constraints.
- `collision_primitives`: simulation collision geometry separated from visual mesh.
- `robot_description`: generated URDF/MJCF paths.
- `scenarios`: selectable test scenarios.

## Modeling Rule
- Visual mesh is for viewport quality.
- Physics collision is simplified and explicit.
- STEP source alone is not simulation-ready without links/joints/actuators/collision metadata.

## Validation Expectations
- IDs unique.
- References resolvable.
- Positive masses and dimensions.
- Warning for placeholders and non-certification scope.
