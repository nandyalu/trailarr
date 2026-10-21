"""Tests for get_base_path in services/images/image.py."""

import asyncio
from pathlib import Path
from unittest.mock import patch

from services.images import image


def test_base_path_is_created_once_and_cached(tmp_path: Path):
    movies = tmp_path / "movies"
    image.get_base_path.cache_clear()
    with (
        patch.object(image, "STATIC_PATH_MOVIES", movies),
        patch.object(Path, "mkdir", autospec=True, side_effect=Path.mkdir) as mk,
    ):
        first = image.get_base_path(True, True)
        calls_after_first = mk.call_count
        second = image.get_base_path(True, True)
    assert first == second == movies / "posters"
    assert first.is_dir()
    assert calls_after_first >= 1
    assert mk.call_count == calls_after_first
    image.get_base_path.cache_clear()


def test_base_path_survives_an_event_loop_change(tmp_path: Path):
    """The scheduler runs each job on a new loop. A cached path must not
    depend on the loop it was first built on."""
    shows = tmp_path / "shows"
    image.get_base_path.cache_clear()
    with patch.object(image, "STATIC_PATH_SHOWS", shows):
        one = asyncio.run(asyncio.sleep(0, image.get_base_path(False, False)))
        two = asyncio.run(asyncio.sleep(0, image.get_base_path(False, False)))
    assert one is two == shows / "fanart"
    image.get_base_path.cache_clear()
