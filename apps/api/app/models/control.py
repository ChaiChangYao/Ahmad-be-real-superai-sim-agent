from __future__ import annotations

from typing import Literal
from pydantic import BaseModel


class InteractiveCommand(BaseModel):
    session_id: str
    command: Literal["forward", "backward", "left", "right", "jump", "stop", "reset", "emergency_stop"]
    duration_s: float = 0.35
