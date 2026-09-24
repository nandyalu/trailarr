"""Some strings are a contract between two files, not prose.

Phase 7 rewrote every log message, and had to leave some strings alone
because other code reads them. A later prose pass can reword one of them
and no test fails, because each file still works on its own. These tests
record the contract, so that a reword fails here and not in production
(hygiene H17).

- `"YT-DLP Output::"` and `"FFMPEG Output::"`: `services/trailers/video_v2.py`
  writes them in front of the tool output. `config/logs/db_handler.py`
  matches them to move that output into the traceback column. If one side
  changes, the full ffmpeg output comes back on the Logs page.
- The yt-dlp signatures in `utils/error_classify.py`: a failed download
  stores its error text through `classified_error`, which matches fragments
  such as "please sign in". The messages that our own download code raises
  must not match one, or the user sees the wrong reason and the wrong fix.

The message of `ItemNotFoundError` is also a contract (it is the 404
detail). The API tests assert it already.
"""

import ast
import pathlib

import pytest

from utils.error_classify import classify_ytdlp_error

BACKEND = pathlib.Path(__file__).resolve().parents[1]

TOOL_OUTPUT_MARKERS = ("YT-DLP Output::", "FFMPEG Output::")
MARKER_WRITER = BACKEND / "services" / "trailers" / "video_v2.py"
MARKER_READER = BACKEND / "config" / "logs" / "db_handler.py"


@pytest.mark.parametrize("marker", TOOL_OUTPUT_MARKERS)
@pytest.mark.parametrize(
    "path", [MARKER_WRITER, MARKER_READER], ids=["writer", "reader"]
)
def test_tool_output_marker_is_on_both_sides(marker: str, path: pathlib.Path):
    assert marker in path.read_text(), (
        f"{path.relative_to(BACKEND)} no longer contains {marker!r}. The"
        " log handler and the downloader must use the same marker."
    )


def _raise_messages(path: pathlib.Path) -> list[tuple[int, str]]:
    """Return the string parts of each `raise X(...)` in a file."""
    messages = []
    for node in ast.walk(ast.parse(path.read_text())):
        if not (isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call)):
            continue
        parts = [
            sub.value
            for arg in node.exc.args
            for sub in ast.walk(arg)
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str)
        ]
        if parts:
            messages.append((node.lineno, " ".join(parts)))
    return messages


DOWNLOAD_CODE = sorted((BACKEND / "services" / "trailers").rglob("*.py"))


def test_the_scan_finds_raise_messages():
    """Guard the test below: an empty scan would pass for any code."""
    assert sum(len(_raise_messages(p)) for p in DOWNLOAD_CODE) >= 10


@pytest.mark.parametrize(
    "path", DOWNLOAD_CODE, ids=lambda p: str(p.relative_to(BACKEND))
)
def test_own_download_errors_do_not_look_like_ytdlp_errors(
    path: pathlib.Path,
):
    matches = [
        f"line {line}: {text!r} reads as {classify_ytdlp_error(text)!r}"
        for line, text in _raise_messages(path)
        if classify_ytdlp_error(text)
    ]
    assert not matches, (
        "A message that Trailarr raises matches a yt-dlp signature in"
        " utils/error_classify.py, so the user would see the wrong reason:\n"
        + "\n".join(matches)
    )
