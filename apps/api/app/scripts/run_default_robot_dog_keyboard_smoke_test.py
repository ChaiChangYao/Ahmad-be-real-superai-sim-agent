from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.project_store import load_manifest
from app.services.genesis.scenario_runner import run_interactive_segment
from app.services.genesis.genesis_runtime import genesis_runtime


def main() -> int:
    genesis_runtime.assert_available()
    manifest = load_manifest("default-robot-dog")
    commands = ["forward", "left", "right", "jump", "reset"]
    ok = True
    for command in commands:
        result = run_interactive_segment(manifest, command, duration_s=0.35)
        if result["step_count"] <= 0 or len(result["timeseries"]) == 0:
            ok = False
        print(f"command={command} steps={result['step_count']} forward={result['metrics'].get('forward_distance_m')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
