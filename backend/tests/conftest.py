import inspect
import os
import tempfile
from unittest.mock import Mock
from urllib.parse import urlencode, urljoin

import aiohttp
from aioresponses import aioresponses
import pytest

# aiohttp 3.14 added a required keyword-only ``stream_writer`` argument to
# ``ClientResponse.__init__``. aioresponses (<=0.7.8) builds mocked responses
# without it, so every mocked request raises ``TypeError: ... missing 1
# required keyword-only argument: 'stream_writer'``. aiohttp only reads
# ``stream_writer.output_size``, so a ``Mock(output_size=0)`` suffices.
#
# This mirrors the upstream fix (aioresponses#288, tracking aioresponses#289).
# Shim sourced from: https://github.com/j7an/dep-rank/pull/123
# The signature guard makes it a no-op on aiohttp < 3.14 and once aioresponses
# ships a release that supplies the argument itself; remove this shim then.
_response_init = aiohttp.ClientResponse.__init__
if "stream_writer" in inspect.signature(_response_init).parameters:

    def _patched_response_init(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        kwargs.setdefault("stream_writer", Mock(output_size=0))
        _response_init(self, *args, **kwargs)

    aiohttp.ClientResponse.__init__ = _patched_response_init

_temp_dir = None


# TODO! Update all tests to current codebase
def pytest_configure(config):
    global _temp_dir
    # Create a temporary directory for the test run
    _temp_dir = tempfile.TemporaryDirectory()

    # Set proper permissions (read, write, execute for owner, group, and others)
    os.chmod(_temp_dir.name, 0o755)

    # Set the environment variable for the app
    os.environ["APP_DATA_DIR"] = _temp_dir.name

    # Create necessary subdirectories that the app expects
    logs_dir = os.path.join(_temp_dir.name, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    os.chmod(logs_dir, 0o755)

    # Ensure the directory exists and is accessible
    assert os.path.exists(
        _temp_dir.name
    ), f"Temp directory {_temp_dir.name} does not exist"
    assert os.access(
        _temp_dir.name, os.R_OK | os.W_OK | os.X_OK
    ), f"Insufficient permissions on {_temp_dir.name}"

    # os.environ["TESTING"] = "True"
    from core.base.database.utils.init_db import init_db

    init_db()


def pytest_unconfigure(config):
    global _temp_dir
    if _temp_dir:
        _temp_dir.cleanup()


@pytest.fixture(autouse=True)
def debug_database():
    # os.environ["TESTING"] = "True"
    pass


TEST_AIOHTTP_APIKEY = "API_KEY"
TEST_AIOHTTP_URL = "http://example.com"
TEST_AIOHTTP_PATH = "example"
TEST_AIOHTTP_PARAMS = {"param1": "value1"}
TEST_AIOHTTP_HEADERS = {"X-Api-Key": TEST_AIOHTTP_APIKEY}
TEST_AIOHTTP_RESPONSE = {"some_key": "some_value"}
_URL_W_PATH = urljoin(TEST_AIOHTTP_URL, TEST_AIOHTTP_PATH)
_URL_QUERY = urlencode(TEST_AIOHTTP_PARAMS)
TEST_AIOHTTP_FINAL_URL = f"{_URL_W_PATH}?{_URL_QUERY}"


@pytest.fixture
def debug_aiohttp_200():
    with aioresponses() as m:
        url = TEST_AIOHTTP_FINAL_URL
        headers = TEST_AIOHTTP_HEADERS
        payload = TEST_AIOHTTP_RESPONSE
        m.get(url, status=200, payload=payload, headers=headers)
        m.post(url, status=200, payload=payload, headers=headers)
        m.put(url, status=200, payload=payload, headers=headers)
        m.delete(url, status=200, payload=payload, headers=headers)
        yield m


@pytest.fixture
def debug_aiohttp():
    with aioresponses() as m:
        # TODO: figure out how to pass in the exception to raise and raise that
        yield m
