from __future__ import annotations

from pathlib import Path

from app.models.manifest import BuildablesPhysicsManifest


def _infer_desc_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".urdf", ".xacro"}:
        return "urdf"
    if ext in {".xml", ".mjcf"}:
        try:
            head = path.read_text(encoding="utf-8", errors="ignore")[:512].lstrip()
            if head.startswith("<robot"):
                return "urdf"
            if head.startswith("<mujoco"):
                return "mjcf"
        except OSError:
            pass
        return "mjcf"
    return "mesh"


def resolve_robot_description_candidates(
    manifest: BuildablesPhysicsManifest, project_dir: Path | None = None
) -> list[tuple[str, Path]]:
    """Return robot description candidates ordered best-first."""
    candidates: list[tuple[str, Path, int]] = []

    def add(path: Path, priority: int) -> None:
        if path.exists():
            candidates.append((_infer_desc_type(path), path.resolve(), priority))

    if project_dir is not None:
        generated = project_dir / "generated" / "robot_description"
        if generated.exists():
            for path in sorted(generated.glob("*.urdf")):
                add(path, 0)
            for path in sorted(generated.glob("*.mjcf")):
                add(path, 0)
        imported = project_dir / "assets" / "imported"
        if imported.exists():
            for path in sorted(imported.glob("*.urdf")):
                add(path, 1)
            for path in sorted(imported.glob("*.xml")):
                add(path, 1)
            for path in sorted(imported.glob("*.mjcf")):
                add(path, 1)

    if manifest.robot_description.urdf_path:
        add(Path(manifest.robot_description.urdf_path), 2)
    if manifest.robot_description.mjcf_path:
        add(Path(manifest.robot_description.mjcf_path), 2)

    preferred = manifest.robot_description.preferred_format
    unique: dict[str, tuple[str, Path, int]] = {}
    for desc_type, path, priority in candidates:
        key = str(path)
        if key not in unique or priority < unique[key][2]:
            unique[key] = (desc_type, path, priority)

    ordered = list(unique.values())
    ordered.sort(key=lambda item: (item[2], 0 if preferred == "urdf" and item[0] == "urdf" else 1 if preferred == "mjcf" and item[0] == "mjcf" else 2))
    return [(desc_type, path) for desc_type, path, _ in ordered]


def resolve_robot_description(manifest: BuildablesPhysicsManifest, project_dir: Path | None = None) -> tuple[str, Path]:
    candidates = resolve_robot_description_candidates(manifest, project_dir)
    if not candidates:
        raise RuntimeError("No robot description file configured or found for active project.")
    return candidates[0]


def load_imported_robot(project_dir: Path, manifest: BuildablesPhysicsManifest) -> dict:
    desc_type, desc_path = resolve_robot_description(manifest, project_dir)
    return {
        "loaded": True,
        "robot_description_type": desc_type,
        "robot_description_path": desc_path,
        "project_mode": manifest.project_mode,
        "project_dir": str(project_dir),
    }
