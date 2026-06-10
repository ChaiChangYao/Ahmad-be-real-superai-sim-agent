from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
THIS_FILE = Path(__file__).resolve()

FORBIDDEN = [
    "Project Chrono",
    "projectchrono",
    "pychrono",
]

TEXT_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".env",
    ".txt",
    ".ps1",
    ".css",
    ".html",
}

SKIP_DIRS = {".git", "node_modules", ".next", ".venv", "__pycache__"}


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS or path.name in {".env.example"}


def main() -> int:
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_dir() or path.resolve() == THIS_FILE:
            continue
        if not is_text_file(path):
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for token in FORBIDDEN:
            if token.lower() in content.lower():
                rel = path.relative_to(ROOT)
                violations.append(f"{rel}: found forbidden token '{token}'")

    if violations:
        print("Forbidden engine reference check failed:")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("Forbidden engine reference check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
