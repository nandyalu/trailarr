"""Tests for the group-stopping tool runner (Copilot review on #701).

yt-dlp starts ffmpeg. A stop must end ffmpeg too, not only yt-dlp.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
import quiv

from services.trailers.process import run_tool

pytestmark = pytest.mark.skipif(
    sys.platform == "win32", reason="process groups are a POSIX feature"
)


def _alive(pid: int) -> bool:
    """True while the process exists and is not a zombie."""
    try:
        status = Path(f"/proc/{pid}/status").read_text()
    except FileNotFoundError:
        return False
    return "State:\tZ" not in status


def _wait_gone(pid: int, seconds: float = 5.0) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not _alive(pid):
            return True
        time.sleep(0.1)
    return False


def _child_that_spawns(tmp_path: Path) -> tuple[list[str], Path]:
    """A shell that starts a grandchild, records its pid, and waits."""
    pidfile = tmp_path / "grandchild.pid"
    cmd = [
        "sh",
        "-c",
        f"sleep 30 & echo $! > '{pidfile}'; wait",
    ]
    return cmd, pidfile


def _read_pid(pidfile: Path) -> int:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if pidfile.exists() and pidfile.read_text().strip():
            return int(pidfile.read_text().strip())
        time.sleep(0.05)
    raise AssertionError("the child never wrote the pid of its grandchild")


class TestRunTool:
    def test_a_stop_ends_the_grandchild_too(self, tmp_path):
        cmd, pidfile = _child_that_spawns(tmp_path)
        stop_event = threading.Event()
        threading.Timer(0.5, stop_event.set).start()
        started = time.monotonic()

        with pytest.raises(quiv.JobCancelledError):
            run_tool(cmd, stop_event=stop_event, capture_output=True)

        assert time.monotonic() - started < 10
        grandchild = _read_pid(pidfile)
        assert _wait_gone(grandchild), f"sleep {grandchild} is still alive"

    def test_a_timeout_ends_the_grandchild_too(self, tmp_path):
        cmd, pidfile = _child_that_spawns(tmp_path)

        with pytest.raises(subprocess.TimeoutExpired):
            run_tool(cmd, timeout=0.6, capture_output=True)

        grandchild = _read_pid(pidfile)
        assert _wait_gone(grandchild)

    def test_a_tool_that_ends_by_itself_returns_its_output(self):
        result = run_tool(
            ["sh", "-c", "echo out; echo err >&2; exit 3"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 3
        assert result.stdout.strip() == "out"
        assert result.stderr.strip() == "err"

    def test_the_child_gets_its_own_process_group(self):
        result = run_tool(
            ["sh", "-c", "ps -o pgid= -p $$"], capture_output=True, text=True
        )
        assert int(result.stdout.strip()) != os.getpgid(os.getpid())

    def test_outside_a_job_without_an_event_it_runs_to_the_end(self):
        result = run_tool(["true"], capture_output=True)
        assert result.returncode == 0
