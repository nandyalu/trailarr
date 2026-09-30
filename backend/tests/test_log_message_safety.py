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


@pytest.mark.parametrize(
    "path", sorted(_python_files()), ids=lambda p: str(p.relative_to(BACKEND))
)
def test_attributes_read_from_an_annotated_argument_exist(path):
    """`media.title` where `media: MediaImage` has no title.

    A log message reaches for a field of one of its function's arguments.
    When the argument carries a type annotation, that type has to have the
    field, or the line raises AttributeError when it runs.

    This is the mistake the Stage C sweep made three times: MediaImage has
    id, is_poster, image_url, image_path and headers, but no title, so
    every image download would have raised.
    """
    source = path.read_text()
    tree = ast.parse(source)
    module = None
    bad = []
    for func in ast.walk(tree):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        # argument name -> annotation name, for simple annotations only
        annotated = {}
        for arg in list(func.args.args) + list(func.args.kwonlyargs):
            ann = arg.annotation
            if isinstance(ann, ast.Name):
                annotated[arg.arg] = ann.id
        if not annotated:
            continue
        for call in _log_calls(func):
            for owner, attr in _attribute_chains(call):
                if owner not in annotated:
                    continue
                type_name = annotated[owner]
                if module is None:
                    rel = path.relative_to(BACKEND).with_suffix("")
                    module = importlib.import_module(".".join(rel.parts))
                cls = getattr(module, type_name, None)
                if cls is None or not isinstance(cls, type):
                    continue
                fields = (
                    set(dir(cls))
                    | set(getattr(cls, "__annotations__", {}))
                    | set(getattr(cls, "model_fields", {}))
                )
                if attr not in fields:
                    bad.append(f"{owner}.{attr} ({type_name} has no {attr})")
    assert bad == [], (
        f"{path.relative_to(BACKEND)} logs a field that does not exist:"
        f" {bad}. The line would raise when it runs."
    )


def test_no_log_message_puts_an_id_in_brackets():
    """A `[123]` in a log message links nothing.

    `db_handler.py` used to read the first bracketed number as the media id.
    A bracketed profile, download or channel id then linked the line to the
    wrong title. v0.13.1 removed that fallback (hygiene H14), so only
    `logger.media(...)` links a line now.

    An id in brackets is the old habit. For a media id it looks like a link
    and is not one; for any other id it is noise. Pass a media id with
    `logger.media(...)`, and name the other thing instead of its id.
    """
    import re

    offenders = []
    bracketed_id = re.compile(r"\[\{([^{}\[\]]*id)\}\]", re.I)
    for path in _python_files():
        source = path.read_text()
        tree = ast.parse(source)
        lines = source.splitlines()
        for call in _log_calls(tree):
            block = "\n".join(lines[call.lineno - 1 : call.end_lineno])
            for match in bracketed_id.finditer(block):
                offenders.append(
                    f"{path.relative_to(BACKEND)}:{call.lineno}"
                    f" -> [{{{match.group(1)}}}]"
                )
    assert offenders == [], (
        "These log messages put an id in square brackets. Brackets no"
        " longer link a line to a title; use logger.media(...):\n  "
        + "\n  ".join(offenders)
    )


def _calls_logger_media(tree) -> bool:
    """Whether the module really calls `logger.media(...)`.

    Read from the syntax tree, not from the text: two modules describe the
    call in a docstring without making it.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "media":
            continue
        if isinstance(func.value, ast.Name) and func.value.id == "logger":
            return True
    return False


def _binds_logger_to_a_module_logger(tree) -> bool:
    """Whether `logger = ModuleLogger(...)` appears at module level."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "logger" not in names:
            continue
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name):
            if call.func.id == "ModuleLogger":
                return True
    return False


def _imports_the_plain_logger(tree) -> bool:
    """Whether the module does `from app_logger import logger`."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "app_logger":
            if any(alias.name == "logger" for alias in node.names):
                return True
    return False


@pytest.mark.parametrize("path", list(_python_files()), ids=lambda p: p.name)
def test_logger_media_is_called_on_a_logger_that_has_it(path):
    """`logger.media(id)` needs a ModuleLogger, not the plain logger.

    `media()` lives on ModuleLogger. `from app_logger import logger` gives
    a plain `logging.Logger`, which parses fine and raises
    AttributeError the moment the line runs.

    This shipped: `services/images/image.py` imported the plain logger and
    called `logger.media(media.id)`, so the Image Refresh task died every
    time — and with it the Arr Data Refresh, which refreshes images when it
    finishes. Nothing failed until a user's container ran the task.
    """
    tree = ast.parse(path.read_text())
    if not _calls_logger_media(tree):
        # A module that only mentions it in prose is not calling it.
        return
    assert not _imports_the_plain_logger(tree), (
        f"{path.relative_to(BACKEND)} calls logger.media() but imports the"
        " plain logger from app_logger. Use ModuleLogger instead."
    )
    assert _binds_logger_to_a_module_logger(tree), (
        f"{path.relative_to(BACKEND)} calls logger.media() without binding"
        " logger = ModuleLogger(...) at module level."
    )
