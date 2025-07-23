#!/usr/bin/env python3
"""Tests for video conversion hardware acceleration functionality."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from core.download.video_conversion import (
    _get_video_options_nvidia,
    _get_video_options_vaapi,
    _get_video_options,
    get_ffmpeg_cmd,
    _VIDEO_CODECS_NVIDIA,
    _VIDEO_CODECS_VAAPI,
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

    @pytest.fixture
    def temp_input_file(self):
        """Create a temporary input file path."""
        return os.path.join(tempfile.gettempdir(), "test_input.mkv")

    @pytest.fixture
    def temp_output_file(self):
        """Create a temporary output file path."""
        return os.path.join(tempfile.gettempdir(), "test_output.mkv")

    @pytest.fixture
    def temp_test_file(self):
        """Create a temporary test file path."""
        return os.path.join(tempfile.gettempdir(), "test.mkv")

    def test_nvidia_codec_mappings(self):
        """Test NVIDIA codec mappings."""
        expected_codecs = {
            "h264": "h264_nvenc",
            "h265": "hevc_nvenc",
            "av1": "av1_nvenc",
        }
        assert _VIDEO_CODECS_NVIDIA == expected_codecs

    def test_vaapi_codec_mappings(self):
        """Test VAAPI codec mappings (for Intel and AMD GPUs)."""
        expected_codecs = {
            "h264": "h264_vaapi",
            "h265": "hevc_vaapi",
            "vp8": "vp8_vaapi",
            "vp9": "vp9-vaapi",
            "av1": "av1_vaapi",
        }
        assert _VIDEO_CODECS_VAAPI == expected_codecs

    def test_nvidia_video_options(self, temp_input_file):
        """Test NVIDIA video options generation."""
        options = _get_video_options_nvidia("h264", temp_input_file)
        
        expected_options = [
            "-hwaccel", "cuda",
            "-hwaccel_output_format", "cuda",
            "-i", temp_input_file,
            "vf", "scale_cuda=format=nv12",
            "-c:v", "h264_nvenc",
            "-preset", "fast",
            "-cq", "22",
            "-b:v", "0",
            "-pix_fmt", "yuv420p"
        ]
        assert options == expected_options

    @patch.dict(os.environ, {}, clear=True)
    def test_vaapi_video_options_default_device(self, temp_input_file):
        """Test VAAPI video options generation with default device."""
        options = _get_video_options_vaapi("h264", temp_input_file)
        
        expected_options = [
            "-hwaccel", "vaapi",
            "-hwaccel_device", "/dev/dri/renderD128",
            "-i", temp_input_file,
            "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi",
            "-qp", "22",
            "-b:v", "0",
            "-pix_fmt", "yuv420p"
        ]
        assert options == expected_options

    @patch.dict(os.environ, {'GPU_DEVICE_INTEL': '/dev/dri/renderD129'}, clear=True)
    @patch('config.settings.app_settings')
    def test_vaapi_video_options_intel_device(self, mock_settings, temp_input_file):
        """Test VAAPI video options generation with Intel GPU device."""
        mock_settings.gpu_available_intel = True
        mock_settings.gpu_enabled_intel = True
        mock_settings.gpu_available_amd = False
        mock_settings.gpu_enabled_amd = False
        
        options = _get_video_options_vaapi("h264", temp_input_file)
        
        expected_options = [
            "-hwaccel", "vaapi",
            "-hwaccel_device", "/dev/dri/renderD129",
            "-i", temp_input_file,
            "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi",
            "-qp", "22",
            "-b:v", "0",
            "-pix_fmt", "yuv420p"
        ]
        assert options == expected_options

    @patch.dict(os.environ, {'GPU_DEVICE_AMD': '/dev/dri/renderD130'}, clear=True)
    @patch('config.settings.app_settings')
    def test_vaapi_video_options_amd_device(self, mock_settings, temp_input_file):
        """Test VAAPI video options generation with AMD GPU device."""
        mock_settings.gpu_available_intel = False
        mock_settings.gpu_enabled_intel = False
        mock_settings.gpu_available_amd = True
        mock_settings.gpu_enabled_amd = True
        
        options = _get_video_options_vaapi("h264", temp_input_file)
        
        expected_options = [
            "-hwaccel", "vaapi",
            "-hwaccel_device", "/dev/dri/renderD130",
            "-i", temp_input_file,
            "-vf", "format=nv12,hwupload",
            "-c:v", "h264_vaapi",
            "-qp", "22",
            "-b:v", "0",
            "-pix_fmt", "yuv420p"
        ]
        assert options == expected_options

    @patch('core.download.video_conversion._get_video_options_cpu')
    def test_unsupported_codec_fallback_vaapi(self, mock_cpu, temp_test_file):
        """Test fallback to CPU when codec is not supported by VAAPI."""
        mock_cpu.return_value = ["-i", temp_test_file, "-c:v", "libvpx-vp9"]
        
        result = _get_video_options_vaapi("unsupported_codec", temp_test_file)
        mock_cpu.assert_called_once_with("unsupported_codec", temp_test_file, None)
        assert result == ["-i", temp_test_file, "-c:v", "libvpx-vp9"]

    def test_video_options_copy_mode(self, temp_input_file):
        """Test video options with copy mode."""
        options = _get_video_options("copy", temp_input_file, False, False)
        
        expected_options = ["-i", temp_input_file, "-c:v", "copy"]
        assert options == expected_options

    def test_video_options_priority_nvidia(self, temp_input_file):
        """Test NVIDIA priority in video options."""
        options = _get_video_options("h264", temp_input_file, True, False)
        
        assert "h264_nvenc" in options
        assert "h264_vaapi" not in options

    def test_video_options_priority_vaapi(self, temp_input_file):
        """Test VAAPI priority when NVIDIA is disabled."""
        options = _get_video_options("h264", temp_input_file, False, True)
        
        assert "h264_vaapi" in options
        assert "h264_nvenc" not in options

    def test_video_options_cpu_fallback(self, temp_input_file):
        """Test CPU fallback when all hardware acceleration is disabled."""
        options = _get_video_options("h264", temp_input_file, False, False)
        
        assert "libx264" in options
        assert "h264_nvenc" not in options
        assert "h264_vaapi" not in options

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_intel_gpu(self, mock_settings, mock_media_info, trailer_profile, temp_input_file, temp_output_file):
        """Test complete ffmpeg command generation with Intel GPU."""
        # Mock settings for Intel GPU
        mock_settings.gpu_available_nvidia = False
        mock_settings.gpu_enabled_nvidia = False
        mock_settings.gpu_available_intel = True
        mock_settings.gpu_enabled_intel = True
        mock_settings.gpu_available_amd = False
        mock_settings.gpu_enabled_amd = False
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, temp_input_file, temp_output_file)
        
        # Verify VAAPI-specific options
        assert "vaapi" in cmd
        assert "format=nv12,hwupload" in cmd
        assert "h264_vaapi" in cmd
        assert "-qp" in cmd
        assert "22" in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_amd_gpu(self, mock_settings, mock_media_info, trailer_profile, temp_input_file, temp_output_file):
        """Test complete ffmpeg command generation with AMD GPU."""
        # Mock settings for AMD GPU
        mock_settings.gpu_available_nvidia = False
        mock_settings.gpu_enabled_nvidia = False
        mock_settings.gpu_available_intel = False
        mock_settings.gpu_enabled_intel = False
        mock_settings.gpu_available_amd = True
        mock_settings.gpu_enabled_amd = True
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, temp_input_file, temp_output_file)
        
        # Verify VAAPI-specific options (same as Intel since we use VAAPI for both)
        assert "vaapi" in cmd
        assert "format=nv12,hwupload" in cmd
        assert "h264_vaapi" in cmd
        assert "-qp" in cmd
        assert "22" in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_fallback_mode(self, mock_settings, mock_media_info, trailer_profile, temp_input_file, temp_output_file):
        """Test fallback mode ignores all hardware acceleration."""
        # Mock settings with all GPUs available
        mock_settings.gpu_available_nvidia = True
        mock_settings.gpu_enabled_nvidia = True
        mock_settings.gpu_available_intel = True
        mock_settings.gpu_enabled_intel = True
        mock_settings.gpu_available_amd = True
        mock_settings.gpu_enabled_amd = True
        mock_settings.trailer_hardware_acceleration = True
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command with fallback=True
        cmd = get_ffmpeg_cmd(trailer_profile, temp_input_file, temp_output_file, fallback=True)
        
        # Verify CPU encoding is used
        assert "libx264" in cmd
        assert "h264_nvenc" not in cmd
        assert "h264_vaapi" not in cmd

    @patch('core.download.video_conversion.get_media_info')
    @patch('config.settings.app_settings')
    def test_ffmpeg_cmd_hardware_acceleration_disabled(self, mock_settings, mock_media_info, trailer_profile, temp_input_file, temp_output_file):
        """Test that hardware acceleration is disabled when setting is False."""
        # Mock settings with hardware acceleration disabled
        mock_settings.gpu_available_nvidia = True
        mock_settings.gpu_enabled_nvidia = True
        mock_settings.gpu_available_intel = True
        mock_settings.gpu_enabled_intel = True
        mock_settings.gpu_available_amd = True
        mock_settings.gpu_enabled_amd = True
        mock_settings.trailer_hardware_acceleration = False
        
        # Mock media info
        mock_media_info.return_value = None
        
        # Generate command
        cmd = get_ffmpeg_cmd(trailer_profile, temp_input_file, temp_output_file)
        
        # Verify CPU encoding is used
        assert "libx264" in cmd
        assert "h264_nvenc" not in cmd
        assert "h264_vaapi" not in cmd