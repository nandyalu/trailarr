from pathlib import Path
from unittest.mock import patch
import pytest
from main import get_sanitized_path


@pytest.fixture
def base_frontend_dir(tmp_path):
    """Create a temporary frontend directory structure for testing."""
    frontend_dir = tmp_path / "frontend-build" / "browser"
    frontend_dir.mkdir(parents=True, exist_ok=True)

    static_dir = frontend_dir / "assets"
    static_dir.mkdir(exist_ok=True)
    (static_dir / "style.css").touch()
    (static_dir / "script.js").touch()

    return frontend_dir


@pytest.fixture
def mock_frontend_dir(base_frontend_dir):
    """Mock the frontend_dir global variable."""
    with patch("main.frontend_dir", base_frontend_dir):
        yield base_frontend_dir


class TestGetSanitizedPath:

    def test_valid_file_path(self, mock_frontend_dir):
        """Valid relative path to existing file."""
        result = get_sanitized_path("assets/style.css")
        assert result is not None
        assert result.is_file()
        assert result.name == "style.css"

    def test_valid_directory_path(self, mock_frontend_dir):
        """Valid relative path to directory."""
        result = get_sanitized_path("assets")
        assert result is not None
        assert result.is_dir()

    def test_empty_string(self, mock_frontend_dir):
        """Empty string should return None."""
        assert get_sanitized_path("") is None

    def test_whitespace_only_string(self, mock_frontend_dir):
        """Whitespace-only string should return None."""
        assert get_sanitized_path("   ") is None
        assert get_sanitized_path("\t") is None
        assert get_sanitized_path("\n") is None

    def test_leading_slashes_removed(self, mock_frontend_dir):
        """Leading slashes should be stripped."""
        result = get_sanitized_path("/assets/style.css")
        assert result is not None
        assert result.is_file()

    def test_multiple_leading_slashes(self, mock_frontend_dir):
        """Multiple leading slashes should be stripped."""
        result = get_sanitized_path("///assets/style.css")
        assert result is not None
        assert result.is_file()

    def test_directory_traversal_attack_prevented(self, mock_frontend_dir):
        """Path traversal attempts should be blocked."""
        result = get_sanitized_path("../../../etc/passwd")
        assert result is None

    def test_directory_traversal_with_leading_slash(self, mock_frontend_dir):
        """Path traversal with leading slash should be blocked."""
        result = get_sanitized_path("/../../../etc/passwd")
        assert result is None

    def test_directory_traversal_with_url_encode_sequence(
        self, mock_frontend_dir
    ):
        """Path traversal with URL-encoded sequence should be blocked."""
        result = get_sanitized_path("%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd")
        assert result is None

    def test_current_directory_traversal(self, mock_frontend_dir):
        """Current directory (.) traversal should be blocked."""
        result = get_sanitized_path("./../../etc/passwd")
        assert result is None

    def test_nonexistent_path_returns_path_object(self, mock_frontend_dir):
        """Nonexistent but valid path within base dir should return Path object."""
        result = get_sanitized_path("assets/nonexistent.txt")
        assert result is not None
        assert isinstance(result, Path)

    def test_path_with_dots_in_filename(self, mock_frontend_dir):
        """Legitimate dots in filename should work."""
        result = get_sanitized_path("assets/style.css")
        assert result is not None

    def test_nested_directories(self, mock_frontend_dir):
        """Nested valid directories should be allowed."""
        (mock_frontend_dir / "js" / "lib").mkdir(parents=True, exist_ok=True)
        (mock_frontend_dir / "js" / "lib" / "utils.js").touch()

        result = get_sanitized_path("js/lib/utils.js")
        assert result is not None
        assert result.is_file()

    def test_symlink_escape_attempt(self, mock_frontend_dir):
        """Symlinks pointing outside base dir should be blocked."""
        outside_file = mock_frontend_dir.parent / "outside.txt"
        outside_file.touch()

        symlink = mock_frontend_dir / "link_to_outside"
        try:
            symlink.symlink_to(outside_file)
            result = get_sanitized_path("link_to_outside")
            assert result is None
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks not supported on this system")

    def test_root_directory_escape_attempt(self, mock_frontend_dir):
        """Attempt to escape to root should be blocked."""
        result = get_sanitized_path("/..")
        assert result is None

    def test_special_characters_in_filename(self, mock_frontend_dir):
        """Valid special characters in filenames should work."""
        (mock_frontend_dir / "file-with-dash_and_underscore.txt").touch()

        result = get_sanitized_path("file-with-dash_and_underscore.txt")
        assert result is not None
        assert result.is_file()
