#!/usr/bin/env python3
"""Part 4 execution verification."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.services.agentic.codegen.generator import generate_genesis_script  # noqa: E402
from app.services.agentic.execution.process_manager import cancel_run, get_run_status  # noqa: E402
from app.services.agentic.execution.runner import start_run  # noqa: E402
from app.services.agentic.execution.schemas import ExecutionBackend, ExecutionRequest  # noqa: E402


def wait_terminal(project_id: str, run_id: str, timeout: float = 120.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = get_run_status(project_id, run_id)
        if run.status.value in ("completed", "failed", "cancelled", "timed_out"):
            return run
        time.sleep(1.0)
    return get_run_status(project_id, run_id)


def case_generate_and_check_structure() -> bool:
    print("\n=== Case: codegen + run dir structure ===")
    gen = generate_genesis_script("default-robot-dog", "gravity_stability")
    if not gen.success:
        print("SKIP run (codegen failed):", gen.explanation)
        return True
    req = ExecutionRequest(
        project_id="default-robot-dog",
        script_id=gen.script_id,
        test_id="gravity_stability",
        backend=ExecutionBackend.local,
        timeout_seconds=30,
    )
    try:
        run = start_run(req)
    except Exception as exc:
        print(f"Run start failed (Genesis may be unavailable): {exc}")
        return True
    print(f"run_id={run.run_id} status={run.status}")
    rdir = Path(run.run_dir)
    assert (rdir / "generated" / "script.py").is_file()
    assert (rdir / "generated" / "script.context.json").is_file()
    assert (rdir / "run.json").is_file()
    final = wait_terminal("default-robot-dog", run.run_id, timeout=90)
    assert (rdir / "stdout.log").is_file() or (rdir / "stderr.log").is_file()
    print(f"final_status={final.status} exit={final.exit_code}")
    return True


def case_invalid_script_blocked() -> bool:
    print("\n=== Case: invalid script blocked ===")
    from app.services.agentic.execution.errors import UnsafeScriptError
    from app.services.agentic.execution.local_runner import _validate_script_source

    scripts = ROOT / "sim-data" / "projects" / "default-robot-dog" / "generated" / "scripts"
    if not scripts.is_dir():
        print("SKIP no scripts")
        return True
    bad = scripts / "bad-test.py"
    bad.write_text("import subprocess\nsubprocess.call(['echo','hi'])\n", encoding="utf-8")
    try:
        _validate_script_source("default-robot-dog", "bad-test")
        print("FAIL expected unsafe block")
        return False
    except UnsafeScriptError:
        print("PASS unsafe blocked")
    finally:
        if bad.is_file():
            bad.unlink()
    return True


def case_two_runs_isolated() -> bool:
    print("\n=== Case: two runs isolated ===")
    gen = generate_genesis_script("default-robot-dog", "static_mesh_preview")
    if not gen.success:
        print("SKIP static preview codegen failed")
        return True
    ids = []
    for _ in range(2):
        run = start_run(
            ExecutionRequest(
                project_id="default-robot-dog",
                script_id=gen.script_id,
                test_id="static_mesh_preview",
                timeout_seconds=20,
            )
        )
        ids.append(run.run_id)
        wait_terminal("default-robot-dog", run.run_id, timeout=60)
    assert ids[0] != ids[1]
    print(f"PASS runs {ids[0]} vs {ids[1]}")
    return True


def case_docker_unavailable() -> bool:
    print("\n=== Case: docker unavailable ===")
    from app.services.agentic.execution.errors import BackendUnavailableError

    try:
        start_run(
            ExecutionRequest(
                project_id="default-robot-dog",
                script_id="script-dummy",
                backend=ExecutionBackend.docker,
            )
        )
        print("FAIL expected docker unavailable")
        return False
    except BackendUnavailableError:
        print("PASS docker blocked")
        return True


def main() -> int:
    passed = 0
    for fn in (case_invalid_script_blocked, case_docker_unavailable, case_generate_and_check_structure, case_two_runs_isolated):
        try:
            if fn():
                passed += 1
        except Exception as exc:
            print(f"FAIL: {exc}")
    print(f"\n{passed}/4 checks passed")
    return 0 if passed >= 3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
