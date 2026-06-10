"""Lazy genesis import so API routes load without PyTorch until a sim is started."""
from __future__ import annotations

from typing import Any

_GS: Any | None = None


def gs() -> Any:
    global _GS
    if _GS is None:
        import genesis as gs_mod

        _GS = gs_mod
    return _GS
