from functools import lru_cache
from pydantic import BaseModel
import os


class Settings(BaseModel):
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    sim_data_root: str = os.getenv("SIM_DATA_ROOT", "sim-data")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
