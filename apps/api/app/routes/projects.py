from pathlib import Path
from uuid import uuid4
import io
import json
import zipfile
import xml.etree.ElementTree as ET

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.genesis.demo_project_setup import ensure_default_robot_dog_ready
from app.services.importers.mesh_validation import validate_urdf_meshes
from app.services.importers.import_validation import build_import_validation, metadata_status_from_validation
from app.services.importers.mjcf_importer import mjcf_to_manifest, parse_mjcf
from app.services.importers.urdf_importer import parse_urdf, urdf_to_manifest
from app.services.cad_import.step_mesh_converter import (
    converter_status,
    export_mapped_meshes,
    export_whole_step_preview,
    inspect_project_step,
    suggest_step_mappings,
)
from app.services.project_store import (
    create_project,
    delete_project,
    get_active_project_id,
    list_projects,
    load_manifest,
    load_or_copy_default_project,
    project_dir,
    save_manifest,
    set_active_project,
)

router = APIRouter(tags=["projects"])


class CreateProjectRequest(BaseModel):
    project_name: str
    project_id: str | None = None


class UploadDiagnostics(BaseModel):
    zip_paths: list[str] = Field(default_factory=list)
    extracted_file_count: int = 0
    urdf_count: int = 0
    mesh_count: int = 0
    skipped_files: list[str] = Field(default_factory=list)
    selected_robot_description: str | None = None
    zip_errors: list[str] = Field(default_factory=list)
    matched_mesh_count: int = 0
    missing_mesh_count: int = 0
    unresolved_references: list[str] = Field(default_factory=list)


MESH_EXTS = {".stl", ".obj", ".glb", ".gltf", ".dae"}


IMPORTABLE_EXTS = {
    ".urdf",
    ".xml",
    ".mjcf",
    ".step",
    ".stp",
    ".glb",
    ".gltf",
    ".obj",
    ".stl",
    ".dae",
    ".mtl",
    ".png",
    ".jpg",
    ".jpeg",
    ".json",
    ".yaml",
    ".yml",
    ".py",
    ".zip",
}


def _safe_zip_member(rel_name: str) -> str | None:
    rel_name = rel_name.replace("\\", "/").lstrip("/")
    if not rel_name or rel_name.endswith("/"):
        return None
    parts = Path(rel_name).parts
    if any(p == ".." for p in parts):
        return None
    return rel_name


def _save_uploaded_files(project_id: str, files: list[UploadFile]) -> tuple[list[Path], UploadDiagnostics]:
    pdir = project_dir(project_id)
    target_dir = pdir / "assets" / "imported"
    target_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []
    diagnostics = UploadDiagnostics()
    extracted = 0

    def _write_bytes(rel_name: str, data: bytes) -> bool:
        nonlocal extracted
        rel_name = rel_name.replace("\\", "/").lstrip("/")
        if not rel_name or rel_name.endswith("/"):
            return False
        file_path = target_dir / rel_name
        suffix = file_path.suffix.lower()
        if suffix and suffix not in IMPORTABLE_EXTS:
            diagnostics.skipped_files.append(f"{rel_name} (unsupported extension)")
            return False
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)
        saved_paths.append(file_path.resolve())
        extracted += 1
        return True

    for upload in files:
        raw_name = (upload.filename or f"file-{uuid4().hex}").replace("\\", "/")
        if raw_name.lower().endswith(".zip"):
            diagnostics.zip_paths.append(raw_name)
            payload = upload.file.read()
            try:
                with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                    for member in archive.namelist():
                        safe = _safe_zip_member(member)
                        if not safe:
                            if member and not member.endswith("/"):
                                diagnostics.skipped_files.append(f"{member} (unsafe path)")
                            continue
                        _write_bytes(safe, archive.read(member))
            except zipfile.BadZipFile as exc:
                diagnostics.zip_errors.append(f"Invalid or corrupt zip '{raw_name}': {exc}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "zip_extract_failed",
                        "title": "Could not extract zip",
                        "explanation": (
                            f"The backend zip extractor failed to read '{raw_name}'. "
                            "This is likely a software import issue — try uploading again or upload extracted files."
                        ),
                        "affected_files": [raw_name],
                        "suggested_actions": [
                            "Upload the zip again",
                            "Upload the extracted meshes folder and URDF separately",
                            "Run preflight retry",
                        ],
                        "copyable_debug_details": str(exc),
                    },
                ) from exc
            except Exception as exc:
                diagnostics.zip_errors.append(f"Zip read error '{raw_name}': {exc}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error_code": "zip_extract_failed",
                        "title": "Zip extraction failed",
                        "explanation": str(exc),
                        "affected_files": [raw_name],
                        "suggested_actions": ["Upload files individually", "Retry upload"],
                        "copyable_debug_details": str(exc),
                    },
                ) from exc
            continue
        suffix = Path(raw_name).suffix.lower()
        if suffix and suffix not in IMPORTABLE_EXTS:
            diagnostics.skipped_files.append(f"{raw_name} (unsupported extension)")
            continue
        _write_bytes(raw_name, upload.file.read())

    diagnostics.extracted_file_count = extracted
    diagnostics.urdf_count = sum(1 for p in saved_paths if p.suffix.lower() == ".urdf")
    diagnostics.mesh_count = sum(1 for p in saved_paths if p.suffix.lower() in MESH_EXTS)
    desc_path, _ = _detect_main_robot_description(saved_paths)
    if desc_path:
        diagnostics.selected_robot_description = str(desc_path)
    return saved_paths, diagnostics


def _enrich_upload_diagnostics(diagnostics: UploadDiagnostics, saved_files: list[Path], desc_path: Path | None) -> UploadDiagnostics:
    if desc_path and desc_path.suffix.lower() == ".urdf":
        parsed = parse_urdf(desc_path)
        mesh_refs = parsed.get("mesh_references", [])
        resolved, missing, _, _ = _mesh_validation_for_project(desc_path, parsed, saved_files)
        diagnostics.matched_mesh_count = len(resolved)
        diagnostics.missing_mesh_count = len(missing)
        diagnostics.unresolved_references = missing[:20]
    return diagnostics


def _mesh_validation_for_project(
    desc_path: Path | None,
    parsed: dict,
    saved_files: list[Path],
) -> tuple[dict[str, str], list[str], list[dict], list[str]]:
    mesh_refs = parsed.get("mesh_references", [])
    mesh_details = parsed.get("mesh_ref_details")
    return validate_urdf_meshes(
        desc_path,
        mesh_refs,
        saved_files,
        mesh_ref_details=mesh_details if isinstance(mesh_details, list) else None,
        auto_map_basenames=True,
    )


def _all_imported_files(project_id: str) -> list[Path]:
    root = project_dir(project_id) / "assets" / "imported"
    if not root.is_dir():
        return []
    return [p.resolve() for p in root.rglob("*") if p.is_file()]


def _revalidate_project(project_id: str, import_mode: str = "robot_mechanism") -> dict:
    manifest = load_manifest(project_id)
    all_files = _all_imported_files(project_id)
    desc_path, desc_type = _detect_main_robot_description(all_files)
    if desc_path is None:
        urdf_path = manifest.robot_description.urdf_path
        if urdf_path:
            desc_path = Path(urdf_path)
            desc_type = "urdf"

    parsed: dict = {"links": [], "joints": [], "mesh_references": [], "mesh_ref_details": [], "urdf_path": None, "mjcf_path": None}
    if desc_path and desc_type == "urdf":
        parsed = parse_urdf(desc_path)
        parsed["urdf_path"] = str(desc_path)
    elif desc_path and desc_type == "mjcf":
        parsed = parse_mjcf(desc_path)
        parsed["mjcf_path"] = str(desc_path)

    mesh_refs = parsed.get("mesh_references", [])
    resolved, missing, mesh_table, auto_map_log = _mesh_validation_for_project(desc_path, parsed, all_files)
    return _persist_import_validation(
        project_id,
        parsed,
        manifest,
        missing,
        resolved,
        mesh_table,
        import_mode,
        auto_map_log=auto_map_log,
    )


def _persist_import_validation(
    project_id: str,
    parsed: dict,
    manifest,
    missing: list[str],
    resolved: dict,
    mesh_table: list[dict],
    import_mode: str,
    *,
    auto_map_log: list[str] | None = None,
) -> dict:
    validation = build_import_validation(
        parsed,
        manifest,
        missing,
        resolved,
        import_mode,
        mesh_table=mesh_table,
        auto_map_log=auto_map_log,
    )
    manifest.metadata_status = metadata_status_from_validation(validation)
    save_manifest(project_id, manifest)
    validation_path = project_dir(project_id) / "import_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    return validation


def _detect_main_robot_description(saved_files: list[Path]) -> tuple[Path | None, str | None]:
    urdf = next((p for p in saved_files if p.suffix.lower() == ".urdf"), None)
    if urdf:
        return urdf, "urdf"
    mjcf = next((p for p in saved_files if p.suffix.lower() in {".xml", ".mjcf"}), None)
    if mjcf:
        try:
            root = ET.fromstring(mjcf.read_text(encoding="utf-8"))
            tag = root.tag.lower()
            if tag.endswith("robot"):
                return mjcf, "urdf"
            if tag.endswith("mujoco"):
                return mjcf, "mjcf"
        except Exception:
            pass
        return mjcf, "mjcf"
    return None, None


@router.post("/projects")
def create_project_endpoint(payload: CreateProjectRequest) -> dict:
    return create_project(payload.project_name, payload.project_id)


@router.get("/projects")
def list_projects_endpoint() -> list[dict]:
    return list_projects()


@router.get("/projects/active")
def get_active_project() -> dict:
    project_id = get_active_project_id()
    if not project_id:
        return {"project_id": None}
    try:
        manifest = load_manifest(project_id)
        return {"project_id": project_id, "project_name": manifest.project_name, "project_mode": manifest.project_mode}
    except FileNotFoundError:
        return {"project_id": None}


@router.get("/projects/{project_id}")
def get_project(project_id: str) -> dict:
    try:
        manifest = load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Project not found: {project_id}") from exc
    return {"project_id": manifest.project_id, "project_name": manifest.project_name}


@router.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: str) -> dict:
    delete_project(project_id)
    if get_active_project_id() == project_id:
        set_active_project(None)
    return {"deleted": True, "project_id": project_id}


@router.post("/projects/{project_id}/activate")
def activate_project(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    set_active_project(project_id)
    return {"project_id": project_id, "project_name": manifest.project_name, "project_mode": manifest.project_mode, "activated": True}


@router.post("/projects/active/clear")
def clear_active_project() -> dict:
    set_active_project(None)
    return {"cleared": True}


@router.post("/projects/import-from-downloads")
def import_from_downloads_robot_dog() -> dict:
    """Import robot_dog_buildables_demo.urdf (+ STEP, meshes/) from the user's Downloads folder."""
    downloads = Path.home() / "Downloads"
    urdf_src = downloads / "robot_dog_buildables_demo.urdf"
    step_src = downloads / "robot_dog_buildables_demo.step"
    meshes_src = downloads / "meshes"

    if not urdf_src.exists():
        raise HTTPException(
            status_code=404,
            detail=f"URDF not found: {urdf_src}. Place robot_dog_buildables_demo.urdf in Downloads.",
        )

    project_id = f"imported-{uuid4().hex[:8]}"
    project_name = "Robot Dog (Downloads)"
    create_project(project_name=project_name, project_id=project_id)
    target_dir = project_dir(project_id) / "assets" / "imported"
    target_dir.mkdir(parents=True, exist_ok=True)

    saved_files: list[Path] = []

    def _copy_into(name: str, src: Path) -> Path:
        dest = target_dir / name
        dest.write_bytes(src.read_bytes())
        saved_files.append(dest.resolve())
        return dest

    urdf_dest = _copy_into(urdf_src.name, urdf_src)
    if step_src.exists():
        _copy_into(step_src.name, step_src)
    if meshes_src.is_dir():
        mesh_target = target_dir / "meshes"
        mesh_target.mkdir(parents=True, exist_ok=True)
        for mesh_file in meshes_src.rglob("*"):
            if mesh_file.is_file():
                rel = mesh_file.relative_to(meshes_src)
                out = mesh_target / rel
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(mesh_file.read_bytes())
                saved_files.append(out.resolve())

    parsed = parse_urdf(urdf_dest)
    parsed["urdf_path"] = str(urdf_dest)
    manifest = urdf_to_manifest(parsed, project_id, project_name, str(urdf_dest))
    manifest.robot_description.urdf_path = str(urdf_dest)

    mesh_refs = parsed.get("mesh_references", [])
    resolved, missing, mesh_table, auto_map_log = _mesh_validation_for_project(urdf_dest, parsed, saved_files)
    validation = build_import_validation(
        parsed,
        manifest,
        missing,
        resolved,
        "robot_mechanism",
        mesh_table=mesh_table,
        auto_map_log=auto_map_log,
    )
    manifest.metadata_status = metadata_status_from_validation(validation)

    for file_path in saved_files:
        if file_path == urdf_dest or (step_src.exists() and file_path.name == step_src.name):
            continue
        suffix = file_path.suffix.lower()
        if suffix not in {".stl", ".obj", ".glb", ".gltf", ".dae"}:
            continue
        manifest.assets.append(
            {
                "id": f"asset-{uuid4().hex[:8]}",
                "name": file_path.stem,
                "type": "stl" if suffix == ".stl" else "other",
                "file_path": str(file_path),
                "original_filename": file_path.name,
                "unit_scale_to_meters": 1.0,
                "visual_only": True,
                "generated": False,
                "source_asset_id": None,
                "notes": "Copied from Downloads/meshes",
            }
        )

    save_manifest(project_id, manifest)
    validation_path = project_dir(project_id) / "import_validation.json"
    validation_path.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    set_active_project(project_id)

    return {
        "project_id": project_id,
        "project_name": project_name,
        "project_mode": "imported_project",
        "activated": True,
        "urdf_path": str(urdf_dest),
        "mesh_files_copied": sum(1 for p in saved_files if p.suffix.lower() == ".stl"),
        "missing_mesh_references": missing,
        "import_validation": validation,
    }


@router.post("/projects/import")
async def import_project(
    project_name: str = Form("Imported Project"),
    import_mode: str = Form("robot_mechanism"),
    files: list[UploadFile] = File(...),
) -> dict:
    project_id = f"imported-{uuid4().hex[:8]}"
    create_project(project_name=project_name, project_id=project_id)
    saved_files, upload_diag = _save_uploaded_files(project_id, files)
    desc_path, desc_type = _detect_main_robot_description(saved_files)
    upload_diag = _enrich_upload_diagnostics(upload_diag, saved_files, desc_path)

    if import_mode == "robot_mechanism" and not desc_path:
        raise HTTPException(status_code=400, detail="Robot/mechanism import requires URDF or MJCF file.")

    if desc_type == "urdf":
        parsed = parse_urdf(desc_path)
        parsed["urdf_path"] = str(desc_path)
        manifest = urdf_to_manifest(parsed, project_id, project_name, str(desc_path))
    elif desc_type == "mjcf":
        parsed = parse_mjcf(desc_path)
        parsed["mjcf_path"] = str(desc_path)
        manifest = mjcf_to_manifest(parsed, project_id, project_name, str(desc_path))
    else:
        # Geometry only import.
        parsed = {"links": [], "joints": [], "mesh_references": [], "urdf_path": None, "mjcf_path": None}
        manifest = load_manifest(project_id)
        manifest.project_mode = "imported_project"
        manifest.project_type = "imported_cad_assembly"
        manifest.controls = {"mode": "joint_command_table"}
        manifest.scenarios = [
            {"id": "passive_gravity", "name": "Passive Gravity", "description": "Passive gravity test for geometry import.", "duration_s": 4.0, "config": {"command_hint": "stand"}}
        ]

    mesh_refs = parsed.get("mesh_references", [])
    resolved, missing, mesh_table, auto_map_log = _mesh_validation_for_project(desc_path, parsed, saved_files)
    control_script = next((str(path) for path in saved_files if path.suffix.lower() == ".py"), None)
    if control_script:
        manifest.controls["control_script_path"] = control_script
    for file_path in saved_files:
        suffix = file_path.suffix.lower()
        asset_type = {
            ".urdf": "urdf",
            ".xml": "mjcf",
            ".mjcf": "mjcf",
            ".step": "step",
            ".stp": "step",
            ".glb": "glb",
            ".gltf": "gltf",
            ".obj": "obj",
            ".stl": "stl",
            ".dae": "other",
        }.get(suffix, "other")
        manifest.assets.append(
            {
                "id": f"asset-{uuid4().hex[:8]}",
                "name": file_path.stem,
                "type": asset_type,
                "file_path": str(file_path),
                "original_filename": file_path.name,
                "unit_scale_to_meters": 1.0,
                "visual_only": asset_type in {"glb", "gltf", "obj", "stl"},
                "generated": False,
                "source_asset_id": None,
                "notes": "Imported file",
            }
        )

    validation = _persist_import_validation(
        project_id,
        parsed,
        manifest,
        missing,
        resolved,
        mesh_table,
        import_mode,
        auto_map_log=auto_map_log,
    )
    summary = validation.get("launch_summary") or {}
    return {
        "project_id": project_id,
        "project_name": project_name,
        "project_mode": "imported_project",
        "import_mode": import_mode,
        "files_saved": len(saved_files),
        "detected_robot_description": desc_type,
        "import_validation": validation,
        "launch_summary": summary,
        "launchable_web": bool(summary.get("launchable_web")),
        "launchable": bool(summary.get("launchable")),
        "missing_mesh_count": int(summary.get("meshesMissing") or len(missing)),
        "first_missing_mesh": missing[0] if missing else None,
        "auto_map_log": auto_map_log,
        "upload_diagnostics": upload_diag.model_dump(),
    }


@router.post("/projects/{project_id}/assets/upload")
async def upload_project_assets(project_id: str, files: list[UploadFile] = File(...)) -> dict:
    try:
        manifest = load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    saved_files, upload_diag = _save_uploaded_files(project_id, files)
    desc_path, _ = _detect_main_robot_description(saved_files)
    upload_diag = _enrich_upload_diagnostics(upload_diag, saved_files, desc_path)
    validation = _revalidate_project(project_id)
    summary = validation.get("launch_summary") or {}
    missing = validation.get("geometry", {}).get("missing_mesh_references") or []
    return {
        "project_id": project_id,
        "files_saved": len(saved_files),
        "import_validation": validation,
        "launch_summary": summary,
        "launchable_web": bool(summary.get("launchable_web")),
        "missing_mesh_count": int(summary.get("meshesMissing") or len(missing)),
        "first_missing_mesh": missing[0] if missing else None,
        "upload_diagnostics": upload_diag.model_dump(),
    }


@router.get("/projects/{project_id}/import-validation")
def get_import_validation(project_id: str) -> dict:
    path = project_dir(project_id) / "import_validation.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Import validation not found for project.")
    validation = json.loads(path.read_text(encoding="utf-8"))
    summary = validation.get("launch_summary")
    if isinstance(summary, dict):
        validation = {**summary, **validation}
    return validation


class StepMeshMappingRequest(BaseModel):
    mappings: dict[str, str] = {}
    whole_preview: bool = False


@router.get("/projects/{project_id}/step/converter-status")
def step_converter_status(project_id: str) -> dict:
    load_manifest(project_id)
    return {**converter_status(), "project_id": project_id}


@router.get("/projects/{project_id}/step/inspect")
def step_inspect(project_id: str) -> dict:
    try:
        load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    result = inspect_project_step(project_id)
    validation_path = project_dir(project_id) / "import_validation.json"
    missing: list[str] = []
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        missing = validation.get("geometry", {}).get("missing_mesh_references") or []
    parts = [str(p.get("name")) for p in result.get("parts") or [] if isinstance(p, dict)]
    result["suggested_mappings"] = suggest_step_mappings(missing, parts)
    result["missing_mesh_references"] = missing
    return result


@router.post("/projects/{project_id}/step/generate-meshes")
def step_generate_meshes(project_id: str, payload: StepMeshMappingRequest) -> dict:
    try:
        manifest = load_manifest(project_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    pdir = project_dir(project_id)
    from app.services.cad_import.step_mesh_converter import find_project_step_file

    step_path = find_project_step_file(pdir)
    if step_path is None:
        raise HTTPException(status_code=400, detail="No STEP file uploaded for this project.")

    urdf_path = manifest.robot_description.urdf_path
    if not urdf_path:
        raise HTTPException(status_code=400, detail="No URDF path in project manifest.")

    urdf_file = Path(urdf_path)
    if not urdf_file.is_file():
        raise HTTPException(status_code=400, detail=f"URDF not found on disk: {urdf_path}")

    if payload.whole_preview:
        out = pdir / "generated" / "step_preview" / "whole_assembly.stl"
        try:
            preview = export_whole_step_preview(step_path, out)
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"preview": preview, "validation": _revalidate_project(project_id)}

    if not payload.mappings:
        inspect = inspect_project_step(project_id)
        missing = []
        validation_path = pdir / "import_validation.json"
        if validation_path.exists():
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            missing = validation.get("geometry", {}).get("missing_mesh_references") or []
        parts = [str(p.get("name")) for p in inspect.get("parts") or [] if isinstance(p, dict)]
        suggestions = suggest_step_mappings(missing, parts)
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Provide STEP part mappings for each missing URDF mesh path.",
                "suggested_mappings": suggestions,
                "parts": inspect.get("parts") or [],
            },
        )

    try:
        export_result = export_mapped_meshes(pdir, urdf_file, step_path, payload.mappings)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    validation = _revalidate_project(project_id)
    summary = validation.get("launch_summary") or {}
    return {
        "export": export_result,
        "import_validation": validation,
        "launch_summary": summary,
        "launchable_web": bool(summary.get("launchable_web")),
        "missing_mesh_count": int(summary.get("meshesMissing") or 0),
    }


@router.get("/projects/{project_id}/robot-description")
def get_robot_description(project_id: str) -> dict:
    manifest = load_manifest(project_id)
    return {
        "project_id": project_id,
        "project_mode": manifest.project_mode,
        "preferred_format": manifest.robot_description.preferred_format,
        "urdf_path": manifest.robot_description.urdf_path,
        "mjcf_path": manifest.robot_description.mjcf_path,
        "generated_from_manifest": manifest.robot_description.generated_from_manifest,
    }


@router.get("/projects/{project_id}/assets/resolution-status")
def get_assets_resolution_status(project_id: str) -> dict:
    validation_path = project_dir(project_id) / "import_validation.json"
    if not validation_path.exists():
        return {"resolved_meshes": {}, "missing_mesh_references": []}
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    return {
        "resolved_meshes": validation.get("geometry", {}).get("resolved_meshes", {}),
        "missing_mesh_references": validation.get("geometry", {}).get("missing_mesh_references", []),
    }


@router.post("/projects/default-robot-dog/load")
def load_default_robot_dog() -> dict:
    try:
        loaded = load_or_copy_default_project("default-robot-dog")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    pdir = project_dir("default-robot-dog")
    manifest = load_manifest("default-robot-dog")
    if ensure_default_robot_dog_ready(manifest, pdir):
        save_manifest("default-robot-dog", manifest)
    set_active_project("default-robot-dog")
    return loaded


@router.post("/projects/default-robot-arm/load")
def load_default_robot_arm() -> dict:
    try:
        loaded = load_or_copy_default_project("default-robot-arm")
        set_active_project("default-robot-arm")
        return loaded
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
