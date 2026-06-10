# Physics Failure Tests

These tests are intended to surface physical failure modes, not hide them.

## Test Types

- Passive gravity / drop
- Lateral push / topple
- Payload load
- Torque margin / stall proxy
- Contact / collision
- Deformation proxy

## Reporting Rules

- Falling/toppling is a valid physics result.
- `genesis_used` can only be `true` if a Genesis scene was stepped.
- If a value is computed from state instead of direct solver API, mark as `derived_from_genesis_state`.

## Engineering Honesty

- Deformation proxy and stress proxy are not certified FEA.
- Reports must explicitly label approximation.
