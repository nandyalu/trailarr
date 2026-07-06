"""Tests for the update_download_profile endpoint in api/v1/media.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from api.v1.media import update_download_profile
from exceptions import ItemNotFoundError

MEDIA_ID = 42
DOWNLOAD_ID = 7
PROFILE_ID = 3


def make_download(media_id: int = MEDIA_ID) -> SimpleNamespace:
    return SimpleNamespace(
        id=DOWNLOAD_ID, media_id=media_id, file_name="movie-trailer.mkv"
    )


def make_profile() -> SimpleNamespace:
    return SimpleNamespace(
        id=PROFILE_ID,
        customfilter=SimpleNamespace(filter_name="Movie Trailers"),
    )


class TestUpdateDownloadProfile:

    @pytest.mark.asyncio
    async def test_success_updates_tracks_and_broadcasts(self):
        with (
            patch(
                "api.v1.media.download_manager.read",
                return_value=make_download(),
            ),
            patch(
                "api.v1.media.trailerprofile.get_trailerprofile",
                return_value=make_profile(),
            ),
            patch(
                "api.v1.media.download_manager.update_profile_id"
            ) as mock_update,
            patch(
                "api.v1.media.event_manager.track_download_attributed"
            ) as mock_track,
            patch(
                "api.v1.media.websockets.ws_manager.broadcast",
                new=AsyncMock(),
            ) as mock_broadcast,
        ):
            msg = await update_download_profile(
                MEDIA_ID, DOWNLOAD_ID, PROFILE_ID
            )

        mock_update.assert_called_once_with(DOWNLOAD_ID, PROFILE_ID)
        mock_track.assert_called_once()
        mock_broadcast.assert_awaited_once()
        assert "movie-trailer.mkv" in msg
        assert "Movie Trailers" in msg

    @pytest.mark.asyncio
    async def test_download_of_other_media_returns_404(self):
        with (
            patch(
                "api.v1.media.download_manager.read",
                return_value=make_download(media_id=MEDIA_ID + 1),
            ),
            patch(
                "api.v1.media.download_manager.update_profile_id"
            ) as mock_update,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_download_profile(
                    MEDIA_ID, DOWNLOAD_ID, PROFILE_ID
                )

        assert exc_info.value.status_code == 404
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_download_returns_404(self):
        with (
            patch(
                "api.v1.media.download_manager.read",
                side_effect=ItemNotFoundError("Download", DOWNLOAD_ID),
            ),
            patch(
                "api.v1.media.download_manager.update_profile_id"
            ) as mock_update,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_download_profile(
                    MEDIA_ID, DOWNLOAD_ID, PROFILE_ID
                )

        assert exc_info.value.status_code == 404
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_profile_returns_404(self):
        with (
            patch(
                "api.v1.media.download_manager.read",
                return_value=make_download(),
            ),
            patch(
                "api.v1.media.trailerprofile.get_trailerprofile",
                side_effect=ItemNotFoundError("TrailerProfile", PROFILE_ID),
            ),
            patch(
                "api.v1.media.download_manager.update_profile_id"
            ) as mock_update,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_download_profile(
                    MEDIA_ID, DOWNLOAD_ID, PROFILE_ID
                )

        assert exc_info.value.status_code == 404
        mock_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_unexpected_error_returns_500_without_leaking_details(self):
        with (
            patch(
                "api.v1.media.download_manager.read",
                side_effect=RuntimeError("db connection lost"),
            ),
            patch(
                "api.v1.media.download_manager.update_profile_id"
            ) as mock_update,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await update_download_profile(
                    MEDIA_ID, DOWNLOAD_ID, PROFILE_ID
                )

        assert exc_info.value.status_code == 500
        assert "db connection lost" not in exc_info.value.detail
        mock_update.assert_not_called()
