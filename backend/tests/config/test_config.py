# FILEPATH: /media/all/Media/scripts/indexarr2/backend/tests/config/test_config.py


from config.config import config


class TestConfig:

    def test_trailer_resolution_valid_value(self):
        config.trailer_resolution = "720p"  # Valid value
        assert config.trailer_resolution == "720p"

    def test_trailer_resolution_invalid_value(self):
        config.trailer_resolution = "721p"  # Invalid value
        assert config.trailer_resolution == "720p"

    def test_trailer_resolution_invalid_string(self):
        config.trailer_resolution = "abcd"  # Invalid value
        assert config.trailer_resolution == config._DEFAULT_RESOLUTION

    def test_trailer_resolution_valid_without_pixels(self):
        config.trailer_resolution = "2160"  # value without 'p'
        assert config.trailer_resolution == "2160p"

    def test_trailer_resolution_valid_name(self):
        config.trailer_resolution = "QHD"  # value without 'p'
        assert config.trailer_resolution == "1440p"

    def test_trailer_quality(self):
        config.trailer_quality = "some quality"  # Invalid value
        assert config.trailer_quality == "high"

    def test_trailer_audio_format(self):
        config.trailer_audio_format = "some format"  # Invalid value
        assert config.trailer_audio_format == "aac"

    def test_trailer_video_format(self):
        config.trailer_video_format = "some format"  # Invalid value
        assert config.trailer_video_format == "x264"

    def test_trailer_file_format(self):
        config.trailer_file_format = "some format"  # Invalid value
        assert config.trailer_file_format == "mkv"
