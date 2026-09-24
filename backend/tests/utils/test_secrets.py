"""Tests for utils/secrets.py."""

from utils.secrets import mask_secret


def test_no_secret_stays_empty():
    """A client tells 'not set' from 'set' by the empty string."""
    assert mask_secret("") == ""


def test_a_short_secret_shows_nothing():
    assert mask_secret("abcd") == "****"
    assert mask_secret("abcdefgh") == "****"


def test_a_long_secret_shows_only_its_last_four():
    masked = mask_secret("7cd673aa4e20351ed73609dd49d199eb")
    assert masked == "****99eb"
    assert "7cd673aa" not in masked
