from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
API_ROOT = ROOT / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from app.services.genesis.genesis_runtime import genesis_runtime


def main() -> None:
    status = genesis_runtime.status()
    print({"installed": status.installed, "version": status.version, "error": status.error, "backend": status.backend, "device": status.device})
    if not status.installed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
