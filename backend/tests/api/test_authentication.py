"""Tests for api/v1/authentication.py — the FastAPI dependencies.

The session store and credential checks live in services/auth.py; their
tests are in tests/services/test_auth.py. What is left here is the part that
turns an answer into an HTTP response.

These patch names on api.v1.authentication because that is the module the
functions below resolve them in — the names are re-exported from
services.auth.
"""

import pytest
from fastapi import HTTPException
from unittest.mock import patch

import services.auth as auth_module
from api.v1.authentication import (
    create_session,
    validate_api_key,
    validate_api_key_cookie,
    validate_api_key_header,
    verify_login,
)

VALID_API_KEY = "test-api-key-abc123"


@pytest.fixture(autouse=True)
def clear_sessions():
    """Isolate _sessions state between tests."""
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


class TestVerifyLogin:
    def test_valid_api_key_skips_credential_check(self):
        # Should not raise even with wrong username/password
        verify_login("wrong", "wrong", valid_api_key=VALID_API_KEY)

    def test_valid_credentials_do_not_raise(self):
        with (
            patch("api.v1.authentication.verify_username", return_value=True),
            patch("api.v1.authentication.verify_password", return_value=True),
        ):
            verify_login("admin", "trailarr", valid_api_key=None)

    def test_wrong_username_raises_401(self):
        with (
            patch("api.v1.authentication.verify_username", return_value=False),
            patch("api.v1.authentication.verify_password", return_value=True),
        ):
            with pytest.raises(HTTPException) as exc:
                verify_login("bad", "trailarr", valid_api_key=None)
            assert exc.value.status_code == 401

    def test_wrong_password_raises_401(self):
        with (
            patch("api.v1.authentication.verify_username", return_value=True),
            patch("api.v1.authentication.verify_password", return_value=False),
        ):
            with pytest.raises(HTTPException) as exc:
                verify_login("admin", "bad", valid_api_key=None)
            assert exc.value.status_code == 401


class TestValidateApiKeyHeader:
    def test_valid_key_is_returned(self):
        with patch("api.v1.authentication.verify_api_key", return_value=True):
            result = validate_api_key_header(header_api_key=VALID_API_KEY)
        assert result == VALID_API_KEY

    def test_none_returns_none(self):
        result = validate_api_key_header(header_api_key=None)
        assert result is None

    def test_invalid_key_returns_none(self):
        with patch("api.v1.authentication.verify_api_key", return_value=False):
            result = validate_api_key_header(header_api_key="bad")
        assert result is None


class TestValidateApiKeyCookie:
    def test_valid_session_cookie_returns_true(self):
        token = create_session()
        assert validate_api_key_cookie(trailarr_session=token, trailarr_api_key=None) is True

    def test_valid_api_key_cookie_returns_true(self):
        with patch("api.v1.authentication.verify_api_key", return_value=True):
            result = validate_api_key_cookie(
                trailarr_api_key=VALID_API_KEY, trailarr_session=None
            )
        assert result is True

    def test_no_valid_credentials_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            validate_api_key_cookie(trailarr_api_key=None, trailarr_session=None)
        assert exc.value.status_code == 401


class TestValidateApiKey:
    def test_valid_session_returns_true(self):
        token = create_session()
        result = validate_api_key(
            query_api_key=None,
            header_api_key=None,
            trailarr_api_key=None,
            trailarr_session=token,
        )
        assert result is True

    def test_valid_query_key_returns_true(self):
        with patch("api.v1.authentication.verify_api_key", return_value=True):
            result = validate_api_key(
                query_api_key=VALID_API_KEY,
                header_api_key=None,
                trailarr_api_key=None,
                trailarr_session=None,
            )
        assert result is True

    def test_valid_header_key_returns_true(self):
        with patch("api.v1.authentication.verify_api_key", return_value=True):
            result = validate_api_key(
                query_api_key=None,
                header_api_key=VALID_API_KEY,
                trailarr_api_key=None,
                trailarr_session=None,
            )
        assert result is True

    def test_valid_cookie_key_returns_true(self):
        with patch("api.v1.authentication.verify_api_key", return_value=True):
            result = validate_api_key(
                query_api_key=None,
                header_api_key=None,
                trailarr_api_key=VALID_API_KEY,
                trailarr_session=None,
            )
        assert result is True

    def test_invalid_key_raises_401(self):
        with patch("api.v1.authentication.verify_api_key", return_value=False):
            with pytest.raises(HTTPException) as exc:
                validate_api_key(
                    query_api_key="bad",
                    header_api_key=None,
                    trailarr_api_key=None,
                    trailarr_session=None,
                )
        assert exc.value.status_code == 401

    def test_all_none_raises_401(self):
        with pytest.raises(HTTPException) as exc:
            validate_api_key(
                query_api_key=None,
                header_api_key=None,
                trailarr_api_key=None,
                trailarr_session=None,
            )
        assert exc.value.status_code == 401
