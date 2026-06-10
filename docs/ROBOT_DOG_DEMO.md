# Robot Dog Demo

The default demo project is `default-robot-dog` and works with no uploaded files.

## Contents
- Quadruped body and leg links
- 8 actuated joints (hip + knee for 4 legs)
- Internal electronics blocks (controller, battery, IMU, depth sensor)
- Wire route objects with mass
- Scenario suite for balance, locomotion, terrain, payload, torque, sensing, and fit checks

## Control Scheme
- `W`: walk forward
- `S`: walk backward
- `A`: turn left
- `D`: turn right
- `Space`: jump
- `R`: reset
- `Esc`: emergency stop

## What the Demo Proves
- Local manifest-driven simulation flow
- Scenario pass/fail metrics and logs
- Internal component placement effects on robot behavior metrics

## Known Limits
- This prototype is not final certification analysis.
- CAD conversion depth depends on local converter tooling availability.
- Wire behavior uses route checks and mass approximations.

## Verification Commands
- `python apps/api/app/scripts/run_default_robot_dog_genesis_smoke_test.py`
- `python apps/api/app/scripts/run_default_robot_dog_keyboard_smoke_test.py`
- `python apps/api/app/scripts/run_default_robot_dog_scenario_suite.py`
