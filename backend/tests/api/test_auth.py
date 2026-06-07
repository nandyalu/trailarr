"""Tests for api/v1/auth.py — 100% coverage."""

import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock, patch

from api.v1.auth import LoginRequest, _set_session_cookie, auth_status, login, logout


def _mock_response() -> MagicMock:
    """Return a MagicMock that satisfies the FastAPI Response interface."""
    return MagicMock()


class TestSetSessionCookie:
    def test_uses_url_base_as_path_when_set(self):
        response = _mock_response()
        with patch("api.v1.auth.app_settings") as mock_settings:
            mock_settings.url_base = "/trailarr"
            _set_session_cookie("mytoken", response)
        response.set_cookie.assert_called_once_with(
            key="trailarr_session",
            value="mytoken",
            path="/trailarr",
            samesite="lax",
            httponly=True,
        )

    def test_falls_back_to_root_when_url_base_empty(self):
        response = _mock_response()
        with patch("api.v1.auth.app_settings") as mock_settings:
            mock_settings.url_base = ""
            _set_session_cookie("mytoken", response)
        response.set_cookie.assert_called_once_with(
            key="trailarr_session",
            value="mytoken",
            path="/",
            samesite="lax",
            httponly=True,
        )


class TestLogin:
    @pytest.mark.asyncio
    async def test_successful_login_sets_cookie_and_returns_ok(self):
        response = _mock_response()
        request = LoginRequest(username="admin", password="trailarr")
        with (
            patch("api.v1.auth.verify_login"),
            patch("api.v1.auth.create_session", return_value="tok123"),
            patch("api.v1.auth._set_session_cookie") as mock_set_cookie,
        ):
            result = await login(request, response, header_api_key=None)
        assert result == {"status": "ok"}
        mock_set_cookie.assert_called_once_with("tok123", response)

    @pytest.mark.asyncio
    async def test_login_with_valid_api_key_bypasses_credentials(self):
        response = _mock_response()
        request = LoginRequest(username="", password="")
        with (
            patch("api.v1.auth.verify_login") as mock_verify,
            patch("api.v1.auth.create_session", return_value="tok456"),
            patch("api.v1.auth._set_session_cookie"),
        ):
            result = await login(request, response, header_api_key="valid-key")
        mock_verify.assert_called_once_with("", "", "valid-key")
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_invalid_credentials_propagate_401(self):
        response = _mock_response()
        request = LoginRequest(username="bad", password="bad")
        with patch(
            "api.v1.auth.verify_login",
            side_effect=HTTPException(status_code=401, detail="Invalid credentials"),
        ):
            with pytest.raises(HTTPException) as exc:
                await login(request, response, header_api_key=None)
        assert exc.value.status_code == 401


class TestLogout:
    @pytest.mark.asyncio
    async def test_with_session_deletes_session_and_clears_cookie(self):
        response = _mock_response()
        with (
            patch("api.v1.auth.delete_session") as mock_delete,
            patch("api.v1.auth.app_settings") as mock_settings,
        ):
            mock_settings.url_base = "/"
            result = await logout(response, trailarr_session="tok789")
        mock_delete.assert_called_once_with("tok789")
        response.delete_cookie.assert_called_once_with(
            key="trailarr_session", path="/"
        )
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_without_session_skips_delete_and_clears_cookie(self):
        response = _mock_response()
        with (
            patch("api.v1.auth.delete_session") as mock_delete,
            patch("api.v1.auth.app_settings") as mock_settings,
        ):
            mock_settings.url_base = ""
            result = await logout(response, trailarr_session=None)
        mock_delete.assert_not_called()
        response.delete_cookie.assert_called_once_with(
            key="trailarr_session", path="/"
        )
        assert result == {"status": "ok"}


class TestAuthStatus:
    @pytest.mark.asyncio
    async def test_valid_session_cookie_returns_authenticated(self):
        response = _mock_response()
        with patch("api.v1.auth.verify_session", return_value=True):
            result = await auth_status(
                response, header_api_key=None, trailarr_session="valid-tok"
            )
        assert result == {"authenticated": True}
        response.set_cookie.assert_not_called()

    @pytest.mark.asyncio
    async def test_valid_api_key_header_creates_session_and_returns_authenticated(self):
        response = _mock_response()
        with (
            patch("api.v1.auth.verify_session", return_value=False),
            patch("api.v1.auth.create_session", return_value="new-tok"),
            patch("api.v1.auth._set_session_cookie") as mock_set_cookie,
        ):
            result = await auth_status(
                response, header_api_key="valid-api-key", trailarr_session=None
            )
        assert result == {"authenticated": True}
        mock_set_cookie.assert_called_once_with("new-tok", response)

    @pytest.mark.asyncio
    async def test_webui_disable_auth_creates_session_and_returns_authenticated(self):
        response = _mock_response()
        with (
            patch("api.v1.auth.verify_session", return_value=False),
            patch("api.v1.auth.app_settings") as mock_settings,
            patch("api.v1.auth.create_session", return_value="auto-tok"),
            patch("api.v1.auth._set_session_cookie") as mock_set_cookie,
        ):
            mock_settings.webui_disable_auth = True
            result = await auth_status(
                response, header_api_key=None, trailarr_session=None
            )
        assert result == {"authenticated": True}
        mock_set_cookie.assert_called_once_with("auto-tok", response)

    @pytest.mark.asyncio
    async def test_no_session_no_api_key_raises_401(self):
        response = _mock_response()
        with (
            patch("api.v1.auth.verify_session", return_value=False),
            patch("api.v1.auth.app_settings") as mock_settings,
        ):
            mock_settings.webui_disable_auth = False
            with pytest.raises(HTTPException) as exc:
                await auth_status(
                    response, header_api_key=None, trailarr_session=None
                )
        assert exc.value.status_code == 401
