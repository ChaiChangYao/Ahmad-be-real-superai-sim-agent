"""Honesty rules — never invent solver metrics."""
from __future__ import annotations

from app.services.agentic.reporting.schemas import SimulationLimitation


def limitations_for_test(
    test_id: str,
    *,
    skeleton_fallback: bool = False,
    readiness_only: bool = False,
    telemetry_demo: bool = False,
) -> list[SimulationLimitation]:
    items: list[SimulationLimitation] = []

    if skeleton_fallback:
        items.append(
            SimulationLimitation(
                limitation_id="skeleton_fallback",
                category="visual",
                text="Skeleton/fallback collision was used — this is not full visual mesh validation.",
                test_id=test_id,
            )
        )

    if readiness_only or test_id in ("fea_readiness", "cfd_readiness"):
        items.append(
            SimulationLimitation(
                limitation_id="readiness_only",
                category="solver",
                text="This is a readiness checklist only — no FEA/CFD solver was run and no stress or flow numbers are reported.",
                test_id=test_id,
            )
        )

    if test_id == "thermal_grid_readiness" or telemetry_demo:
        items.append(
            SimulationLimitation(
                limitation_id="thermal_demo",
                category="thermal",
                text="Temperature grid values may be demo/placeholder fields — not validated against real material properties.",
                test_id=test_id,
            )
        )

    if test_id in ("gravity_stability", "joint_sweep"):
        items.append(
            SimulationLimitation(
                limitation_id="no_structural",
                category="structural",
                text="No stress, buckling, or fatigue analysis was performed.",
                test_id=test_id,
            )
        )

    if test_id == "imu_sensor":
        items.append(
            SimulationLimitation(
                limitation_id="imu_noise",
                category="sensor",
                text="IMU noise model and calibration were not validated against hardware.",
                test_id=test_id,
            )
        )

    items.append(
        SimulationLimitation(
            limitation_id="genesis_physics",
            category="general",
            text="Results reflect Genesis rigid-body simulation fidelity — not manufacturing tolerances or real-world wear.",
            test_id=test_id,
        )
    )
    return items


def standard_disclaimer(test_id: str) -> str:
    if test_id in ("fea_readiness", "cfd_readiness"):
        return (
            "This report summarizes input readiness only. It does not contain finite-element "
            "or CFD solver results. Upload complete geometry and boundary conditions before "
            "running external analysis tools."
        )
    return (
        "This report is generated from recorded simulation artifacts. It describes what was "
        "observed in the run — not guaranteed real-world performance."
    )
