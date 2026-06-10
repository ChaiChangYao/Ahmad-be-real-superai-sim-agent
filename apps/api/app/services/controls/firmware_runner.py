from pathlib import Path


def store_firmware_file(project_control_dir: Path, filename: str, content: bytes) -> Path:
    project_control_dir.mkdir(parents=True, exist_ok=True)
    out_path = project_control_dir / filename
    out_path.write_bytes(content)
    return out_path
