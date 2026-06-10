"""Log capture and tailing for execution runs."""
from __future__ import annotations

import re
import threading
from datetime import datetime, UTC
from pathlib import Path

from app.services.agentic.execution.schemas import RunEvent

_REDACT = re.compile(r"(api[_-]?key|token|secret|password)\s*[=:]\s*\S+", re.I)

_TAILERS: dict[str, threading.Thread] = {}
_OFFSETS: dict[str, dict[str, int]] = {}
_EVENTS: dict[str, list[RunEvent]] = {}


def _redact(line: str) -> str:
    return _REDACT.sub(r"\1=***", line)


def append_combined(run_dir: Path, source: str, text: str) -> None:
    if not text:
        return
    combined = run_dir / "combined.log"
    combined.parent.mkdir(parents=True, exist_ok=True)
    for line in text.splitlines(keepends=True):
        stamped = f"[{datetime.now(UTC).isoformat()}][{source}] {_redact(line)}"
        with combined.open("a", encoding="utf-8") as f:
            f.write(stamped if stamped.endswith("\n") else stamped + "\n")


def record_event(run_id: str, level: str, message: str, source: str = "worker", data: dict | None = None) -> None:
    evt = RunEvent(
        run_id=run_id,
        ts=datetime.now(UTC).isoformat(),
        level=level,
        source=source,
        message=message,
        data=data or {},
    )
    _EVENTS.setdefault(run_id, []).append(evt)


def get_events(run_id: str, since_index: int = 0) -> list[RunEvent]:
    return _EVENTS.get(run_id, [])[since_index:]


def tail_logs(run_dir: Path, *, tail: int = 200) -> dict:
    stdout_path = run_dir / "stdout.log"
    stderr_path = run_dir / "stderr.log"
    combined_path = run_dir / "combined.log"
    stdout = stdout_path.read_text(encoding="utf-8", errors="ignore") if stdout_path.is_file() else ""
    stderr = stderr_path.read_text(encoding="utf-8", errors="ignore") if stderr_path.is_file() else ""
    combined = combined_path.read_text(encoding="utf-8", errors="ignore") if combined_path.is_file() else ""
    if tail > 0:
        stdout = "\n".join(stdout.splitlines()[-tail:])
        stderr = "\n".join(stderr.splitlines()[-tail:])
        combined = "\n".join(combined.splitlines()[-tail:])
    return {
        "stdout": stdout,
        "stderr": stderr,
        "combined": combined,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "combined_path": str(combined_path),
    }


def _tail_worker(run_id: str, run_dir: Path, stop_event: threading.Event) -> None:
    offsets = _OFFSETS.setdefault(run_id, {"stdout.log": 0, "stderr.log": 0})
    while not stop_event.wait(0.5):
        for name in ("stdout.log", "stderr.log"):
            path = run_dir / name
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            offset = offsets.get(name, 0)
            if len(text) <= offset:
                continue
            chunk = text[offset:]
            offsets[name] = len(text)
            source = "stdout" if name.startswith("stdout") else "stderr"
            append_combined(run_dir, source, chunk)
            for line in chunk.splitlines():
                if line.strip():
                    record_event(run_id, "info", line, source=source)


def start_log_tailer(run_id: str, run_dir: Path) -> None:
    stop = threading.Event()
    thread = threading.Thread(
        target=_tail_worker,
        args=(run_id, run_dir, stop),
        name=f"agentic-log-{run_id}",
        daemon=True,
    )
    _TAILERS[run_id] = thread
    thread.start()


def stop_log_tailer(run_id: str, run_dir: Path) -> None:
    thread = _TAILERS.pop(run_id, None)
    if thread and thread.is_alive():
        thread.join(timeout=2.0)
    _tail_worker(run_id, run_dir, threading.Event())


def parse_run_failure(run_dir: Path) -> dict[str, str] | None:
    """Parse failure patterns from agentic run logs (.log or .txt)."""
    chunks: list[str] = []
    for name in ("stderr.log", "stdout.log", "stderr.txt", "stdout.txt"):
        path = run_dir / name
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8", errors="ignore"))
    text = "\n".join(chunks)
    if not text.strip():
        return None
    summary = ""
    for line in reversed(text.splitlines()):
        plain = line.strip()
        if not plain or "[INFO]" in plain:
            continue
        summary = plain
        break
    if not summary:
        return None
    lower = text.lower()
    failure_code = "unknown"
    suggested_fix = "Review run logs and verify project assets."
    if "unrecognized arguments" in lower or "--no-vis" in lower:
        failure_code = "invalid_cli_flag"
        suggested_fix = "Do not pass unsupported CLI flags. Use web headless recording."
    elif "no such file" in lower or "filenotfounderror" in lower or "missing mesh" in lower or "asset file not found" in lower:
        failure_code = "missing_asset"
        suggested_fix = "Upload missing mesh files or use skeleton fallback."
    elif "importerror" in lower or "modulenotfounderror" in lower:
        failure_code = "missing_dependency"
        suggested_fix = "Install missing Python dependency or optional Genesis extra."
    elif "timed out" in lower or "timeout" in lower:
        failure_code = "timeout"
        suggested_fix = "Increase timeout or simplify the simulation."
    elif "unsafe" in lower or "banned" in lower:
        failure_code = "unsafe_script"
        suggested_fix = "Regenerate script from assistant."
    return {
        "failure_code": failure_code,
        "failure_detail": summary,
        "suggested_fix": suggested_fix,
        "failure_summary": summary,
    }


def read_failure_excerpt(run_dir: Path, max_lines: int = 40) -> str:
    logs = tail_logs(run_dir, tail=max_lines)
    return (logs.get("stderr") or "") + "\n" + (logs.get("stdout") or "")
