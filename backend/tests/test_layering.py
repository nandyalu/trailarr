"""Guard the backend layering.

Phase 7 gave the backend five layers: api -> services -> database, with
tasks driving services and utils usable by anything. This test keeps that
true. It parses the imports rather than grepping, so comments that mention
a layer, and imports written inside a function, are both counted correctly.

If this test fails, do not add the module to the allow-list to make it pass.
Move the logic instead: the layer below must not know about the layer above.
"""

import ast
import pathlib

BACKEND = pathlib.Path(__file__).resolve().parents[1]

# Layers that sit above the database layer. Nothing in database/ may import
# from these.
ABOVE_DATABASE = {"api", "services", "tasks"}

# utils/ is the shared floor: pure helpers with no dependency on any layer.
FORBIDDEN_FOR_UTILS = {"api", "services", "tasks", "database"}


def _imported_roots(path: pathlib.Path) -> set[str]:
    """Collect the top-level package of every import in a file.

    Covers `import x.y`, `from x.y import z`, and both written inside a
    function body, which is where layering violations tend to hide.
    """
    tree = ast.parse(path.read_text())
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            # level > 0 is a relative import, which stays inside the package
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
    return roots


def _python_files(package: str) -> list[pathlib.Path]:
    return [
        f
        for f in (BACKEND / package).rglob("*.py")
        if "__pycache__" not in f.parts
    ]


def test_database_layer_imports_nothing_above_it():
    """The database layer stores rows. It must not call business logic.

    The connection managers used to reach into the Radarr, Sonarr and Plex
    clients, so a database call did network I/O. The event manager used to
    import the notification dispatcher; it now publishes to listeners that
    register themselves.
    """
    offenders: list[str] = []
    for f in _python_files("database"):
        bad = _imported_roots(f) & ABOVE_DATABASE
        if bad:
            offenders.append(f"{f.relative_to(BACKEND)} imports {sorted(bad)}")

    assert offenders == [], "database/ must not import from " + ", ".join(
        sorted(ABOVE_DATABASE)
    ) + ":\n  " + "\n  ".join(offenders)


def test_utils_layer_imports_no_other_layer():
    """utils/ holds pure helpers. Both database/ and services/ import it, so
    it must depend on none of them."""
    offenders: list[str] = []
    for f in _python_files("utils"):
        bad = _imported_roots(f) & FORBIDDEN_FOR_UTILS
        if bad:
            offenders.append(f"{f.relative_to(BACKEND)} imports {sorted(bad)}")

    assert offenders == [], "utils/ must not import other layers:\n  " + "\n  ".join(
        offenders
    )


def test_no_module_imports_the_retired_core_package():
    """Phase 7 removed core/. Nothing may bring it back by name."""
    offenders: list[str] = []
    for package in ("api", "services", "database", "tasks", "utils", "config"):
        for f in _python_files(package):
            if "core" in _imported_roots(f):
                offenders.append(str(f.relative_to(BACKEND)))

    assert offenders == [], "core/ was retired in Phase 7:\n  " + "\n  ".join(
        offenders
    )
