from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import threading

from app.paths import repo_root

_LOG_PATH = repo_root() / "logs" / "genesis-workbench.log"
_LOCK = threading.Lock()


def log_path() -> Path:
    return _LOG_PATH


def append_log(source: str, message: str) -> None:
    line = message.rstrip("\n")
    if not line:
        return
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat()
    with _LOCK:
        with _LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(f"[{stamp}] [{source}] {line}\n")


def append_block(source: str, text: str) -> None:
    for line in text.splitlines():
        append_log(source, line)
