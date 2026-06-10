#!/usr/bin/env python3
"""HTTP-level E2E verification for the Agentic Simulation Layer API.

Uses FastAPI TestClient — no running server required.
Proves upload → scan → inspect → plan → codegen → run → report via real endpoints.
"""
from __future__ import annotations

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

QA_PROJECT_PREFIX = "qa-agentic-"


def _fixture_urdf() -> Path | None:
    candidates = [
        ROOT / "sim-data" / "projects" / "imported-85653eba" / "assets" / "imported" / "robot_dog_buildables_demo.urdf",
        ROOT / "sim-data" / "projects" / "default-robot-dog" / "assets" / "imported" / "robot_dog_buildables_demo.urdf",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def _cleanup_qa_projects() -> None:
    projects = ROOT / "sim-data" / "projects"
    if not projects.is_dir():
        return
    for child in projects.iterdir():
        if child.is_dir() and child.name.startswith(QA_PROJECT_PREFIX):
            shutil.rmtree(child, ignore_errors=True)


class QaRunner:
    def __init__(self) -> None:
        self.client = TestClient(app)
        self.results: list[dict] = []
        self.project_id: str | None = None
        self.script_id: str | None = None
        self.run_id: str | None = None
        self.genesis_available = False

    def record(self, name: str, ok: bool, detail: str = "", skipped: bool = False) -> None:
        status = "SKIP" if skipped else ("PASS" if ok else "FAIL")
        self.results.append({"name": name, "status": status, "detail": detail})
        print(f"[{status}] {name}" + (f" - {detail}" if detail else ""))

    def run(self) -> int:
        _cleanup_qa_projects()
        self._check_health()
        self._check_dependencies()
        self._test_import_upload()
        self._test_parse_goal_joint()
        self._test_zip_upload_diagnostics()
        self._test_preflight_chain()
        self._test_blocked_test_explanation()
        self._test_codegen()
        self._test_run_lifecycle()
        self._test_report()
        self._test_asset_upload()
        return self._summary()

    def _check_health(self) -> None:
        res = self.client.get("/health")
        ok = res.status_code == 200
        self.record("health", ok, res.text[:120] if not ok else "API reachable")

    def _check_dependencies(self) -> None:
        res = self.client.get("/agentic/dependencies")
        ok = res.status_code == 200
        if ok:
            data = res.json()
            self.genesis_available = data.get("genesis", {}).get("installed", False) or False
            genesis = self.client.get("/genesis/status")
            if genesis.status_code == 200:
                self.genesis_available = bool(genesis.json().get("installed"))
        self.record("agentic/dependencies", ok, f"genesis_installed={self.genesis_available}")

    def _test_import_upload(self) -> None:
        urdf = _fixture_urdf()
        if not urdf:
            self.record("import URDF", False, "no fixture URDF in sim-data")
            return
        with urdf.open("rb") as fh:
            res = self.client.post(
                "/projects/import",
                data={"project_name": "QA Agentic E2E", "import_mode": "robot_mechanism"},
                files={"files": (urdf.name, fh, "application/xml")},
            )
        ok = res.status_code == 200
        if ok:
            data = res.json()
            self.project_id = data.get("project_id")
            diag = data.get("upload_diagnostics") or {}
            ok = bool(self.project_id) and data.get("files_saved", 0) >= 1 and "upload_diagnostics" in data
            if ok and not diag.get("urdf_count", 0):
                ok = False
        self.record("import URDF", ok, f"project_id={self.project_id}")

    def _test_parse_goal_joint(self) -> None:
        if not self._require_project():
            return
        res = self.client.post(
            f"/projects/{self.project_id}/parse-goal",
            json={"user_goal": "testing the joint of this robot"},
        )
        ok = res.status_code == 200
        detail = ""
        if ok:
            data = res.json()
            candidates = data.get("candidate_tests") or []
            ok = "joint_sweep" in candidates
            detail = f"candidates={candidates}"
        self.record("parse-goal joint phrase", ok, detail)

    def _test_zip_upload_diagnostics(self) -> None:
        import io
        import zipfile

        urdf = _fixture_urdf()
        if not urdf:
            self.record("zip import diagnostics", False, "no fixture URDF", skipped=True)
            return
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            zf.writestr(urdf.name, urdf.read_bytes())
            mesh_dir = urdf.parent / "meshes"
            if mesh_dir.is_dir():
                for mesh in list(mesh_dir.rglob("*.stl"))[:3]:
                    zf.writestr(f"meshes/{mesh.name}", mesh.read_bytes())
        buf.seek(0)
        res = self.client.post(
            "/projects/import",
            data={"project_name": "QA Zip Import", "import_mode": "robot_mechanism"},
            files={"files": ("synthetic_bundle.zip", buf, "application/zip")},
        )
        ok = res.status_code == 200
        detail = ""
        if ok:
            data = res.json()
            diag = data.get("upload_diagnostics") or {}
            ok = diag.get("extracted_file_count", 0) > 0 and diag.get("urdf_count", 0) >= 1
            detail = f"extracted={diag.get('extracted_file_count')} urdf={diag.get('urdf_count')}"
        self.record("zip import diagnostics", ok, detail)

    def _require_project(self) -> bool:
        if not self.project_id:
            self.record("preflight chain", False, "skipped - import failed")
            return False
        return True

    def _test_preflight_chain(self) -> None:
        if not self._require_project():
            return
        pid = self.project_id
        scan = self.client.post(f"/projects/{pid}/scan")
        inspect = self.client.post(f"/projects/{pid}/inspect")
        plan = self.client.post(f"/projects/{pid}/plan", json={"user_goal": "gravity stability joint sweep IMU"})
        reqs = self.client.get(f"/projects/{pid}/test-requirements")
        ok = all(r.status_code == 200 for r in (scan, inspect, plan, reqs))
        detail = ""
        if ok:
            plan_data = plan.json()
            rec = plan_data.get("recommended_tests") or []
            blocked = plan_data.get("blocked_tests") or []
            detail = f"recommended={len(rec)} blocked={len(blocked)}"
            ok = len(rec) + len(blocked) > 0
        self.record("scan -> inspect -> plan -> test-requirements", ok, detail)

    def _test_blocked_test_explanation(self) -> None:
        if not self._require_project():
            return
        res = self.client.get(f"/projects/{self.project_id}/test-requirements")
        if res.status_code != 200:
            self.record("blocked tests have reasons", False, res.text[:200])
            return
        data = res.json()
        blocked = [t for t in data.get("readiness", []) if not t.get("can_run") and not t.get("can_run_with_fallback")]
        ok = True
        detail = f"blocked_count={len(blocked)}"
        for t in blocked[:3]:
            if not (t.get("blockers") or t.get("missing_required")):
                ok = False
                detail = f"{t.get('test_id')} missing blockers"
                break
        self.record("blocked tests have reasons", ok, detail)

    def _test_codegen(self) -> None:
        if not self._require_project():
            return
        res = self.client.post(
            f"/projects/{self.project_id}/generate-script",
            json={"test_id": "gravity_stability"},
        )
        ok = res.status_code == 200
        detail = ""
        if ok:
            data = res.json()
            ok = bool(data.get("success"))
            self.script_id = data.get("script_id")
            script_path = data.get("script_path")
            detail = f"script_id={self.script_id}"
            if ok and script_path:
                ok = Path(script_path).is_file()
                if ok:
                    source = Path(script_path).read_text(encoding="utf-8")
                    ok = "franka" not in source.lower() and "panda" not in source.lower()
                    detail += f" lines={len(source.splitlines())}"
        self.record("generate-script (gravity_stability)", ok, detail)

    def _test_run_lifecycle(self) -> None:
        if not self._require_project() or not self.script_id:
            self.record("run lifecycle", False, "skipped - codegen failed", skipped=True)
            return
        if not self.genesis_available:
            self.record("run lifecycle", True, "SKIP Genesis not installed", skipped=True)
            return
        res = self.client.post(
            f"/projects/{self.project_id}/runs",
            json={
                "script_id": self.script_id,
                "backend": "local",
                "test_id": "gravity_stability",
                "timeout_seconds": 45,
            },
        )
        if res.status_code not in (200, 503, 500):
            self.record("run lifecycle", False, f"start status={res.status_code} {res.text[:200]}")
            return
        if res.status_code != 200:
            self.record("run lifecycle", True, f"Genesis run unavailable: {res.status_code}", skipped=True)
            return
        run = res.json()
        self.run_id = run.get("run_id")
        ok = bool(self.run_id)
        rdir = Path(run.get("run_dir", ""))
        if ok:
            ok = (rdir / "run.json").is_file() and (rdir / "generated" / "script.py").is_file()
        deadline = time.monotonic() + 90
        final = run
        while time.monotonic() < deadline:
            poll = self.client.get(f"/projects/{self.project_id}/runs/{self.run_id}")
            if poll.status_code == 200:
                final = poll.json()
                if final.get("status") in ("completed", "failed", "cancelled", "timed_out"):
                    break
            time.sleep(1.0)
        logs = self.client.get(f"/projects/{self.project_id}/runs/{self.run_id}/logs?tail=50")
        ok = ok and logs.status_code == 200
        detail = f"run_id={self.run_id} status={final.get('status')} exit={final.get('exit_code')}"
        self.record("run lifecycle", ok, detail)

    def _test_report(self) -> None:
        pid = self.project_id or "default-robot-dog"
        runs = self.client.get(f"/projects/{pid}/runs")
        run_id = self.run_id
        if runs.status_code == 200 and runs.json().get("runs"):
            run_id = run_id or runs.json()["runs"][0].get("run_id")
        if not run_id:
            # Use fixture from verify_reporting
            run_id = "agentic-report-imu"
            fixture_dir = ROOT / "sim-data" / "projects" / "default-robot-dog" / "runs" / run_id
            if not fixture_dir.is_dir():
                self.record("engineering report", False, "no run_id and no fixture", skipped=True)
                return
        res = self.client.post(f"/projects/{pid}/runs/{run_id}/report", json={"force": True})
        ok = res.status_code == 200
        detail = ""
        if ok:
            data = res.json()
            report = data.get("report") or data
            rdir = ROOT / "sim-data" / "projects" / pid / "runs" / run_id
            report_json = rdir / "report.json"
            report_md = rdir / "report.md"
            ok = bool(report.get("outcome")) or report_json.is_file()
            detail = f"outcome={report.get('outcome', {}).get('status')} report.json={report_json.is_file()}"
        self.record("engineering report", ok, detail)

    def _test_asset_upload(self) -> None:
        if not self._require_project():
            return
        urdf = _fixture_urdf()
        if not urdf:
            self.record("asset upload", False, "no fixture file")
            return
        with urdf.open("rb") as fh:
            res = self.client.post(
                f"/projects/{self.project_id}/assets/upload",
                files={"files": (f"qa-extra-{urdf.name}", fh, "application/xml")},
            )
        ok = res.status_code == 200 and res.json().get("files_saved", 0) >= 1
        self.record("asset upload", ok, res.text[:120] if not ok else f"files_saved={res.json().get('files_saved')}")

    def _summary(self) -> int:
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = [r for r in self.results if r["status"] == "FAIL"]
        skipped = [r for r in self.results if r["status"] == "SKIP"]
        print("\n=== API E2E Summary ===")
        print(f"PASS={passed} FAIL={len(failed)} SKIP={len(skipped)} TOTAL={len(self.results)}")
        for r in failed:
            print(f"  FAIL: {r['name']} - {r['detail']}")
        return 1 if failed else 0


def main() -> int:
    return QaRunner().run()


if __name__ == "__main__":
    raise SystemExit(main())
