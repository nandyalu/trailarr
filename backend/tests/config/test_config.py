import bcrypt

from config.settings import _hashed_webui_password, app_settings

# The default password 'trailarr', hashed.
DEFAULT_HASH = "$2b$12$CU7h.sOkBp5RFRJIYEwXU.1LCUTD2pWE4p5nsW3k1iC9oZEGVWeum"


class TestConfig:
    # ffmpeg_timeout is an int_property(default=15, min_=10, max_=300);
    # these tests cover the shared int_property parsing behavior.

    def test_int_property_string_input(self):
        """Test that int properties accept string input (API use case)"""
        app_settings.ffmpeg_timeout = "120"  # String input like from API
        assert app_settings.ffmpeg_timeout == 120

    def test_int_property_string_below_minimum(self):
        """Test that int properties enforce minimum value with string input"""
        app_settings.ffmpeg_timeout = "5"  # Below minimum of 10
        assert app_settings.ffmpeg_timeout == 10

    def test_int_property_invalid_string(self):
        """Test that int properties handle invalid string input"""
        app_settings.ffmpeg_timeout = "invalid"  # Invalid string
        assert app_settings.ffmpeg_timeout == 15  # Should use default


class TestWebuiPassword:
    # A variable set in docker-compose.yml wins over the stored .env value, so
    # WEBUI_PASSWORD can hold plain text. bcrypt raises an error for a value
    # that is not a hash, which would break the login with a 500 error.

    def test_empty_value_gives_the_default_password(self):
        assert _hashed_webui_password("", DEFAULT_HASH) == DEFAULT_HASH

    def test_improperly_escaped_value_gives_the_default_password(self):
        assert _hashed_webui_password("''", DEFAULT_HASH) == DEFAULT_HASH
        assert _hashed_webui_password(' \t ', DEFAULT_HASH) == DEFAULT_HASH

    def test_existing_hash_is_kept(self):
        assert _hashed_webui_password(DEFAULT_HASH, DEFAULT_HASH) == DEFAULT_HASH

    def test_plain_text_password_is_hashed(self):
        result = _hashed_webui_password("MySecret123", DEFAULT_HASH)
        assert result.startswith("$2")
        assert bcrypt.checkpw(b"MySecret123", result.encode("utf-8"))

    def test_default_password_still_works_after_a_reset(self):
        result = _hashed_webui_password("", DEFAULT_HASH)
        assert bcrypt.checkpw(b"trailarr", result.encode("utf-8"))
