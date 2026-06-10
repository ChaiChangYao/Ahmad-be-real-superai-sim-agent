import json
from pathlib import Path


def main() -> int:
    source = Path(__file__).resolve().parents[3] / "sim-data" / "projects" / "robot-dog-demo" / "manifest.buildables.physics.json"
    print(json.dumps({"demo_manifest": str(source), "exists": source.exists()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
