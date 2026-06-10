from __future__ import annotations

from app.models.manifest import BuildablesPhysicsManifest
from app.services.genesis.genesis_runtime import genesis_runtime
from app.services.genesis_catalog.project_type_rules import infer_project_type
from app.services.genesis_catalog.test_catalog import get_test_catalog


def _has_manifest_field(manifest: BuildablesPhysicsManifest, field_name: str) -> bool:
    value = getattr(manifest, field_name, None)
    if value is None:
        return False
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _required_field_reason(field_name: str) -> str:
    return f"missing required manifest field: {field_name}"


def build_test_availability(manifest: BuildablesPhysicsManifest) -> list[dict]:
    project_type = infer_project_type(manifest)
    genesis_status = genesis_runtime.status()
    out: list[dict] = []
    for test in get_test_catalog():
        reasons: list[str] = []
        status = "available"
        if project_type not in test["supported_project_types"]:
            status = "not_applicable"
            reasons.append(f"project_type={project_type} not supported")

        if status == "available":
            for field_name in test.get("required_manifest_fields", []):
                if not _has_manifest_field(manifest, field_name):
                    status = "missing_metadata"
                    reasons.append(_required_field_reason(field_name))

        if status == "available" and not genesis_status.installed:
            status = "missing_genesis_feature"
            reasons.append("Genesis not installed")

        if status == "available" and not test.get("implemented", False):
            status = "missing_genesis_feature"
            reasons.append("Test exists in catalog but implementation is pending in Buildables")

        out.append({**test, "status": status, "reasons": reasons, "project_type": project_type})
    return out
