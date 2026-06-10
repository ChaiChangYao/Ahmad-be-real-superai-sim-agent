import os
from pathlib import Path
from .config import get_settings


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sim_data_root() -> Path:
    return (repo_root() / get_settings().sim_data_root).resolve()


def ensure_genesis_repo_env() -> None:
    """Auto-detect genesis-world / genesis-nyx clones next to the monorepo root."""
    root = repo_root()
    if not os.getenv("GENESIS_WORLD_ROOT"):
        candidate = root / "genesis-world"
        if (candidate / "examples" / "rigid").is_dir():
            os.environ["GENESIS_WORLD_ROOT"] = str(candidate.resolve())
    if not os.getenv("GENESIS_NYX_ROOT"):
        candidate = root / "genesis-nyx"
        if (candidate / "examples" / "01_hello_nyx.py").is_file():
            os.environ["GENESIS_NYX_ROOT"] = str(candidate.resolve())


def projects_root() -> Path:
    return sim_data_root() / "projects"


def showcase_launcher_script() -> Path:
    """Subprocess entry for Genesis Workbench catalogue demos."""
    return Path(__file__).resolve().parent / "scripts" / "showcase_launcher.py"


def component_profiles_root() -> Path:
    return sim_data_root() / "component-profiles"


def material_profiles_root() -> Path:
    return sim_data_root() / "material-profiles"


def ensure_base_paths() -> None:
    ensure_genesis_repo_env()
    for path in [projects_root(), component_profiles_root(), material_profiles_root(), sim_data_root() / "generated", sim_data_root() / "runs"]:
        path.mkdir(parents=True, exist_ok=True)
