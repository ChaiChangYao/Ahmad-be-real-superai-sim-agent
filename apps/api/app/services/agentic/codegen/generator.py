"""Generate Genesis simulation scripts from typed templates."""
from __future__ import annotations

from app.services.agentic.codegen.schemas import CodeGenResult
from app.services.agentic.codegen.script_writer import render_template, write_script_artifacts
from app.services.agentic.codegen.template_context import build_script_context
from app.services.agentic.codegen.template_registry import resolve_template
from app.services.agentic.codegen.validators import validate_generated_script
from app.services.agentic.errors import AgenticError, TestRequirementNotMetError
from app.services.agentic.project_state import update_agentic_state


def generate_genesis_script(
    project_id: str,
    test_id: str,
    user_parameters: dict | None = None,
    fallback_mode: str | None = None,
) -> CodeGenResult:
    try:
        spec = resolve_template(test_id, fallback_mode)
        ctx = build_script_context(project_id, test_id, user_parameters, fallback_mode)
        ctx.template_id = spec.template_id

        source = render_template(spec, ctx)
        script_path, context_path = write_script_artifacts(ctx, source)
        validation = validate_generated_script(source, ctx, spec)

        result = CodeGenResult(
            success=validation.valid,
            script_id=ctx.script_id,
            script_path=str(script_path),
            context_path=str(context_path),
            template_id=spec.template_id,
            context=ctx,
            validation=validation,
            expected_outputs=validation.expected_outputs,
            next_step="run_simulation" if validation.valid else "fix_blockers",
            explanation=(
                f"Generated {spec.display_name} script ({spec.template_id}) for project {project_id}."
                if validation.valid
                else validation.blocked_reason
            ),
        )

        update_agentic_state(
            project_id,
            selected_test=test_id,
            last_codegen=result.model_dump(),
        )
        return result
    except TestRequirementNotMetError as exc:
        from app.services.agentic.codegen.schemas import GeneratedScriptValidation

        return CodeGenResult(
            success=False,
            template_id="",
            validation=GeneratedScriptValidation(
                valid=False,
                errors=[exc.explanation],
                blocked_reason=exc.explanation,
            ),
            next_step="select_fallback_or_upload_assets",
            explanation=exc.explanation,
        )
    except AgenticError as exc:
        from app.services.agentic.codegen.schemas import GeneratedScriptValidation

        return CodeGenResult(
            success=False,
            explanation=exc.explanation,
            validation=GeneratedScriptValidation(
                valid=False,
                errors=[exc.explanation],
                blocked_reason=exc.explanation,
            ),
        )


def list_generated_scripts(project_id: str) -> list[dict]:
    from app.services.project_store import project_dir

    scripts_dir = project_dir(project_id) / "generated" / "scripts"
    if not scripts_dir.is_dir():
        return []
    items: list[dict] = []
    for script in sorted(scripts_dir.glob("script-*.py"), key=lambda p: p.stat().st_mtime, reverse=True):
        ctx_path = script.with_name(f"{script.stem}.context.json")
        entry = {
            "script_id": script.stem,
            "script_path": str(script),
            "context_path": str(ctx_path) if ctx_path.is_file() else "",
            "modified_at": script.stat().st_mtime,
        }
        if ctx_path.is_file():
            import json

            try:
                data = json.loads(ctx_path.read_text(encoding="utf-8"))
                entry["test_id"] = data.get("test_id")
                entry["template_id"] = data.get("template_id")
            except json.JSONDecodeError:
                pass
        items.append(entry)
    return items


def get_generated_script(project_id: str, script_id: str) -> dict | None:
    from app.services.project_store import project_dir

    scripts_dir = project_dir(project_id) / "generated" / "scripts"
    script_path = scripts_dir / f"{script_id}.py"
    context_path = scripts_dir / f"{script_id}.context.json"
    if not script_path.is_file():
        return None
    import json

    ctx_data = {}
    if context_path.is_file():
        ctx_data = json.loads(context_path.read_text(encoding="utf-8"))
    source = script_path.read_text(encoding="utf-8")
    from app.services.agentic.codegen.schemas import GenesisScriptContext
    from app.services.agentic.codegen.template_registry import resolve_template
    from app.services.agentic.codegen.validators import validate_generated_script

    ctx = GenesisScriptContext.model_validate(ctx_data) if ctx_data else None
    validation = None
    if ctx:
        spec = resolve_template(ctx.test_id, ctx.fallback_mode)
        validation = validate_generated_script(source, ctx, spec).model_dump()
    return {
        "script_id": script_id,
        "script_path": str(script_path),
        "context_path": str(context_path),
        "source": source,
        "context": ctx_data,
        "validation": validation,
    }


def delete_generated_script(project_id: str, script_id: str) -> bool:
    from app.services.project_store import project_dir

    scripts_dir = project_dir(project_id) / "generated" / "scripts"
    script_path = scripts_dir / f"{script_id}.py"
    context_path = scripts_dir / f"{script_id}.context.json"
    removed = False
    if script_path.is_file():
        script_path.unlink()
        removed = True
    if context_path.is_file():
        context_path.unlink()
        removed = True
    return removed
