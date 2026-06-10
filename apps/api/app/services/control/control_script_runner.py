from __future__ import annotations


def run_control_script(script_text: str, context: dict | None = None) -> dict:
    # Placeholder execution contract; secure sandboxing is intentionally out of scope for this local MVP.
    return {
        "executed": False,
        "reason": "Control script runtime is metadata-only placeholder in this build.",
        "script_preview": script_text[:120],
        "context_keys": sorted((context or {}).keys()),
    }
