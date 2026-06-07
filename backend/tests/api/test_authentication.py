"""Tests for api/v1/authentication.py — 100% coverage."""

import bcrypt
import pytest
from fastapi import HTTPException
from unittest.mock import patch

import api.v1.authentication as auth_module
from api.v1.authentication import (
    create_session,
    delete_session,
    get_session,
    get_string_hash,
    set_password,
    set_username,
    validate_api_key,
    validate_api_key_cookie,
    validate_api_key_header,
    verify_api_key,
    verify_login,
    verify_password,
    verify_session,
    verify_username,
)

VALID_API_KEY = "test-api-key-abc123"
# bcrypt hash of "trailarr" (the app default)
_HASHED_TRAILARR = "$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"


@pytest.fixture(autouse=True)
def clear_sessions():
    """Isolate _sessions state between tests."""
    auth_module._sessions.clear()
    yield
    auth_module._sessions.clear()


class TestCreateSession:
    def test_returns_64_char_hex_string(self):
        token = create_session()
        assert isinstance(token, str)
        assert len(token) == 64

    def test_adds_token_to_sessions(self):
        token = create_session()
        assert token in auth_module._sessions

    def test_each_call_produces_unique_token(self):
        assert create_session() != create_session()


class TestDeleteSession:
    def test_removes_existing_token(self):
        token = create_session()
        delete_session(token)
        assert token not in auth_module._sessions

    def test_silently_ignores_unknown_token(self):
        delete_session("nonexistent-token")  # must not raise


class TestVerifySession:
    def test_none_returns_false(self):
        assert verify_session(None) is False

    def test_unknown_token_returns_false(self):
        assert verify_session("not-a-real-token") is False

    def test_valid_token_returns_true(self):
        token = create_session()
        assert verify_session(token) is True


class TestGetSession:
    def test_creates_session_when_none_exist(self):
        token = get_session()
        assert token in auth_module._sessions

    def test_returns_existing_session(self):
        existing = create_session()
        result = get_session()
        assert result == existing

    def test_skips_invalid_token_and_creates_new(self):
        # Two tokens in _sessions; patch verify_session so the first token
        # seen fails, exercising the loop-continue branch (31->30).
        create_session()
        create_session()
        with patch("api.v1.authentication.verify_session", side_effect=[False, True]):
            token = get_session()
        assert token in auth_module._sessions


class TestGetStringHash:
    def test_returns_bytes(self):
        result = get_string_hash("hello")
        assert isinstance(result, bytes)

    def test_hash_is_bcrypt_verifiable(self):
        result = get_string_hash("hello")
        assert bcrypt.checkpw(b"hello", result)

    def test_produces_unique_salt_each_call(self):
        assert get_string_hash("same") != get_string_hash("same")


class TestSetUsername:
    def test_sets_username_on_settings(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            set_username("newuser")
        assert mock_settings.webui_username == "newuser"

    def test_returns_success_message(self):
        with patch("api.v1.authentication.app_settings"):
            result = set_username("newuser")
        assert "success" in result.lower()


class TestSetPassword:
    def test_stores_bcrypt_hash(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            set_password("newpass")
        stored_hash = mock_settings.webui_password
        assert bcrypt.checkpw(b"newpass", stored_hash.encode("utf-8"))

    def test_returns_success_message(self):
        with patch("api.v1.authentication.app_settings"):
            result = set_password("newpass")
        assert "success" in result.lower()


class TestVerifyUsername:
    def test_matching_username_returns_true(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.webui_username = "admin"
            assert verify_username("admin") is True

    def test_wrong_username_returns_false(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.webui_username = "admin"
            assert verify_username("notadmin") is False


class TestVerifyPassword:
    def test_matching_password_returns_true(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.webui_password = _HASHED_TRAILARR
            assert verify_password("trailarr") is True

    def test_wrong_password_returns_false(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.webui_password = _HASHED_TRAILARR
            assert verify_password("wrongpass") is False


class TestVerifyApiKey:
    def test_matching_key_returns_true(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.api_key = VALID_API_KEY
            assert verify_api_key(VALID_API_KEY) is True

    def test_wrong_key_returns_false(self):
        with patch("api.v1.authentication.app_settings") as mock_settings:
            mock_settings.api_key = VALID_API_KEY
            assert verify_api_key("bad-key") is False


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
