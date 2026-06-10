"""Render Jinja templates and write generated script artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.agentic.codegen.schemas import GenesisScriptContext, GenesisTemplateSpec
from app.services.agentic.codegen.template_registry import TEMPLATES_DIR

_env: Environment | None = None


def _get_env() -> Environment:
    global _env
    if _env is None:
        _env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=select_autoescape(enabled_extensions=()),
            trim_blocks=False,
            lstrip_blocks=False,
        )
        _env.filters["tojson"] = lambda v: json.dumps(v)
    return _env


def render_template(spec: GenesisTemplateSpec, ctx: GenesisScriptContext) -> str:
    template = _get_env().get_template(spec.template_path)
    return template.render(ctx=ctx.model_dump())


def scripts_dir(project_root: Path) -> Path:
    d = project_root / "generated" / "scripts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_script_artifacts(
    ctx: GenesisScriptContext,
    source: str,
) -> tuple[Path, Path]:
    root = Path(ctx.project_root)
    out_dir = scripts_dir(root)
    script_path = out_dir / f"{ctx.script_id}.py"
    context_path = out_dir / f"{ctx.script_id}.context.json"
    script_path.write_text(source, encoding="utf-8")
    context_path.write_text(ctx.model_dump_json(indent=2), encoding="utf-8")
    return script_path, context_path
