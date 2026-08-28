"""Tests for the .env loading of the Docker and direct installations.

A variable set in the environment (docker-compose.yml, service unit) must win
over the value stored in `{APP_DATA_DIR}/.env`. Before this, the stored value
replaced the environment, so a user with a bad `URL_BASE` or `WEBUI_PASSWORD`
could not correct it from the compose file and was locked out of the app.
See https://github.com/nandyalu/trailarr/issues/663
"""

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
LOAD_ENV_SCRIPT = REPO_ROOT / "scripts" / "load_env.sh"
START_SCRIPT = REPO_ROOT / "scripts" / "start" / "start.py"

STORED_ENV = """\
# Trailarr settings
URL_BASE='/trailarr'
WEBUI_PASSWORD='stored-hash'
APP_PORT='7889'
TRAILER_FILE_NAME='{title} - Trailer-trailer.{ext}'
export MONITOR_ENABLED='true'
NOT A SETTING
"""


def _load_with_bash(
    env_file: Path, preset: dict[str, str], names: list[str]
) -> dict[str, str]:
    """Run load_env_file with the given environment, and read back the names."""
    script = f'. "$1"\nload_env_file "$2"\n'
    script += "".join(f'printf "%s\\n" "${name}"\n' for name in names)
    environ = {"PATH": os.environ.get("PATH", ""), **preset}
    result = subprocess.run(
        ["bash", "-c", script, "bash", str(LOAD_ENV_SCRIPT), str(env_file)],
        check=True,
        capture_output=True,
        text=True,
        env=environ,
    )
    return dict(zip(names, result.stdout.splitlines()))


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    path = tmp_path / ".env"
    path.write_text(STORED_ENV, encoding="utf-8")
    return path


class TestDockerEnvLoading:
    def test_stored_value_is_used_when_the_variable_is_not_set(self, env_file):
        loaded = _load_with_bash(env_file, {}, ["URL_BASE", "WEBUI_PASSWORD"])
        assert loaded["URL_BASE"] == "/trailarr"
        assert loaded["WEBUI_PASSWORD"] == "stored-hash"

    def test_environment_value_wins_over_the_stored_value(self, env_file):
        loaded = _load_with_bash(env_file, {"URL_BASE": "/media"}, ["URL_BASE"])
        assert loaded["URL_BASE"] == "/media"

    def test_empty_environment_value_wins_and_clears_the_setting(self, env_file):
        # The user sets `URL_BASE=` in docker-compose.yml to remove the URL base.
        loaded = _load_with_bash(env_file, {"URL_BASE": ""}, ["URL_BASE"])
        assert loaded["URL_BASE"] == ""

    def test_value_with_spaces_keeps_its_content(self, env_file):
        loaded = _load_with_bash(env_file, {}, ["TRAILER_FILE_NAME"])
        assert loaded["TRAILER_FILE_NAME"] == "{title} - Trailer-trailer.{ext}"

    def test_export_prefix_is_accepted(self, env_file):
        loaded = _load_with_bash(env_file, {}, ["MONITOR_ENABLED"])
        assert loaded["MONITOR_ENABLED"] == "true"

    def test_comment_and_invalid_lines_are_skipped(self, env_file):
        loaded = _load_with_bash(env_file, {}, ["APP_PORT"])
        assert loaded["APP_PORT"] == "7889"

    def test_missing_file_is_not_an_error(self, tmp_path):
        loaded = _load_with_bash(tmp_path / "none.env", {}, ["URL_BASE"])
        assert loaded["URL_BASE"] == ""


def _start_module():
    """Import scripts/start/start.py without running the service."""
    spec = importlib.util.spec_from_file_location("trailarr_start", START_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestDirectInstallEnvLoading:
    """The direct installation (systemd, launchd, NSSM) must behave the same."""

    def test_stored_value_is_used_when_the_variable_is_not_set(
        self, env_file, monkeypatch
    ):
        monkeypatch.delenv("URL_BASE", raising=False)
        env = _start_module()._load_env(env_file)
        assert env["URL_BASE"] == "/trailarr"
        assert os.environ["URL_BASE"] == "/trailarr"

    def test_environment_value_wins_over_the_stored_value(
        self, env_file, monkeypatch
    ):
        monkeypatch.setenv("URL_BASE", "/media")
        env = _start_module()._load_env(env_file)
        assert env["URL_BASE"] == "/media"
        assert os.environ["URL_BASE"] == "/media"

    def test_empty_environment_value_wins_and_clears_the_setting(
        self, env_file, monkeypatch
    ):
        monkeypatch.setenv("URL_BASE", "")
        env = _start_module()._load_env(env_file)
        assert env["URL_BASE"] == ""
