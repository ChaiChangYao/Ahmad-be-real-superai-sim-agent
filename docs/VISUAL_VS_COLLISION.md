# Visual vs Collision

## Three Layers
1. Source CAD (`STEP/STP`) when provided.
2. Visual mesh/procedural visual model for viewport rendering.
3. Collision shell used by Genesis for stepping and contacts.

## Why This Split Exists
- Source CAD is not enough for simulation.
- Real-time simulation needs simplified collision geometry.
- Visual quality and physics stability are separate concerns.

## UI Guidance
Use viewport toggles to inspect:
- visual representation
- collision shell
- both overlays

Important copy:
\"Visual mesh is for rendering. Collision mesh is what Genesis uses for real-time physics.\"
