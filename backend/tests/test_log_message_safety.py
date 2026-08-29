"""A log message must not raise when something logs it.

An f-string in a log call is only evaluated when that line runs. A name that
does not exist therefore fails at the worst moment — on an error path, in a
backoff, or at the end of a long task — and the traceback replaces the
message the reader needed.

The Stage C rewrite of every log message in Phase 7 introduced exactly this
twice:

- `attempt.next_eligible_at` instead of `next_eligible_at(attempt)`, which
  would have raised the first time a download went into backoff.
- `ProbeStatus.FAIL`, which does not exist, on the line that ends every
  Connection Doctor run.

Both passed the whole test suite. These tests read the calls instead of
running them, so they cover every log line rather than the few a test
happens to reach.
"""

import ast
import importlib
import pathlib

import pytest

BACKEND = pathlib.Path(__file__).resolve().parents[1]
PACKAGES = ("api", "services", "database", "tasks", "utils", "config")

LOG_METHODS = {
    "debug",
    "info",
    "warning",
    "error",
    "exception",
    "critical",
    "trace",
}


def _python_files():
    for package in PACKAGES:
        for f in (BACKEND / package).rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            yield f


def _log_calls(tree):
    """Every logger.<level>(...) call in a module."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in LOG_METHODS:
            continue
        target = func.value
        if isinstance(target, ast.Name) and target.id == "logger":
            yield node


def _attribute_chains(node):
    """Names of the form `a.b` used inside an f-string in the call."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name):
            yield sub.value.id, sub.attr


ENUM_LIKE = {
    "ProbeStatus",
    "LogLevel",
    "EventType",
    "EventSource",
    "ArrType",
    "MonitorStatus",
}


@pytest.mark.parametrize(
    "path", sorted(_python_files()), ids=lambda p: str(p.relative_to(BACKEND))
)
def test_enum_members_named_in_log_messages_exist(path):
    """`ProbeStatus.FAIL` parses fine and raises when the line runs."""
    tree = ast.parse(path.read_text())
    module = None
    bad = []
    for call in _log_calls(tree):
        for owner, attr in _attribute_chains(call):
            if owner not in ENUM_LIKE:
                continue
            if module is None:
                rel = path.relative_to(BACKEND).with_suffix("")
                module = importlib.import_module(".".join(rel.parts))
            enum_cls = getattr(module, owner, None)
            if enum_cls is None:
                continue
            if not hasattr(enum_cls, attr):
                bad.append(f"{owner}.{attr}")
    assert bad == [], (
        f"{path.relative_to(BACKEND)} logs a member that does not exist:"
        f" {bad}. The line would raise when it runs."
    )


def test_no_log_message_puts_a_non_media_id_in_brackets():
    """A `[123]` in a log message is read as the media id.

    `db_handler.py` searches the message for the first bracketed number and
    stores it in the mediaid column, which is what makes the Logs page link
    a line to a title. A bracketed profile, download, channel, connection or
    section id therefore links the line to whatever media has that id.

    Pass the id with `logger.media(...)` instead, and keep other ids out of
    brackets.
    """
    import re

    offenders = []
    bracketed = re.compile(r"\[\{([^{}\[\]]+)\}\]")
    for path in _python_files():
        source = path.read_text()
        tree = ast.parse(source)
        lines = source.splitlines()
        for call in _log_calls(tree):
            block = "\n".join(lines[call.lineno - 1 : call.end_lineno])
            if "logger.media(" in block:
                continue
            for match in bracketed.finditer(block):
                expression = match.group(1)
                if not re.search(r"media", expression, re.I):
                    offenders.append(
                        f"{path.relative_to(BACKEND)}:{call.lineno}"
                        f" -> [{{{expression}}}]"
                    )
    assert offenders == [], (
        "These log messages put a number that is not a media id in square"
        " brackets, so the Logs page links them to the wrong title:\n  "
        + "\n  ".join(offenders)
    )
