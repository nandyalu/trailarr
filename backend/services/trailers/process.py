"""Run a tool that starts children of its own, and stop them all on a cancel.

`quiv.run_subprocess` stops the direct child only. yt-dlp starts ffmpeg
to merge the video and the audio streams, and for other post-processing,
so a stop during those steps left ffmpeg running while Trailarr removed
its files. This helper gives the child its own process group and, on a
stop or a timeout, signals the whole group, then reaps the child.

The loop is the same as the one in quiv: wait in short slices, and check
the stop event between them. It raises the same errors, so the callers
of `quiv.run_subprocess` need no change but the function name.
"""

import os
import signal
import subprocess
import sys
import threading
import time
from typing import Any, Sequence

import quiv
from app_logger import ModuleLogger

logger = ModuleLogger("ToolProcess")

# How long one wait slice lasts before the stop event is checked.
_POLL_SECONDS = 0.5

_IS_POSIX = sys.platform != "win32"


def _current_stop_event() -> threading.Event | None:
    """The stop event of the quiv job this code runs in, or None.

    quiv keeps it in its job context and does not export an accessor, so
    this reads the one that `run_subprocess` uses. Outside a job, or
    when quiv changes its internals, there is no event, and the tool
    runs to its end or its timeout, as `subprocess.run` would.
    """
    accessor = getattr(quiv.subprocesses, "_current_stop_event", None)
    if accessor is None:
        return None
    try:
        return accessor()
    except Exception:
        return None


def _signal_group(proc: subprocess.Popen, kill: bool) -> None:
    """Terminate, or kill, the process group of the child. Where there is
    no group, the child alone."""
    if _IS_POSIX:
        sig = signal.SIGKILL if kill else signal.SIGTERM
        try:
            os.killpg(os.getpgid(proc.pid), sig)
            return
        except (ProcessLookupError, PermissionError, OSError):
            pass
    try:
        if kill:
            proc.kill()
        else:
            proc.terminate()
    except ProcessLookupError:
        pass


def _stop_group(
    proc: subprocess.Popen, kill_grace: float
) -> tuple[Any, Any]:
    """Terminate the group, kill it after the grace, and reap the child.

    Returns:
        tuple: What the child wrote to stdout and stderr before it died.
    """
    _signal_group(proc, kill=False)
    try:
        stdout, stderr = proc.communicate(timeout=kill_grace)
    except subprocess.TimeoutExpired:
        _signal_group(proc, kill=True)
        stdout, stderr = proc.communicate()
    return stdout, stderr


def run_tool(
    args: Sequence[str],
    *,
    stop_event: threading.Event | None = None,
    timeout: float | None = None,
    kill_grace: float = 5.0,
    capture_output: bool = False,
    **popen_kwargs: Any,
) -> subprocess.CompletedProcess:
    """Run a tool, and stop its whole process group on a cancel.

    A drop-in for `quiv.run_subprocess` for a tool that starts children,
    such as yt-dlp. On POSIX the child gets its own session, so every
    process it starts is in its group, and a stop signals the group.

    Args:
        args (Sequence[str]): The command.
        stop_event (threading.Event | None): The event to watch. Defaults
            to the stop event of the job this code runs inside.
        timeout (float | None): Seconds before the tool is stopped and
            `TimeoutExpired` is raised.
        kill_grace (float): Seconds between SIGTERM and SIGKILL.
        capture_output (bool): Collect stdout and stderr.
        **popen_kwargs: Passed to `subprocess.Popen`.

    Returns:
        subprocess.CompletedProcess: As `subprocess.run` returns.

    Raises:
        quiv.JobCancelledError: If the stop event was set while the tool
            ran. The group is stopped first.
        subprocess.TimeoutExpired: If the timeout passed first.
    """
    if capture_output:
        popen_kwargs["stdout"] = subprocess.PIPE
        popen_kwargs["stderr"] = subprocess.PIPE
    if _IS_POSIX:
        popen_kwargs.setdefault("start_new_session", True)
    if stop_event is None:
        stop_event = _current_stop_event()

    name = os.path.basename(str(args[0])) if args else "tool"
    deadline = None if timeout is None else time.monotonic() + timeout

    with subprocess.Popen(args, **popen_kwargs) as proc:
        while True:
            try:
                stdout, stderr = proc.communicate(timeout=_POLL_SECONDS)
                break
            except subprocess.TimeoutExpired:
                if stop_event is not None and stop_event.is_set():
                    _stop_group(proc, kill_grace)
                    logger.info(
                        f"Trailarr stopped {name} and the processes it"
                        " started. A stop was requested."
                    )
                    raise quiv.JobCancelledError(
                        f"{name} was stopped: the job's stop event was set"
                    ) from None
                if deadline is not None and time.monotonic() >= deadline:
                    assert timeout is not None
                    stdout, stderr = _stop_group(proc, kill_grace)
                    raise subprocess.TimeoutExpired(
                        args, timeout, output=stdout, stderr=stderr
                    ) from None

    return subprocess.CompletedProcess(args, proc.returncode, stdout, stderr)
