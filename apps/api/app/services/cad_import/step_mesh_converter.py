"""Optional STEP → mesh export via FreeCAD CLI (freecadcmd / FreeCADCmd)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Any

from app.services.cad_import.step_importer import step_converter_available
from app.services.importers.asset_resolver import normalize_mesh_ref


def converter_status() -> dict[str, Any]:
    available = step_converter_available()
    return {
        "available": available,
        "dependency": "FreeCAD CLI (freecadcmd or FreeCADCmd on PATH)",
        "install_hint": "Install FreeCAD and ensure freecadcmd is on PATH to export meshes from STEP.",
        "fallback": "Without FreeCAD, upload STL/OBJ meshes or use skeleton preview.",
    }


def find_project_step_file(project_dir_path: Path) -> Path | None:
    return _find_step_file(project_dir_path)


def _find_step_file(project_dir: Path) -> Path | None:
    imported = project_dir / "assets" / "imported"
    if not imported.is_dir():
        return None
    for path in sorted(imported.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".step", ".stp"}:
            return path
    return None


def _run_freecad_script(script: str, timeout_s: int = 180) -> tuple[int, str, str]:
    cmd = None
    for binary in ("freecadcmd", "FreeCADCmd", "FreeCADCmd.exe"):
        if shutil.which(binary):
            cmd = [binary, "-c", script]
            break
    if cmd is None:
        raise RuntimeError("FreeCAD CLI not found. Install FreeCAD and add freecadcmd to PATH.")

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def inspect_step_parts(step_path: Path) -> dict[str, Any]:
    if not step_path.is_file():
        raise FileNotFoundError(f"STEP file not found: {step_path}")
    if not step_converter_available():
        return {**converter_status(), "parts": [], "error": "FreeCAD CLI not installed"}

    step_esc = str(step_path.resolve()).replace("\\", "\\\\")
    script = textwrap.dedent(
        f"""
        import json, FreeCAD as App, Import
        doc = App.newDocument("Inspect")
        Import.insert(r"{step_esc}", doc.Name)
        parts = []
        for obj in doc.Objects:
            if hasattr(obj, "Shape") and obj.Shape and not obj.Shape.isNull():
                parts.append({{"name": obj.Label, "type": obj.TypeId}})
        print("BUILDABLES_JSON:" + json.dumps({{"parts": parts}}))
        App.closeDocument(doc.Name)
        """
    )
    code, stdout, stderr = _run_freecad_script(script)
    if code != 0:
        return {"parts": [], "error": stderr or stdout or "FreeCAD inspect failed"}
    for line in stdout.splitlines():
        if line.startswith("BUILDABLES_JSON:"):
            payload = json.loads(line[len("BUILDABLES_JSON:") :])
            return {**converter_status(), **payload, "step_path": str(step_path)}
    return {"parts": [], "error": stdout or stderr or "No parts returned from FreeCAD"}


def suggest_step_mappings(missing_mesh_refs: list[str], part_names: list[str]) -> list[dict[str, str | None]]:
    suggestions: list[dict[str, str | None]] = []
    part_lower = {p.lower(): p for p in part_names}
    for ref in missing_mesh_refs:
        base = Path(normalize_mesh_ref(ref)).stem.lower()
        match = part_lower.get(base)
        if not match:
            for pname, original in part_lower.items():
                if base in pname or pname in base:
                    match = original
                    break
        suggestions.append({"urdf_mesh_path": ref, "suggested_step_part": match})
    return suggestions


def export_step_part(step_path: Path, part_name: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    step_esc = str(step_path.resolve()).replace("\\", "\\\\")
    out_esc = str(output_path.resolve()).replace("\\", "\\\\")
    part_esc = part_name.replace("\\", "\\\\")
    script = textwrap.dedent(
        f"""
        import FreeCAD as App, Import, Mesh, MeshPart
        doc = App.newDocument("Export")
        Import.insert(r"{step_esc}", doc.Name)
        target = None
        for obj in doc.Objects:
            if obj.Label == r"{part_esc}" and hasattr(obj, "Shape"):
                target = obj
                break
        if target is None:
            raise RuntimeError("STEP part not found: {part_esc}")
        mesh = MeshPart.meshFromShape(Shape=target.Shape, LinearDeflection=0.1, AngularDeflection=0.5)
        mesh.write(r"{out_esc}")
        App.closeDocument(doc.Name)
        """
    )
    code, stdout, stderr = _run_freecad_script(script, timeout_s=300)
    if code != 0 or not output_path.is_file():
        raise RuntimeError(stderr or stdout or f"Failed to export STEP part {part_name}")


def export_whole_step_preview(step_path: Path, output_path: Path) -> dict[str, Any]:
    """Level 1: export entire STEP assembly to one STL (static preview only)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    step_esc = str(step_path.resolve()).replace("\\", "\\\\")
    out_esc = str(output_path.resolve()).replace("\\", "\\\\")
    script = textwrap.dedent(
        f"""
        import FreeCAD as App, Import, Mesh, MeshPart
        doc = App.newDocument("Whole")
        Import.insert(r"{step_esc}", doc.Name)
        shapes = [o for o in doc.Objects if hasattr(o, "Shape") and o.Shape and not o.Shape.isNull()]
        if not shapes:
            raise RuntimeError("No solid bodies found in STEP")
        compound = App.ActiveDocument.addObject("Part::Compound", "Compound")
        compound.Shapes = [o.Shape for o in shapes]
        mesh = MeshPart.meshFromShape(Shape=compound.Shape, LinearDeflection=0.1, AngularDeflection=0.5)
        mesh.write(r"{out_esc}")
        App.closeDocument(doc.Name)
        """
    )
    code, stdout, stderr = _run_freecad_script(script, timeout_s=300)
    if code != 0 or not output_path.is_file():
        raise RuntimeError(stderr or stdout or "Whole STEP export failed")
    return {
        "mode": "whole_step_preview",
        "output_path": str(output_path),
        "note": "Static preview mesh only. Does not satisfy per-link URDF visuals.",
    }


def export_mapped_meshes(
    project_dir: Path,
    urdf_path: Path,
    step_path: Path,
    mappings: dict[str, str],
) -> dict[str, Any]:
    """Level 2: map STEP part names to URDF mesh paths and export STL files."""
    urdf_dir = urdf_path.parent
    exported: list[dict[str, str]] = []
    errors: list[str] = []
    for urdf_ref, step_part in mappings.items():
        if not step_part:
            errors.append(f"No STEP part mapped for {urdf_ref}")
            continue
        normalized = normalize_mesh_ref(urdf_ref)
        out_path = urdf_dir / normalized
        try:
            export_step_part(step_path, step_part, out_path)
            exported.append({"urdf_mesh_path": urdf_ref, "step_part": step_part, "output_path": str(out_path)})
        except Exception as exc:
            errors.append(f"{urdf_ref} ← {step_part}: {exc}")

    return {
        "exported": exported,
        "errors": errors,
        "exported_count": len(exported),
    }


def inspect_project_step(project_id: str) -> dict[str, Any]:
    from app.services.project_store import project_dir

    pdir = project_dir(project_id)
    step_path = _find_step_file(pdir)
    if step_path is None:
        return {**converter_status(), "stepUploaded": False, "parts": [], "error": "No STEP file in project"}
    result = inspect_step_parts(step_path)
    result["stepUploaded"] = True
    result["step_path"] = str(step_path)
    return result
