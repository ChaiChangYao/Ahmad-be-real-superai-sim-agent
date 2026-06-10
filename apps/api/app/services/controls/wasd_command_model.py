from pydantic import BaseModel


class WasdCommand(BaseModel):
    key: str
    timestamp_ms: int
