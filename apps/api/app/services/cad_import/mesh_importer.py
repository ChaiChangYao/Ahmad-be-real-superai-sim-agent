from pathlib import Path


def import_mesh_asset(project_assets_dir: Path, filename: str, data: bytes) -> Path:
    project_assets_dir.mkdir(parents=True, exist_ok=True)
    out = project_assets_dir / filename
    out.write_bytes(data)
    return out
