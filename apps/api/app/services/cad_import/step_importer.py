from pathlib import Path
import shutil


def step_converter_available() -> bool:
    return shutil.which("freecadcmd") is not None


def import_step_source(project_assets_dir: Path, filename: str, data: bytes) -> tuple[Path, str | None]:
    project_assets_dir.mkdir(parents=True, exist_ok=True)
    out = project_assets_dir / filename
    out.write_bytes(data)
    if step_converter_available():
        return out, None
    return out, "STEP imported as source CAD, but converter missing. Install FreeCAD CLI to generate visual mesh from STEP on Windows."
