"""Tests for the database backup retention policy.

Trailarr copies the database on every start and kept the newest 30 copies. That
caps a count, not a disk: a user with a 45 MB database found 1.5 GB of backups
(https://github.com/nandyalu/trailarr/issues/681). Retention now applies a count
limit and an age limit together.

Four paths make backups, and each one used to carry its own copy of the rule.
They now call `scripts/backup_retention.py`, and these tests check that they do
— a path that grows its own policy again is the failure this file exists for.
None of this code runs in the test suite otherwise: it runs at start, before
the application, where no test would walk it.
"""

import importlib.util
import os
import subprocess
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
RETENTION_SCRIPT = REPO_ROOT / "scripts" / "backup_retention.py"
DOCKER_START = REPO_ROOT / "scripts" / "start.sh"
DIRECT_START = REPO_ROOT / "scripts" / "start" / "start.py"
CLI_SCRIPT = REPO_ROOT / "scripts" / "cli" / "trailarr_cli.py"
LAUNCH_SCRIPT = REPO_ROOT / "scripts" / "launch.py"

DAY = 86400


def _retention():
    spec = importlib.util.spec_from_file_location("backup_retention", RETENTION_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def retention():
    return _retention()


def _backup(folder: Path, name: str, age_days: float, size: int = 1024) -> Path:
    path = folder / name
    path.write_bytes(b"x" * size)
    when = time.time() - (age_days * DAY)
    os.utime(path, (when, when))
    return path


def _update_dir(folder: Path, name: str, age_days: float, size: int = 1024) -> Path:
    path = folder / name
    path.mkdir()
    (path / "trailarr.db").write_bytes(b"x" * size)
    when = time.time() - (age_days * DAY)
    os.utime(path, (when, when))
    return path


class TestBothLimitsApply:
    def test_keeps_only_the_newest_count(self, tmp_path, retention):
        for day in range(20):
            _backup(tmp_path, f"trailarr_{day:04d}.db", age_days=day * 0.1)
        retention.prune_backups(tmp_path, count=10, days=30)
        assert len(list(tmp_path.glob("trailarr_*.db"))) == 10

    def test_deletes_a_backup_older_than_the_age_limit(self, tmp_path, retention):
        fresh = _backup(tmp_path, "trailarr_new.db", age_days=1)
        stale = _backup(tmp_path, "trailarr_old.db", age_days=45)
        retention.prune_backups(tmp_path, count=10, days=30)
        assert fresh.exists()
        assert not stale.exists()

    def test_the_age_limit_applies_under_the_count_limit(self, tmp_path, retention):
        # Three backups, well under a count of 10, but all far too old. The
        # count limit alone would keep every one of them — that is the 1.5 GB
        # case for a user who restarts rarely.
        for index in range(3):
            _backup(tmp_path, f"trailarr_{index}.db", age_days=100 + index)
        deleted, _ = retention.prune_backups(tmp_path, count=10, days=30)
        assert len(deleted) == 3
        assert list(tmp_path.glob("trailarr_*.db")) == []

    def test_the_count_limit_applies_under_the_age_limit(self, tmp_path, retention):
        # Twenty backups, every one younger than 30 days: the frequent
        # restarter, whom the age limit alone would never bound.
        for index in range(20):
            _backup(tmp_path, f"trailarr_{index:04d}.db", age_days=index * 0.5)
        retention.prune_backups(tmp_path, count=10, days=30)
        assert len(list(tmp_path.glob("trailarr_*.db"))) == 10

    def test_reports_the_space_it_freed(self, tmp_path, retention):
        _backup(tmp_path, "trailarr_keep.db", age_days=1, size=500)
        _backup(tmp_path, "trailarr_drop.db", age_days=99, size=2048)
        deleted, freed = retention.prune_backups(tmp_path, count=10, days=30)
        assert len(deleted) == 1
        assert freed == 2048


class TestTheRestorePathIsSafe:
    """The migration-failure path restores the backup the run just took."""

    def test_the_newest_backup_is_never_deleted(self, tmp_path, retention):
        just_taken = _backup(tmp_path, "trailarr_now.db", age_days=0)
        for index in range(50):
            _backup(tmp_path, f"trailarr_old_{index:04d}.db", age_days=90 + index)
        retention.prune_backups(tmp_path, count=1, days=1)
        assert just_taken.exists()
        assert list(tmp_path.glob("trailarr_*.db")) == [just_taken]

    def test_a_count_below_one_cannot_empty_the_folder(self, tmp_path, retention):
        just_taken = _backup(tmp_path, "trailarr_now.db", age_days=0)
        retention.prune_backups(tmp_path, count=0, days=0)
        assert just_taken.exists()

    @pytest.mark.parametrize("value", ["0", "-5", "not-a-number", ""])
    def test_a_bad_environment_value_never_empties_the_folder(
        self, tmp_path, retention, monkeypatch, value
    ):
        monkeypatch.setenv("BACKUP_KEEP_COUNT", value)
        monkeypatch.setenv("BACKUP_KEEP_DAYS", value)
        just_taken = _backup(tmp_path, "trailarr_now.db", age_days=0)
        retention.prune_backups(tmp_path)
        assert just_taken.exists()


class TestUpdateFolders:
    """The CLI updater wrote one folder per version and capped none of them."""

    def test_an_old_update_folder_is_deleted(self, tmp_path, retention):
        recent = _update_dir(tmp_path, "update_0.13.0", age_days=1)
        ancient = _update_dir(tmp_path, "update_0.9.6", age_days=200)
        retention.prune_backups(tmp_path, count=10, days=30)
        assert recent.is_dir()
        assert not ancient.exists()

    def test_update_folders_count_toward_the_same_limit(self, tmp_path, retention):
        for index in range(8):
            _update_dir(tmp_path, f"update_0.1{index}.0", age_days=index * 0.1)
        for index in range(8):
            _backup(tmp_path, f"trailarr_{index}.db", age_days=index * 0.1)
        retention.prune_backups(tmp_path, count=10, days=30)
        remaining = list(tmp_path.glob("update_*")) + list(tmp_path.glob("trailarr_*.db"))
        assert len(remaining) == 10

    def test_the_size_of_a_deleted_folder_is_counted(self, tmp_path, retention):
        _update_dir(tmp_path, "update_0.9.6", age_days=200, size=4096)
        _, freed = retention.prune_backups(tmp_path, count=10, days=30)
        assert freed == 4096


class TestSettings:
    def test_defaults_are_ten_backups_for_thirty_days(self, retention, monkeypatch):
        monkeypatch.delenv("BACKUP_KEEP_COUNT", raising=False)
        monkeypatch.delenv("BACKUP_KEEP_DAYS", raising=False)
        assert retention.keep_count() == 10
        assert retention.keep_days() == 30

    def test_the_environment_overrides_the_defaults(self, retention, monkeypatch):
        monkeypatch.setenv("BACKUP_KEEP_COUNT", "3")
        monkeypatch.setenv("BACKUP_KEEP_DAYS", "7")
        assert retention.keep_count() == 3
        assert retention.keep_days() == 7

    def test_a_missing_folder_is_not_an_error(self, tmp_path, retention):
        assert retention.prune_backups(tmp_path / "nothing-here") == ([], 0)


class TestTheCommandLine:
    """scripts/start.sh calls the module as a command."""

    def _run(self, folder: Path, env: dict[str, str] | None = None):
        return subprocess.run(
            ["python3", str(RETENTION_SCRIPT), str(folder)],
            capture_output=True,
            text=True,
            env={"PATH": os.environ.get("PATH", ""), **(env or {})},
        )

    def test_it_reports_what_it_deleted(self, tmp_path):
        _backup(tmp_path, "trailarr_now.db", age_days=0)
        _backup(tmp_path, "trailarr_old.db", age_days=99)
        result = self._run(tmp_path)
        assert result.returncode == 0
        assert "Deleted 1 backup(s)" in result.stdout
        assert "keeps 10 backups, for 30 days" in result.stdout

    def test_it_reports_when_it_deleted_nothing(self, tmp_path):
        _backup(tmp_path, "trailarr_now.db", age_days=0)
        result = self._run(tmp_path)
        assert result.returncode == 0
        assert "Kept all 1 backup(s)" in result.stdout

    def test_it_reads_the_limits_from_the_environment(self, tmp_path):
        for index in range(5):
            _backup(tmp_path, f"trailarr_{index}.db", age_days=index * 0.1)
        result = self._run(tmp_path, {"BACKUP_KEEP_COUNT": "2"})
        assert "keeps 2 backups" in result.stdout
        assert len(list(tmp_path.glob("trailarr_*.db"))) == 2

    def test_a_missing_folder_is_not_a_failure(self, tmp_path):
        # The container must start even when the folder is not there yet.
        result = self._run(tmp_path / "nothing-here")
        assert result.returncode == 0


class TestEveryPathUsesTheSharedPolicy:
    """The rule was written four times. It must never be written twice again."""

    @pytest.mark.parametrize(
        "script", [DIRECT_START, CLI_SCRIPT, LAUNCH_SCRIPT], ids=lambda p: p.name
    )
    def test_the_python_paths_import_it(self, script):
        source = script.read_text(encoding="utf-8")
        assert "from backup_retention import" in source
        assert "prune_backups(" in source

    def test_the_docker_path_runs_it(self):
        source = DOCKER_START.read_text(encoding="utf-8")
        assert "backup_retention.py" in source

    @pytest.mark.parametrize(
        "script",
        [DOCKER_START, DIRECT_START, CLI_SCRIPT, LAUNCH_SCRIPT],
        ids=lambda p: p.name,
    )
    def test_no_path_carries_its_own_cap(self, script):
        # The old rule, in each of its four spellings.
        source = script.read_text(encoding="utf-8")
        assert "backups[30:]" not in source
        assert "tail -n +31" not in source
        assert "-gt 30" not in source

    def test_the_docker_path_loads_env_before_it_backs_up(self):
        # The retention settings live in APP_DATA_DIR/.env. Loading that file
        # after the backup block, as the script did, means the settings are
        # read too late to have any effect in the Docker installation.
        source = DOCKER_START.read_text(encoding="utf-8")
        load_at = source.index("load_env_file ")
        backup_at = source.index("Backing up database")
        retention_at = source.index("backup_retention.py")
        assert load_at < backup_at < retention_at

    def test_the_docker_path_cannot_fail_the_start(self):
        # A retention failure must never keep the container from starting.
        source = DOCKER_START.read_text(encoding="utf-8")
        line = next(ln for ln in source.splitlines() if "backup_retention.py" in ln)
        assert line.strip().startswith("if RETENTION_OUTPUT=$(")
        assert "Trailarr starts anyway" in source
