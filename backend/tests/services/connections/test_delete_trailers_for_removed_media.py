"""A media item that leaves its library loses its trailers, and only its
trailers — code review of Phase 9, finding 1.

The scan records the extras that a person placed (a featurette, a deleted
scene) as download rows. Trailarr never downloaded them, so it never
deletes them: a person deletes an extra from the Files section.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from services.connections.base import delete_trailers_for_removed_media

PKG = "services.connections.base"


def _download(path: str, video_type: str, file_exists: bool = True):
    return SimpleNamespace(
        path=path, video_type=video_type, file_exists=file_exists
    )


def _media(downloads):
    return SimpleNamespace(
        id=1, title="Gone Movie", folder_path=None, downloads=downloads
    )


class TestOnlyTheTrailersAreDeleted:
    @pytest.mark.asyncio
    async def test_an_extra_that_a_person_placed_stays(self):
        media = _media(
            [
                _download("/m/Trailers/Movie-trailer.mkv", "trailer"),
                _download("/m/Featurettes/Making Of.mkv", "featurette"),
                _download("/m/Deleted Scenes/x.mkv", "other"),
            ]
        )
        with (
            patch(f"{PKG}.app_settings") as settings,
            patch(
                f"{PKG}.FilesHandler.delete_file",
                new_callable=AsyncMock,
                return_value=True,
            ) as delete_file,
        ):
            settings.delete_trailer_media = False
            deleted = await delete_trailers_for_removed_media(
                media, "Arr application"
            )

        assert deleted is True
        delete_file.assert_awaited_once_with("/m/Trailers/Movie-trailer.mkv")

    @pytest.mark.asyncio
    async def test_a_teaser_is_not_a_trailer_either(self):
        media = _media([_download("/m/Trailers/Movie-teaser.mkv", "teaser")])
        with (
            patch(f"{PKG}.app_settings") as settings,
            patch(
                f"{PKG}.FilesHandler.delete_file", new_callable=AsyncMock
            ) as delete_file,
        ):
            settings.delete_trailer_media = False
            deleted = await delete_trailers_for_removed_media(
                media, "Plex library"
            )

        assert deleted is False
        delete_file.assert_not_awaited()
