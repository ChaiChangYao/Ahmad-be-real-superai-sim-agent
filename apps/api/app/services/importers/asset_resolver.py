from __future__ import annotations



import re

from pathlib import Path, PureWindowsPath
from urllib.parse import unquote





def normalize_mesh_ref(ref: str) -> str:

    """Normalize package://, file://, Windows, and relative URDF mesh paths."""

    cleaned = ref.strip().replace("\\", "/")

    if not cleaned:

        return cleaned



    lower = cleaned.lower()

    if lower.startswith("file:///"):

        # file:///C:/path or file:///c%3A/path

        rest = cleaned[8:]

        if re.match(r"^[a-zA-Z]:", rest):

            cleaned = rest

        elif rest.startswith("/") and len(rest) > 3 and rest[2] == ":":

            cleaned = rest.lstrip("/")

        else:

            cleaned = rest

    elif lower.startswith("file://"):

        cleaned = cleaned[7:]



    cleaned = unquote(cleaned) if "%" in cleaned else cleaned



    if cleaned.lower().startswith("package://"):

        cleaned = cleaned[len("package://") :]

        if "/" in cleaned:

            cleaned = cleaned.split("/", 1)[1]



    # Windows absolute path embedded in URDF

    if re.match(r"^[a-zA-Z]:/", cleaned):

        cleaned = str(PureWindowsPath(cleaned)).replace("\\", "/")



    return cleaned.lstrip("/")





def resolve_asset_references(references: list[str], uploaded_files: list[Path]) -> tuple[dict[str, str], list[str]]:

    by_name = {path.name.lower(): path for path in uploaded_files}

    by_rel = {str(path).replace("\\", "/").lower(): path for path in uploaded_files}

    resolved: dict[str, str] = {}

    missing: list[str] = []

    for ref in references:

        normalized = normalize_mesh_ref(ref)

        key_name = Path(normalized).name.lower()

        key_rel = normalized.lower()

        if key_rel in by_rel:

            resolved[ref] = str(by_rel[key_rel])

            continue

        if key_name in by_name:

            resolved[ref] = str(by_name[key_name])

            continue

        missing.append(ref)

    return resolved, missing





def resolve_mesh_references_on_disk(

    urdf_path: Path | None,

    references: list[str],

) -> tuple[dict[str, str], list[str], list[dict]]:

    """Resolve URDF mesh paths against files on disk relative to the URDF directory."""

    if urdf_path is None:

        return {}, list(dict.fromkeys(references)), [

            {

                "urdf_path": ref,

                "resolved_local_path": "",

                "found": False,

                "file_type": Path(normalize_mesh_ref(ref)).suffix.lower().lstrip("."),

                "usage": "visual/collision",

                "status": "missing",

                "action_needed": "Upload mesh file",

            }

            for ref in references

        ]



    urdf_dir = urdf_path.parent

    resolved: dict[str, str] = {}

    missing: list[str] = []

    table: list[dict] = []

    seen: set[str] = set()



    for ref in references:

        if ref in seen:

            continue

        seen.add(ref)

        normalized = normalize_mesh_ref(ref)

        candidate = urdf_dir / normalized

        found = candidate.is_file()

        entry = {

            "urdf_path": ref,

            "resolved_local_path": str(candidate.resolve()) if found else str(candidate),

            "found": found,

            "file_type": candidate.suffix.lower().lstrip(".") or "unknown",

            "usage": "visual/collision",

            "status": "found" if found else "missing",

            "action_needed": "" if found else "Upload mesh or zip bundle",

        }

        table.append(entry)

        if found:

            resolved[ref] = str(candidate.resolve())

        else:

            missing.append(ref)



    return resolved, missing, table


