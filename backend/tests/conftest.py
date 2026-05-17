import os
import tempfile
from urllib.parse import urlencode, urljoin

import pytest
from aioresponses import aioresponses

_temp_dir = None


def pytest_configure(config):
    global _temp_dir
    _temp_dir = tempfile.TemporaryDirectory()
    os.chmod(_temp_dir.name, 0o755)
    os.environ["APP_DATA_DIR"] = _temp_dir.name

    logs_dir = os.path.join(_temp_dir.name, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    os.chmod(logs_dir, 0o755)

    assert os.path.exists(_temp_dir.name)
    assert os.access(_temp_dir.name, os.R_OK | os.W_OK | os.X_OK)

    from db.init_db import init_db
    init_db()


def pytest_unconfigure(config):
    global _temp_dir
    if _temp_dir:
        _temp_dir.cleanup()


@pytest.fixture(autouse=True)
def debug_database():
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
        yield m
