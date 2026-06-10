"""Lightweight user goal parser — maps text to candidate test IDs without hallucination."""
from __future__ import annotations

import re

from pydantic import BaseModel, Field

# test_id -> trigger phrases (order matters for specificity)
_GOAL_PATTERNS: list[tuple[str, list[str]]] = [
    ("cfd_readiness", ["cfd", "computational fluid", "aerodynamic", "fluid dynamics", "wind tunnel"]),
    ("fea_readiness", ["fea", "finite element", "stress analysis", "structural analysis", "von mises"]),
    ("imu_sensor", ["imu", "accelerometer", "gyro", "angular velocity", "linear acceleration", "inertial"]),
    ("contact_force", ["contact force", "contact", "foot force", "ground reaction", "force sensor"]),
    ("depth_camera", ["depth camera", "depth image", "rgbd", "camera sensor", "depth frame"]),
    ("thermal_grid_readiness", ["thermal", "temperature grid", "heatmap", "heat map", "thermal sensor"]),
    (
        "joint_sweep",
        [
            "joint sweep",
            "joint range",
            "joint movement",
            "test movement",
            "sweep joint",
            "collision sweep",
            "can this move",
            "see if it works",
            "walk",
            "gait",
            "locomotion",
            "movement",
            "joints",
            "joint",
        ],
    ),
    ("gravity_stability", ["gravity", "drop test", "stability", "balance", "stand", "tip over", "fall"]),
    ("lidar", ["lidar", "laser scan", "point cloud"]),
]

_AMBIGUOUS_PAIRS = [
    ({"gravity_stability", "joint_sweep"}, "Do you want a static gravity/balance test or joint motion sweep?"),
    ({"imu_sensor", "contact_force"}, "Do you want IMU telemetry or contact force data?"),
]


class GoalParseResult(BaseModel):
    raw_goal: str = ""
    candidate_tests: list[str] = Field(default_factory=list)
    unknown_terms: list[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarifying_questions: list[str] = Field(default_factory=list)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def parse_user_goal(user_goal: str | None) -> GoalParseResult:
    if not user_goal or not user_goal.strip():
        return GoalParseResult(raw_goal=user_goal or "")

    text = _normalize(user_goal)
    candidates: list[str] = []
    matched_phrases: set[str] = set()

    for test_id, phrases in _GOAL_PATTERNS:
        for phrase in phrases:
            if phrase in text:
                if test_id not in candidates:
                    candidates.append(test_id)
                matched_phrases.add(phrase)
                break

    # Map generic "telemetry" / "sensor" to IMU if no specific sensor matched
    if not candidates and any(w in text for w in ("telemetry", "sensor", "sensors")):
        candidates.append("imu_sensor")

    # Map "simulation" / "physics" to gravity if nothing else
    if not candidates and any(w in text for w in ("simulate", "simulation", "physics test")):
        candidates.append("gravity_stability")

    # Demo / works intent — recommend motion + stability when joints may exist
    if any(w in text for w in ("demo", "see if it works", "does it work", "can do a demo")):
        if "joint_sweep" not in candidates:
            candidates.append("joint_sweep")
        if "gravity_stability" not in candidates:
            candidates.append("gravity_stability")

    # Load / payload hints
    if re.search(r"\d+\s*n\b", text) or "payload" in text or "load" in text:
        if "gravity_stability" not in candidates:
            candidates.append("gravity_stability")
        if "fea_readiness" not in candidates and "stress" in text:
            candidates.append("fea_readiness")

    unknown: list[str] = []
    tokens = set(re.findall(r"[a-z]{3,}", text))
    known_words = set()
    for _, phrases in _GOAL_PATTERNS:
        for p in phrases:
            known_words.update(p.split())
    for tok in tokens:
        if tok not in known_words and tok not in {
            "the", "and", "can", "run", "want", "test", "my", "this", "that", "with", "for", "from",
            "robot", "dog", "arm", "file", "files", "upload", "uploaded", "does", "will", "have",
        }:
            if len(unknown) < 5:
                unknown.append(tok)

    questions: list[str] = []
    candidate_set = set(candidates)
    for pair, question in _AMBIGUOUS_PAIRS:
        if pair.issubset(candidate_set):
            questions.append(question)

    if "cfd" in text or "fluid" in text:
        questions.append(
            "CFD readiness checks domain and boundary conditions — Genesis does not run a full CFD solver in MVP.",
        )
    if "fea" in text or "finite element" in text:
        questions.append(
            "FEA readiness requires material, constraints, and loads — full FEA solver is not implemented yet.",
        )

    return GoalParseResult(
        raw_goal=user_goal,
        candidate_tests=candidates,
        unknown_terms=unknown[:5],
        needs_clarification=len(questions) > 0,
        clarifying_questions=questions,
    )
