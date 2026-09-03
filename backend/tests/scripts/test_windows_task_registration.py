"""Tests for the Windows Task Scheduler startup task that the installer writes.

Trailarr installs to `C:\\Program Files\\Trailarr`, so every path in the
registration command holds a space. An unquoted `-Execute` made PowerShell
read `C:\\Program` as the program and the rest of the path as the positional
`-WorkingDirectory`. PowerShell reports no error for this, so the installer
registered a task that reports "Ready" and never starts: no port, no log file,
and a re-install writes the same broken task again.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALL_ROOT = REPO_ROOT / "scripts" / "install"

EXE = Path("C:/Program Files/Trailarr/backend/.venv/Scripts/trailarr.exe")
SCRIPT = Path("C:/Program Files/Trailarr/scripts/start/start.py")


@pytest.fixture(scope="module")
def build_ps():
    """Load `build_register_task_ps` from the installer package."""
    if str(INSTALL_ROOT) not in sys.path:
        sys.path.insert(0, str(INSTALL_ROOT))
    spec = importlib.util.spec_from_file_location(
        "trailarr_installer_windows",
        INSTALL_ROOT / "platforms" / "windows.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_register_task_ps


def test_execute_path_is_quoted(build_ps):
    """The program path goes inside single quotes, spaces and all."""
    ps = build_ps(EXE, SCRIPT, "someuser")
    assert f"-Execute '{EXE}'" in ps


def test_execute_path_is_not_split_on_the_space(build_ps):
    """`C:\\Program` on its own is the bug: the path must stay whole."""
    ps = build_ps(EXE, SCRIPT, "someuser")
    action = next(
        line for line in ps.splitlines() if "New-ScheduledTaskAction" in line
    )
    assert "-Execute C:" not in action
    assert "-WorkingDirectory" not in action


def test_start_script_is_passed_as_a_quoted_argument(build_ps):
    """The start script path also holds a space, so it stays quoted."""
    ps = build_ps(EXE, SCRIPT, "someuser")
    assert f"""-Argument '"{SCRIPT}"'""" in ps


def test_task_name_and_user_are_quoted(build_ps):
    """A user name can hold a space, so it stays inside quotes."""
    ps = build_ps(EXE, SCRIPT, "First Last", task_name="Trailarr")
    assert "-User 'First Last'" in ps
    assert "-UserId 'First Last'" in ps
    assert "-TaskName 'Trailarr'" in ps


def test_an_apostrophe_in_the_user_name_is_escaped(build_ps):
    """A Windows account can be named O'Brien. PowerShell doubles the quote.

    Without this the string stops at the apostrophe, and PowerShell runs the
    remainder of the name as a command.
    """
    ps = build_ps(EXE, SCRIPT, "O'Brien")
    assert "-User 'O''Brien'" in ps
    assert "-UserId 'O''Brien'" in ps
    assert "-User 'O'Brien'" not in ps


def test_an_apostrophe_in_the_task_name_is_escaped(build_ps):
    """The task name goes through the same quoting."""
    ps = build_ps(EXE, SCRIPT, "someuser", task_name="Bob's Trailarr")
    assert "-TaskName 'Bob''s Trailarr'" in ps
    assert "Start-ScheduledTask -TaskName 'Bob''s Trailarr'" in ps


def test_the_task_starts_after_it_is_registered(build_ps):
    """Registering alone leaves the app down until the next logon."""
    ps = build_ps(EXE, SCRIPT, "someuser")
    assert "Register-ScheduledTask" in ps
    assert "Start-ScheduledTask -TaskName 'Trailarr'" in ps


@pytest.mark.skipif(
    sys.platform != "win32", reason="needs PowerShell to parse the command"
)
def test_powershell_parses_the_action_as_written(build_ps):
    """Ask PowerShell itself what the generated action means."""
    import json
    import subprocess

    ps = build_ps(EXE, SCRIPT, "someuser")
    action_line = next(
        line for line in ps.splitlines() if "New-ScheduledTaskAction" in line
    )
    # Build the action only — do not register anything on the test machine.
    expression = action_line.split("=", 1)[1].strip()
    result = subprocess.run(
        [
            "powershell",
            "-NonInteractive",
            "-NoProfile",
            "-Command",
            f"({expression}) | "
            "Select-Object Execute, Arguments, WorkingDirectory | "
            "ConvertTo-Json -Compress",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    action = json.loads(result.stdout)
    assert action["Execute"] == str(EXE)
    assert action["Arguments"] == f'"{SCRIPT}"'
    assert not action["WorkingDirectory"]


@pytest.mark.skipif(
    sys.platform != "win32", reason="needs PowerShell to parse the command"
)
@pytest.mark.parametrize("username", ["someuser", "First Last", "O'Brien"])
def test_powershell_reads_the_whole_script_without_an_error(
    build_ps, username
):
    """The generated script is valid PowerShell for each kind of user name."""
    import subprocess

    ps = build_ps(EXE, SCRIPT, username)
    # Parse only. Running this would register a task on the test machine.
    checker = (
        "$errors = $null; "
        "[void][System.Management.Automation.Language.Parser]::ParseInput("
        "[Console]::In.ReadToEnd(), [ref]$null, [ref]$errors); "
        "if ($errors.Count) { $errors | ForEach-Object { $_.Message }; exit 1 }"
    )
    result = subprocess.run(
        ["powershell", "-NonInteractive", "-NoProfile", "-Command", checker],
        input=ps,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout
