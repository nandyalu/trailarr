from config.settings import app_settings


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
