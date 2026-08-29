"""Tests for services/settings.py.

This logic sat in the api/v1/settings.py handlers and had no tests. Phase 7
Stage B moved it into a service, which made it reachable without going
through HTTP.

Both functions answer with a message instead of raising. The frontend reads
that message from a 200 response, so the exact wording is part of the
contract.
"""

from unittest.mock import patch

from services import settings as settings_service

PKG = "services.settings"


class TestUpdateSetting:

    def test_missing_key_is_refused(self):
        result = settings_service.update_setting(None, "x")
        assert result == "Error updating setting: Key is required"

    def test_empty_key_is_refused(self):
        result = settings_service.update_setting("", "x")
        assert result == "Error updating setting: Key is required"

    def test_none_value_is_refused(self):
        result = settings_service.update_setting("monitor_enabled", None)
        assert result == "Error updating setting: Value is required"

    def test_empty_value_is_refused(self):
        result = settings_service.update_setting("monitor_enabled", "")
        assert result == "Error updating setting: Value is required"

    def test_unknown_key_is_refused_and_lists_the_valid_ones(self):
        result = settings_service.update_setting("not_a_setting", "x")
        assert result.startswith("Error updating setting: Invalid key")
        assert "not_a_setting" in result

    def test_a_known_key_is_written_and_reported(self):
        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.monitor_enabled = False
            result = settings_service.update_setting(
                "monitor_enabled", True
            )

        assert mock_settings.monitor_enabled is True
        assert result.startswith("Setting Monitor Enabled updated to")

    def test_zero_is_a_real_value_not_a_missing_one(self):
        """0 is falsy but valid — only None and "" are refused."""
        with patch(f"{PKG}.app_settings") as mock_settings:
            mock_settings.monitor_interval = 60
            result = settings_service.update_setting("monitor_interval", 0)

        assert mock_settings.monitor_interval == 0
        assert "updated to" in result


class TestUpdateLogin:

    def test_current_password_is_required(self):
        result = settings_service.update_login(None, "newuser", "newpass")
        assert result == "Error updating login: Current password is required!"

    def test_wrong_current_password_is_refused(self):
        with patch(f"{PKG}.auth.verify_password", return_value=False):
            result = settings_service.update_login("wrong", "newuser", None)
        assert result == "Error updating login: Current password is incorrect!"

    def test_username_only(self):
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

    def test_password_only(self):
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

    def test_both_username_and_password(self):
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

    def test_neither_username_nor_password_changes_nothing(self):
        with (
            patch(f"{PKG}.auth.verify_password", return_value=True),
            patch(f"{PKG}.auth.set_username") as mock_user,
            patch(f"{PKG}.auth.set_password") as mock_pass,
        ):
            result = settings_service.update_login("right", None, None)

        mock_user.assert_not_called()
        mock_pass.assert_not_called()
        assert result == "Error updating credentials: None were provided!"
