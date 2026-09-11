"""Tests for services/settings.py.

This logic sat in the api/v1/settings.py handlers and had no tests. Phase 7
Stage B moved it into a service, which made it reachable without going
through HTTP.

Both functions answer with a message instead of raising. The frontend reads
that message from a 200 response, so the exact wording is part of the
contract.
"""

from unittest.mock import AsyncMock, patch

import pytest

from services import settings as settings_service

PKG = "services.settings"


class TestUpdateSetting:

    @pytest.mark.asyncio
    async def test_missing_key_is_refused(self):
        result = await settings_service.update_setting(None, "x")
        assert result == "Error updating setting: Key is required"

    @pytest.mark.asyncio
    async def test_empty_key_is_refused(self):
        result = await settings_service.update_setting("", "x")
        assert result == "Error updating setting: Key is required"

    @pytest.mark.asyncio
    async def test_none_value_is_refused(self):
        result = await settings_service.update_setting("monitor_enabled", None)
        assert result == "Error updating setting: Value is required"

    @pytest.mark.asyncio
    async def test_empty_value_is_refused(self):
        result = await settings_service.update_setting("monitor_enabled", "")
        assert result == "Error updating setting: Value is required"

    @pytest.mark.asyncio
    async def test_unknown_key_is_refused_and_lists_the_valid_ones(self):
        result = await settings_service.update_setting("not_a_setting", "x")
        assert result.startswith("Error updating setting: Invalid key")
        assert "not_a_setting" in result

    @pytest.mark.asyncio
    async def test_a_known_key_is_written_and_reported(self):
        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.monitor_enabled = False
            result = await settings_service.update_setting(
                "monitor_enabled", True
            )

        assert mock_settings.monitor_enabled is True
        assert result.startswith("Setting Monitor Enabled updated to")

    @pytest.mark.asyncio
    async def test_zero_is_a_real_value_not_a_missing_one(self):
        """0 is falsy but valid — only None and "" are refused."""
        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.monitor_interval = 60
            result = await settings_service.update_setting("monitor_interval", 0)

        assert mock_settings.monitor_interval == 0
        assert "updated to" in result


class TestUpdateLogin:

    @pytest.mark.asyncio
    async def test_current_password_is_required(self):
        result = settings_service.update_login(None, "newuser", "newpass")
        assert result == "Error updating login: Current password is required!"

    @pytest.mark.asyncio
    async def test_wrong_current_password_is_refused(self):
        with patch(f"{PKG}.auth.verify_password", return_value=False):
            result = settings_service.update_login("wrong", "newuser", None)
        assert result == "Error updating login: Current password is incorrect!"

    @pytest.mark.asyncio
    async def test_username_only(self):
        with (
            patch(f"{PKG}.auth.verify_password", return_value=True),
            patch(
                f"{PKG}.auth.set_username", return_value="Username updated successfully"
            ) as mock_user,
            patch(f"{PKG}.auth.set_password") as mock_pass,
        ):
            result = settings_service.update_login("right", "newuser", None)

        mock_user.assert_called_once_with("newuser")
        mock_pass.assert_not_called()
        assert result == "Username updated successfully"

    @pytest.mark.asyncio
    async def test_password_only(self):
        with (
            patch(f"{PKG}.auth.verify_password", return_value=True),
            patch(f"{PKG}.auth.set_username") as mock_user,
            patch(
                f"{PKG}.auth.set_password", return_value="Password updated successfully"
            ) as mock_pass,
        ):
            result = settings_service.update_login("right", None, "newpass")

        mock_user.assert_not_called()
        mock_pass.assert_called_once_with("newpass")
        assert result == "Password updated successfully"

    @pytest.mark.asyncio
    async def test_both_username_and_password(self):
        with (
            patch(f"{PKG}.auth.verify_password", return_value=True),
            patch(f"{PKG}.auth.set_username") as mock_user,
            patch(f"{PKG}.auth.set_password") as mock_pass,
        ):
            result = settings_service.update_login(
                "right", "newuser", "newpass"
            )

        mock_user.assert_called_once_with("newuser")
        mock_pass.assert_called_once_with("newpass")
        assert result == "Username and password updated successfully"

    @pytest.mark.asyncio
    async def test_neither_username_nor_password_changes_nothing(self):
        with (
            patch(f"{PKG}.auth.verify_password", return_value=True),
            patch(f"{PKG}.auth.set_username") as mock_user,
            patch(f"{PKG}.auth.set_password") as mock_pass,
        ):
            result = settings_service.update_login("right", None, None)

        mock_user.assert_not_called()
        mock_pass.assert_not_called()
        assert result == "Error updating credentials: None were provided!"


class TestSecretSettings:
    """The TMDB key is checked before it is stored, and never sent back.

    The API answers with a masked key, so the page shows `****99eb`. A save
    of the page that did not touch the field sends that text back, and
    writing it would replace a working key with the mask.
    """

    KEY = "7cd673aa4e20351ed73609dd49d199eb"

    @pytest.mark.asyncio
    async def test_a_good_key_is_stored(self):
        with patch(f"{PKG}.app_settings") as mock_settings:
            with patch(f"{PKG}.TMDBAPI") as api:
                api.return_value.validate_key = AsyncMock(
                    return_value="TMDB key accepted."
                )
                result = await settings_service.update_setting(
                    "tmdb_api_key", self.KEY
                )

        assert mock_settings.tmdb_api_key == self.KEY
        assert result == "Setting Tmdb Api Key updated."

    @pytest.mark.asyncio
    async def test_the_message_never_repeats_the_key(self):
        with patch(f"{PKG}.app_settings"):
            with patch(f"{PKG}.TMDBAPI") as api:
                api.return_value.validate_key = AsyncMock(return_value="ok")
                result = await settings_service.update_setting(
                    "tmdb_api_key", self.KEY
                )

        assert self.KEY not in result

    @pytest.mark.asyncio
    async def test_the_masked_value_coming_back_changes_nothing(self):
        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.tmdb_api_key = self.KEY
            with patch(f"{PKG}.TMDBAPI") as api:
                result = await settings_service.update_setting(
                    "tmdb_api_key", "****99eb"
                )

        assert mock_settings.tmdb_api_key == self.KEY, "the key was overwritten"
        assert api.call_count == 0, "a masked value must not reach TMDB"
        assert result == "The TMDB API key did not change."

    @pytest.mark.asyncio
    async def test_a_key_that_tmdb_refuses_is_not_stored(self):
        from services.tmdb.api_manager import TMDBAuthError

        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.tmdb_api_key = "old-key"
            with patch(f"{PKG}.TMDBAPI") as api:
                api.return_value.validate_key = AsyncMock(
                    side_effect=TMDBAuthError("no")
                )
                result = await settings_service.update_setting(
                    "tmdb_api_key", "wrong"
                )

        assert mock_settings.tmdb_api_key == "old-key"
        assert result.startswith("Error updating setting: TMDB refused")

    @pytest.mark.asyncio
    async def test_a_key_is_stored_when_tmdb_cannot_be_reached(self):
        """The network is the problem, not the key. Refusing it would stop
        a user setting up Trailarr while TMDB is down."""
        with patch(f"{PKG}.app_settings") as mock_settings:
            with patch(f"{PKG}.TMDBAPI") as api:
                api.return_value.validate_key = AsyncMock(
                    side_effect=OSError("network down")
                )
                result = await settings_service.update_setting(
                    "tmdb_api_key", self.KEY
                )

        assert mock_settings.tmdb_api_key == self.KEY
        assert result == "Setting Tmdb Api Key updated."
