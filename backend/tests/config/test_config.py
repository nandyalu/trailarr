from config.config import config


class TestConfig:

    def test_trailer_resolution_valid_value(self):
        config.trailer_resolution = "720"  # Valid value
        assert config.trailer_resolution == 720

    def test_trailer_resolution_invalid_value(self):
        config.trailer_resolution = "721"  # Invalid value
        assert config.trailer_resolution == 720

    def test_trailer_resolution_invalid_string(self):
        config.trailer_resolution = "abcd"  # Invalid value
        assert config.trailer_resolution == config._DEFAULT_RESOLUTION

    def test_trailer_resolution_valid_with_pixels(self):
        config.trailer_resolution = "2160p"  # value with 'p'
        assert config.trailer_resolution == 2160

    def test_trailer_resolution_valid_name(self):
        config.trailer_resolution = "QHD"  # resolution name
        assert config.trailer_resolution == 1440

    def test_trailer_audio_format(self):
        config.trailer_audio_format = "some format"  # Invalid value
        assert config.trailer_audio_format == "aac"

    def test_trailer_video_format(self):
        config.trailer_video_format = "some format"  # Invalid value
        assert config.trailer_video_format == "h264"

    def test_trailer_file_format(self):
        config.trailer_file_format = "some format"  # Invalid value
        assert config.trailer_file_format == "mkv"
