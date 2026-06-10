"""Cancel running execution processes."""
from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from subprocess import Popen


def terminate_process(proc: Popen, *, graceful_seconds: float = 3.0) -> int | None:
    if proc.poll() is not None:
        return proc.returncode
    proc.terminate()
    try:
        return proc.wait(timeout=graceful_seconds)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            proc.kill()
        else:
            proc.kill()
        return proc.wait(timeout=5.0)
