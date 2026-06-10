"""AST safety validation for generated scripts."""
from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORT_ROOTS = {
    "os",
    "sys",
    "json",
    "math",
    "pathlib",
    "traceback",
    "time",
    "numpy",
    "genesis",
    "app",
    "__future__",
}

BANNED_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "system",
    "popen",
    "remove",
    "rmdir",
    "unlink",
    "show",
    "imshow",
}

BANNED_IMPORTS = {
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "ftplib",
    "telnetlib",
    "cv2",
}


def validate_script_safety(source: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"Syntax error: {exc}"], warnings

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in BANNED_IMPORTS:
                    errors.append(f"Banned import: {alias.name}")
                elif root not in ALLOWED_IMPORT_ROOTS:
                    warnings.append(f"Non-standard import: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in BANNED_IMPORTS:
                    errors.append(f"Banned import from: {node.module}")
                elif root not in ALLOWED_IMPORT_ROOTS:
                    warnings.append(f"Non-standard import from: {node.module}")
        elif isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            if name in BANNED_CALLS:
                errors.append(f"Banned call detected: {name}")

    if "plt.show" in source or "matplotlib.pyplot.show" in source:
        errors.append("Matplotlib show() not allowed in web mode")
    if "cv2.imshow" in source:
        errors.append("cv2.imshow not allowed in web mode")

    return errors, warnings


def validate_output_paths(context: dict, project_root: Path) -> list[str]:
    errors: list[str] = []
    root = project_root.resolve()
    for key in ("output_root",):
        val = context.get(key)
        if val:
            p = Path(val).resolve()
            if root not in p.parents and p != root:
                try:
                    p.relative_to(root)
                except ValueError:
                    errors.append(f"Output path outside project: {val}")
    return errors
