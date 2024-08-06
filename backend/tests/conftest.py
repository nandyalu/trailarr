import os
from urllib.parse import urlencode, urljoin
from aioresponses import aioresponses
import pytest


# TODO! Update all tests to current codebase
def pytest_configure():
    os.environ["TESTING"] = "True"
    from core.base.database.utils.init_db import init_db

    init_db()


@pytest.fixture(autouse=True)
def debug_database():
    os.environ["TESTING"] = "True"


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
