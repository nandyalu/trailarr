"""The scheduler's temp database must not outlive the interpreter.

quiv creates ``quiv_<id>.db`` in the system temp folder when ``Quiv()`` is
built, and only ``shutdown()`` deletes it. ``tasks/__init__.py`` builds the
scheduler at import time, so every interpreter that imported the package and
never ran the FastAPI lifespan left one file behind: each pytest run, and each
child interpreter the migration tests spawn. 173 of them sat in ``/tmp`` on
Oct 21, 2026.
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


def test_a_bare_import_leaves_no_database_behind(tmp_path: Path):
    data_dir = tmp_path / "appdata"
    (data_dir / "logs").mkdir(parents=True)
    temp_dir = tmp_path / "tmp"
    temp_dir.mkdir()
    env = {
        **os.environ,
        "APP_DATA_DIR": str(data_dir),
        "PYTHONPATH": str(BACKEND_DIR),
        # quiv puts its database in tempfile.gettempdir(), which reads TMPDIR.
        "TMPDIR": str(temp_dir),
    }
    result = subprocess.run(
        [sys.executable, "-c", "import tasks"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert sorted(temp_dir.glob("quiv_*")) == []


def test_shutdown_scheduler_runs_quiv_shutdown_once(monkeypatch):
    import tasks

    calls: list[float | None] = []
    monkeypatch.setattr(tasks, "_scheduler_stopped", False)
    monkeypatch.setattr(
        tasks.scheduler, "shutdown", lambda timeout=None: calls.append(timeout)
    )
    tasks.shutdown_scheduler(timeout=4)
    tasks.shutdown_scheduler(timeout=1)
    assert calls == [4]
