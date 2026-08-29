"""Every handler that maps errors must be able to log them.

`errors.as_http_error` takes the module logger so the traceback lands under
the right name. A module that calls it without defining `logger` raises
NameError — but only on the error path, which no test walked. That shipped a
raw 500 with no log line at all until it was found by driving the running
app.

These tests check the wiring by reading the modules, so they cover every
handler rather than the few an integration test happens to reach.
"""

import ast
import importlib
import pathlib

import pytest

API_DIR = pathlib.Path(__file__).resolve().parents[2] / "api" / "v1"


def _calls_the_error_mapper(source: str) -> bool:
    """True when the module CALLS as_http_error.

    Checked by parsing, not by searching the text, so the module that
    defines the helper is not mistaken for one that uses it.
    """
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "attr", None) or getattr(node.func, "id", None)
        if name == "as_http_error":
            return True
    return False


def _modules_using_the_error_mapper() -> list[pathlib.Path]:
    return [
        f
        for f in sorted(API_DIR.glob("*.py"))
        if _calls_the_error_mapper(f.read_text())
    ]


def test_the_error_mapper_is_actually_used():
    """Guard the guard: if the helper is renamed, these tests must not
    quietly start checking nothing."""
    assert _modules_using_the_error_mapper(), (
        "No api/v1 module calls errors.as_http_error — did it get renamed?"
    )


@pytest.mark.parametrize(
    "module_path",
    _modules_using_the_error_mapper(),
    ids=lambda p: p.name,
)
def test_a_module_that_maps_errors_defines_a_logger(module_path):
    """`logger=logger` needs a module-level `logger` to resolve."""
    module = importlib.import_module(f"api.v1.{module_path.stem}")
    assert hasattr(module, "logger"), (
        f"api/v1/{module_path.name} passes logger=logger to as_http_error"
        " but defines no module-level logger. The NameError would only"
        " appear when a request fails."
    )


@pytest.mark.parametrize(
    "module_path",
    _modules_using_the_error_mapper(),
    ids=lambda p: p.name,
)
def test_every_name_the_error_mapper_is_given_resolves(module_path):
    """Read each as_http_error call and check its arguments exist.

    A keyword argument that names something undefined only fails when the
    handler fails, which is exactly when the app should still work.
    """
    module = importlib.import_module(f"api.v1.{module_path.stem}")
    tree = ast.parse(module_path.read_text())
    missing = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = getattr(func, "attr", None) or getattr(func, "id", None)
        if name != "as_http_error":
            continue
        for kw in node.keywords:
            if isinstance(kw.value, ast.Name):
                # the caught exception is a local; everything else is global
                if kw.value.id in ("e", "exc"):
                    continue
                if not hasattr(module, kw.value.id):
                    missing.append(f"{kw.arg}={kw.value.id}")
    assert missing == [], (
        f"api/v1/{module_path.name} passes names that do not exist: {missing}"
    )
