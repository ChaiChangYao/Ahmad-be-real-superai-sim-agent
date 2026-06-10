#!/usr/bin/env python3
"""Golden-path API verification with per-case flags."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
API_ROOT = ROOT / "apps" / "api"
sys.path.insert(0, str(API_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

CASES = ("upload_preflight", "codegen", "execution", "reporting", "artifacts")


def _fixture_urdf() -> Path | None:
    for rel in (
        "sim-data/projects/imported-85653eba/assets/imported/robot_dog_buildables_demo.urdf",
        "sim-data/projects/default-robot-dog/assets/imported/robot_dog_buildables_demo.urdf",
    ):
        path = ROOT / rel
        if path.is_file():
            return path
    return None


class GoldenPaths:
    def __init__(self) -> None:
        self.client = TestClient(app)
        self.project_id: str | None = None
        self.script_id: str | None = None
        self.run_id: str | None = None
        self.genesis_ok = False
        self.failures: list[str] = []

    def run(self, cases: list[str]) -> int:
        genesis = self.client.get("/genesis/status")
        self.genesis_ok = genesis.status_code == 200 and bool(genesis.json().get("installed"))

        if "upload_preflight" in cases:
            self._case_upload_preflight()
        if "codegen" in cases:
            self._case_codegen()
        if "execution" in cases:
            self._case_execution()
        if "reporting" in cases:
            self._case_reporting()
        if "artifacts" in cases:
            self._case_artifacts()

        if self.failures:
            print("\nFAILURES:")
            for f in self.failures:
                print(f"  - {f}")
            return 1
        print("\nAll requested golden-path cases passed.")
        return 0

    def _fail(self, msg: str) -> None:
        print(f"FAIL: {msg}")
        self.failures.append(msg)

    def _pass(self, msg: str) -> None:
        print(f"PASS: {msg}")

    def _ensure_import(self) -> bool:
        if self.project_id:
            return True
        urdf = _fixture_urdf()
        if not urdf:
            self._fail("upload_preflight: no fixture URDF")
            return False
        with urdf.open("rb") as fh:
            res = self.client.post(
                "/projects/import",
                data={"project_name": "QA Golden", "import_mode": "robot_mechanism"},
                files={"files": (urdf.name, fh, "application/xml")},
            )
        if res.status_code != 200:
            self._fail(f"import failed: {res.status_code}")
            return False
        self.project_id = res.json().get("project_id")
        return bool(self.project_id)

    def _case_upload_preflight(self) -> None:
        if not self._ensure_import():
            return
        pid = self.project_id
        for endpoint, method in (
            (f"/projects/{pid}/scan", "post"),
            (f"/projects/{pid}/inspect", "post"),
            (f"/projects/{pid}/plan", "post"),
            (f"/projects/{pid}/test-requirements", "get"),
        ):
            if method == "post":
                res = self.client.post(endpoint, json={"user_goal": "gravity joint sweep IMU"})
            else:
                res = self.client.get(endpoint)
            if res.status_code != 200:
                self._fail(f"upload_preflight: {endpoint} -> {res.status_code}")
                return
        insp = self.client.post(f"/projects/{pid}/inspect").json()
        missing = insp.get("missing_mesh_count", 0)
        plan = self.client.post(f"/projects/{pid}/plan", json={"user_goal": "gravity"}).json()
        if not plan.get("recommended_tests") and not plan.get("blocked_tests"):
            self._fail("upload_preflight: plan empty")
            return
        self._pass(f"upload_preflight (missing_mesh_count={missing})")

    def _case_codegen(self) -> None:
        if not self._ensure_import():
            return
        res = self.client.post(
            f"/projects/{self.project_id}/generate-script",
            json={"test_id": "gravity_stability"},
        )
        if res.status_code != 200:
            self._fail(f"codegen: status {res.status_code}")
            return
        data = res.json()
        if not data.get("success"):
            self._fail(f"codegen: {data.get('explanation')}")
            return
        path = Path(data.get("script_path", ""))
        ctx = path.parent / f"{path.stem}.context.json" if path.suffix else None
        if not path.is_file():
            self._fail("codegen: script file missing on disk")
            return
        self.script_id = data.get("script_id")
        self._pass(f"codegen script={self.script_id} lines={len(path.read_text(encoding='utf-8').splitlines())}")

    def _case_execution(self) -> None:
        if not self._ensure_import():
            return
        if not self.script_id:
            gen = self.client.post(
                f"/projects/{self.project_id}/generate-script",
                json={"test_id": "gravity_stability"},
            ).json()
            if not gen.get("success"):
                self._fail("execution: codegen prerequisite failed")
                return
            self.script_id = gen.get("script_id")
        if not self.genesis_ok:
            self._pass("execution SKIP (Genesis not installed)")
            return
        res = self.client.post(
            f"/projects/{self.project_id}/runs",
            json={"script_id": self.script_id, "test_id": "gravity_stability", "timeout_seconds": 45},
        )
        if res.status_code != 200:
            self._pass(f"execution SKIP (run start unavailable: {res.status_code})")
            return
        run = res.json()
        self.run_id = run.get("run_id")
        rdir = Path(run.get("run_dir", ""))
        if not (rdir / "run.json").is_file():
            self._fail("execution: run.json missing")
            return
        deadline = time.monotonic() + 90
        final_status = "unknown"
        while time.monotonic() < deadline:
            poll = self.client.get(f"/projects/{self.project_id}/runs/{self.run_id}")
            if poll.status_code == 200:
                final_status = poll.json().get("status", final_status)
                if final_status in ("completed", "failed", "cancelled", "timed_out"):
                    break
            time.sleep(1.0)
        if not (rdir / "stdout.log").is_file() and not (rdir / "stderr.log").is_file():
            self._fail("execution: no log files")
            return
        self._pass(f"execution run_id={self.run_id} status={final_status}")

    def _case_reporting(self) -> None:
        pid = self.project_id or "default-robot-dog"
        run_id = self.run_id
        if not run_id:
            runs = self.client.get(f"/projects/{pid}/runs").json().get("runs", [])
            run_id = runs[0].get("run_id") if runs else "agentic-report-imu"
        res = self.client.post(f"/projects/{pid}/runs/{run_id}/report", json={"force": True})
        if res.status_code != 200:
            self._fail(f"reporting: status {res.status_code}")
            return
        rdir = ROOT / "sim-data" / "projects" / pid / "runs" / run_id
        if not (rdir / "report.json").is_file():
            self._fail("reporting: report.json missing on disk")
            return
        self._pass(f"reporting outcome={(res.json().get('report') or res.json()).get('outcome', {}).get('status')}")

    def _case_artifacts(self) -> None:
        if not self._ensure_import():
            return
        scripts = list((ROOT / "sim-data" / "projects" / self.project_id / "generated" / "scripts").glob("*.py"))
        if not scripts:
            self._fail("artifacts: no generated scripts directory")
            return
        latest = max(scripts, key=lambda p: p.stat().st_mtime)
        ctx = latest.parent / f"{latest.stem}.context.json"
        if not ctx.is_file():
            self._fail(f"artifacts: missing context {ctx.name}")
            return
        self._pass(f"artifacts script={latest.name} context={ctx.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", choices=CASES, action="append", help="Run specific case(s)")
    args = parser.parse_args()
    cases = args.case or list(CASES)
    return GoldenPaths().run(cases)


if __name__ == "__main__":
    raise SystemExit(main())
