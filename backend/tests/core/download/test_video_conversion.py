#!/usr/bin/env python3
"""Tests for video conversion hardware acceleration functionality."""

import pytest
from unittest.mock import Mock, patch

from core.download.video_conversion import (
    _get_video_options_nvidia,
    _get_video_options_intel,
    _get_video_options_amd,
    _get_video_options,
    get_ffmpeg_cmd,
    _VIDEO_CODECS_NVIDIA,
    _VIDEO_CODECS_INTEL,
    _VIDEO_CODECS_AMD,
)
from core.base.database.models.trailerprofile import TrailerProfileRead


class TestVideoConversionHardwareAcceleration:
    """Test hardware acceleration support for video conversion."""

    @pytest.fixture
    def trailer_profile(self):
        """Create a test trailer profile."""
        return TrailerProfileRead(
            id=1,
            name="test_profile",
            video_format="h264",
            audio_format="aac",
            subtitles_format="srt",
            file_format="mkv",
            video_resolution=1080,
            audio_volume_level=100,
            subtitles_enabled=True,
            subtitles_language="en",
            embed_metadata=True,
            ytdlp_extra_options=""
        )

    def test_nvidia_codec_mappings(self):
        """Test NVIDIA codec mappings."""
        expected_codecs = {
            "h264": "h264_nvenc",
            "h265": "hevc_nvenc",
        }
        assert _VIDEO_CODECS_NVIDIA == expected_codecs

    def test_intel_codec_mappings(self):
        """Test Intel codec mappings."""
        expected_codecs = {
            "h264": "h264_vaapi",
            "h265": "hevc_vaapi",
        }
        assert _VIDEO_CODECS_INTEL == expected_codecs

    def test_amd_codec_mappings(self):
        """Test AMD codec mappings."""
        expected_codecs = {
            "h264": "h264_amf",
            "h265": "hevc_amf",
        }
        assert _VIDEO_CODECS_AMD == expected_codecs

    def test_nvidia_video_options(self):
        """Test NVIDIA video options generation."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options_nvidia("h264", input_file)
        
        expected_options = [
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-i", input_file,
            "-c:v", "h264_nvenc",
            "-preset", "fast",
            "-cq", "22"
        ]
        assert options == expected_options

    def test_intel_video_options(self):
        """Test Intel video options generation."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options_intel("h264", input_file)
        
        expected_options = [
            "-init_hw_device", "vaapi=intel:/dev/dri/renderD128",
            "-filter_hw_device", "intel",
            "-i", input_file,
            "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi",
            "-qp", "22"
        ]
        assert options == expected_options

    def test_amd_video_options(self):
        """Test AMD video options generation."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options_amd("h264", input_file)
        
        expected_options = [
            "-i", input_file,
            "-c:v", "h264_amf",
            "-qp", "22"
        ]
        assert options == expected_options

    @patch('core.download.video_conversion._get_video_options_cpu')
    def test_unsupported_codec_fallback_intel(self, mock_cpu):
        """Test fallback to CPU when codec is not supported by Intel."""
        mock_cpu.return_value = ["-i", "/tmp/test.mkv", "-c:v", "libvpx-vp9"]
        
        result = _get_video_options_intel("vp9", "/tmp/test.mkv")
        mock_cpu.assert_called_once_with("vp9", "/tmp/test.mkv", None)
        assert result == ["-i", "/tmp/test.mkv", "-c:v", "libvpx-vp9"]

    @patch('core.download.video_conversion._get_video_options_cpu')
    def test_unsupported_codec_fallback_amd(self, mock_cpu):
        """Test fallback to CPU when codec is not supported by AMD."""
        mock_cpu.return_value = ["-i", "/tmp/test.mkv", "-c:v", "libvpx-vp9"]
        
        result = _get_video_options_amd("vp9", "/tmp/test.mkv")
        mock_cpu.assert_called_once_with("vp9", "/tmp/test.mkv", None)
        assert result == ["-i", "/tmp/test.mkv", "-c:v", "libvpx-vp9"]

    def test_video_options_copy_mode(self):
        """Test video options with copy mode."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options("copy", input_file, False, False, False)
        
        expected_options = ["-i", input_file, "-c:v", "copy"]
        assert options == expected_options

    def test_video_options_priority_nvidia(self):
        """Test NVIDIA priority in video options."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options("h264", input_file, True, False, False)
        
        assert "h264_nvenc" in options
        assert "h264_vaapi" not in options
        assert "h264_amf" not in options

    def test_video_options_priority_intel(self):
        """Test Intel priority when NVIDIA is disabled."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options("h264", input_file, False, True, False)
        
        assert "h264_vaapi" in options
        assert "h264_nvenc" not in options
        assert "h264_amf" not in options

    def test_video_options_priority_amd(self):
        """Test AMD priority when NVIDIA and Intel are disabled."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options("h264", input_file, False, False, True)
        
        assert "h264_amf" in options
        assert "h264_nvenc" not in options
        assert "h264_vaapi" not in options

    def test_video_options_cpu_fallback(self):
        """Test CPU fallback when all hardware acceleration is disabled."""
        input_file = "/tmp/test_input.mkv"
        options = _get_video_options("h264", input_file, False, False, False)
        
        assert "libx264" in options
        assert "h264_nvenc" not in options
        assert "h264_vaapi" not in options
        assert "h264_amf" not in options

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_intel_gpu(self, mock_settings, mock_media_info, trailer_profile):
        """Test complete ffmpeg command generation with Intel GPU."""
        # Mock settings for Intel GPU
        mock_settings.nvidia_gpu_available = False
        mock_settings.intel_gpu_available = True
        mock_settings.amd_gpu_available = False
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, "/tmp/input.mkv", "/tmp/output.mkv")
        
        # Verify Intel-specific options
        assert "vaapi=intel:/dev/dri/renderD128" in cmd
        assert "format=nv12,hwupload" in cmd
        assert "h264_vaapi" in cmd
        assert "-qp" in cmd
        assert "22" in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_amd_gpu(self, mock_settings, mock_media_info, trailer_profile):
        """Test complete ffmpeg command generation with AMD GPU."""
        # Mock settings for AMD GPU
        mock_settings.nvidia_gpu_available = False
        mock_settings.intel_gpu_available = False
        mock_settings.amd_gpu_available = True
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, "/tmp/input.mkv", "/tmp/output.mkv")
        
        # Verify AMD-specific options
        assert "h264_amf" in cmd
        assert "-qp" in cmd
        assert "22" in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_fallback_mode(self, mock_settings, mock_media_info, trailer_profile):
        """Test fallback mode ignores all hardware acceleration."""
        # Mock settings with all GPUs available
        mock_settings.nvidia_gpu_available = True
        mock_settings.intel_gpu_available = True
        mock_settings.amd_gpu_available = True
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command with fallback=True
        cmd = get_ffmpeg_cmd(trailer_profile, "/tmp/input.mkv", "/tmp/output.mkv", fallback=True)
        
        # Verify CPU encoding is used
        assert "libx264" in cmd
        assert "h264_nvenc" not in cmd
        assert "h264_vaapi" not in cmd
        assert "h264_amf" not in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_hardware_acceleration_disabled(self, mock_settings, mock_media_info, trailer_profile):
        """Test that hardware acceleration is disabled when setting is False."""
        # Mock settings with hardware acceleration disabled
        mock_settings.nvidia_gpu_available = True
        mock_settings.intel_gpu_available = True
        mock_settings.amd_gpu_available = True
        mock_settings.trailer_hardware_acceleration = False
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, "/tmp/input.mkv", "/tmp/output.mkv")
        
        # Verify CPU encoding is used
        assert "libx264" in cmd
        assert "h264_nvenc" not in cmd
        assert "h264_vaapi" not in cmd
        assert "h264_amf" not in cmd