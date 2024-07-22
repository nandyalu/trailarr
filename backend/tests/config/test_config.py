from config.settings import app_settings


class TestConfig:

    def test_trailer_resolution_valid_value(self):
        app_settings.trailer_resolution = "720"  # Valid value
        assert app_settings.trailer_resolution == 720

    def test_trailer_resolution_invalid_value(self):
        app_settings.trailer_resolution = "721"  # Invalid value
        assert app_settings.trailer_resolution == 720

    def test_trailer_resolution_invalid_string(self):
        app_settings.trailer_resolution = "abcd"  # Invalid value
        assert app_settings.trailer_resolution == app_settings._DEFAULT_RESOLUTION

    def test_trailer_resolution_valid_with_pixels(self):
        app_settings.trailer_resolution = "2160p"  # value with 'p'
        assert app_settings.trailer_resolution == 2160

    def test_trailer_resolution_valid_name(self):
        app_settings.trailer_resolution = "QHD"  # resolution name
        assert app_settings.trailer_resolution == 1440

    def test_trailer_audio_format(self):
        app_settings.trailer_audio_format = "some format"  # Invalid value
        assert app_settings.trailer_audio_format == "aac"

    def test_trailer_video_format(self):
        app_settings.trailer_video_format = "some format"  # Invalid value
        assert app_settings.trailer_video_format == "h264"

    def test_trailer_file_format(self):
        app_settings.trailer_file_format = "some format"  # Invalid value
        assert app_settings.trailer_file_format == "mkv"
