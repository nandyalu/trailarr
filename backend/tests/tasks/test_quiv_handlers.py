"""Every task handler must register with the quiv version in use.

quiv 1.0.0 renamed the parameters it injects into a handler: `_job_id`,
`_stop_event` and `_progress_hook` became `job_id`, `stop_event` and
`progress_hook`. `add_task()` rejects a handler that still declares an old
name, but only when the app registers it — at startup, or when a user
starts a one-off task. No other test runs `add_task()` with the real
handlers, so these tests register each one on a quiv instance of their own.
"""

import ast
import importlib
import pathlib

import pytest
from quiv import Quiv

from config.logging_context import get_trace_id, with_logging_context
from tasks.schedules import TASK_REGISTRY

BACKEND = pathlib.Path(__file__).resolve().parents[2]
TASKS = BACKEND / "tasks"


def _registered_handlers() -> dict[str, object]:
    """Find every callable that the tasks package passes to `add_task`.

    A `func=` argument is either a module-level function, or a value from
    `TASK_REGISTRY` (read directly, or through a local named `func`).
    Anything else fails the test, so a new form of registration cannot
    slip past it.
    """
    handlers: dict[str, object] = {}
    for path in sorted(TASKS.glob("*.py")):
        module = importlib.import_module(f"tasks.{path.stem}")
        for node in ast.walk(ast.parse(path.read_text())):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_task"
            ):
                continue
            func_arg = next(k.value for k in node.keywords if k.arg == "func")
            where = f"tasks/{path.name}:{node.lineno}"
            if isinstance(func_arg, ast.Name) and func_arg.id == "func":
                for key, handler in TASK_REGISTRY.items():
                    handlers[f"TASK_REGISTRY[{key!r}]"] = handler
            elif (
                isinstance(func_arg, ast.Subscript)
                and isinstance(func_arg.value, ast.Name)
                and func_arg.value.id == "TASK_REGISTRY"
            ):
                for key, handler in TASK_REGISTRY.items():
                    handlers[f"TASK_REGISTRY[{key!r}]"] = handler
            elif isinstance(func_arg, ast.Name):
                handlers[f"{where} {func_arg.id}"] = getattr(
                    module, func_arg.id
                )
            else:
                pytest.fail(
                    f"{where} passes {ast.unparse(func_arg)} to add_task."
                    " Teach this test how to resolve it."
                )
    return handlers


HANDLERS = _registered_handlers()


def test_the_scan_finds_the_handlers():
    """Guard the test below: an empty scan would pass for any code."""
    assert len(HANDLERS) >= len(TASK_REGISTRY) + 5


@pytest.mark.parametrize("name", sorted(HANDLERS))
def test_quiv_accepts_the_handler(name: str):
    scheduler = Quiv()
    try:
        scheduler.add_task(
            task_name="Registration check",
            func=HANDLERS[name],
            interval=3600,
            delay=3600,
            run_once=True,
        )
    finally:
        scheduler.shutdown()


class TestTraceIdFromTheJob:
    """`with_logging_context` names each log line after the job that wrote
    it. It reads the id from the keyword that quiv injects, so the rename
    in quiv 1.0.0 had to reach it too. A stale name raises nothing: the
    lines only lose their task name on the Logs page."""

    def test_sync_handler_uses_the_injected_job_id(self):
        @with_logging_context
        def handler(job_id=None):
            return get_trace_id()

        assert handler(job_id="job-42") == "job-42"

    @pytest.mark.asyncio
    async def test_async_handler_uses_the_injected_job_id(self):
        @with_logging_context
        async def handler(job_id=None):
            return get_trace_id()

        assert await handler(job_id="job-42") == "job-42"
