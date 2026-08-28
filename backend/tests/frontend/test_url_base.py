"""Tests for URL_BASE (reverse proxy) serving and the session cookie.

These tests send real requests through the ASGI stack (middleware, routes and
static files). They cover the reverse proxy problems reported in
https://github.com/nandyalu/trailarr/issues/663:
  - the session cookie was scoped to the URL base, which caused a 401 error
    for every API call made from the root path,
  - the prefix middleware was registered only at startup, so a URL base set in
    the WebUI made the API return "405 Method Not Allowed" until a restart.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.auth import auth_router
from frontend import router as frontend_router
from frontend.router import setup_frontend

INDEX_HTML = (
    '<!doctype html><html><head><base href="/"><title>Trailarr</title>'
    "</head><body><app-root></app-root></body></html>"
)


@pytest.fixture
def frontend_dir(tmp_path: Path) -> Path:
    """Create a frontend build folder with an index.html and an asset."""
    build_dir = tmp_path / "frontend-build" / "browser"
    (build_dir / "assets").mkdir(parents=True)
    (build_dir / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (build_dir / "assets" / "style.css").write_text("body{}", encoding="utf-8")
    return build_dir


@pytest.fixture
def default_credentials(monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    """Use the default WebUI username and password for login tests."""
    monkeypatch.delenv("WEBUI_USERNAME", raising=False)
    monkeypatch.delenv("WEBUI_PASSWORD", raising=False)
    return "admin", "trailarr"


def _build_app(frontend_dir: Path) -> FastAPI:
    """Build an app with an API route, the auth routes and frontend serving."""
    app = FastAPI()

    @app.post("/api/v1/ping")
    async def ping() -> dict:
        return {"ping": "pong"}

    @app.get("/status")
    async def status() -> dict:
        return {"status": "healthy"}

    app.include_router(auth_router, prefix="/api/v1")
    with patch(
        "frontend.router._resolve_frontend_dir", return_value=frontend_dir
    ):
        setup_frontend(app)
    return app


def _base_href(html: str) -> str:
    """Return the base href value of an index.html response."""
    start = html.index('<base href="') + len('<base href="')
    return html[start: html.index('"', start)]


@pytest.fixture(autouse=True)
def clear_sub_index_cache():
    """Keep the index.html cache out of other tests."""
    frontend_router._sub_index_cache.clear()
    yield
    frontend_router._sub_index_cache.clear()


class TestUrlBaseSetAtStartup:
    """URL_BASE is set before the app starts — the usual Docker setup."""

    @pytest.fixture
    def client(self, frontend_dir, monkeypatch):
        monkeypatch.setenv("URL_BASE", "/trailarr")
        return TestClient(_build_app(frontend_dir))

    def test_api_reachable_below_the_url_base(self, client):
        # nginx `proxy_pass` keeps the prefix, so the app must strip it.
        assert client.post("/trailarr/api/v1/ping").status_code == 200

    def test_api_reachable_at_the_root_path(self, client):
        # A proxy that strips the prefix sends the request without it.
        assert client.post("/api/v1/ping").status_code == 200

    def test_index_below_the_url_base_uses_the_prefixed_base_href(self, client):
        response = client.get("/trailarr/")
        assert response.status_code == 200
        assert _base_href(response.text) == "/trailarr/"

    def test_index_at_the_root_path_uses_the_root_base_href(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert _base_href(response.text) == "/"

    def test_deep_link_below_the_url_base_serves_the_prefixed_index(self, client):
        response = client.get("/trailarr/settings/general")
        assert response.status_code == 200
        assert _base_href(response.text) == "/trailarr/"

    def test_asset_below_the_url_base_is_served(self, client):
        response = client.get("/trailarr/assets/style.css")
        assert response.status_code == 200
        assert response.text == "body{}"

    def test_forwarded_prefix_serves_the_prefixed_index(self, client):
        # The proxy stripped the prefix, and tells the app with a header.
        response = client.get("/", headers={"X-Forwarded-Prefix": "/trailarr"})
        assert response.status_code == 200
        assert _base_href(response.text) == "/trailarr/"


class TestUrlBaseChangedWhileRunning:
    """URL_BASE is set in the WebUI after the app started.

    The user gets a "405 Method Not Allowed" error for the login request when
    the app strips the prefix only for a URL base that was set at startup.
    """

    @pytest.fixture
    def client(self, frontend_dir, monkeypatch):
        monkeypatch.delenv("URL_BASE", raising=False)
        client = TestClient(_build_app(frontend_dir))
        monkeypatch.setenv("URL_BASE", "/trailarr")
        return client

    def test_api_reachable_below_the_new_url_base(self, client):
        response = client.post("/trailarr/api/v1/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}

    def test_index_uses_the_new_prefixed_base_href(self, client):
        response = client.get("/trailarr/")
        assert response.status_code == 200
        assert _base_href(response.text) == "/trailarr/"

    def test_api_at_the_root_path_still_works(self, client):
        assert client.post("/api/v1/ping").status_code == 200


class TestUvicornRootPath:
    """Docker starts the app with `uvicorn --root-path {url_base}`.

    uvicorn adds the root path to the request path. A reverse proxy that keeps
    the prefix — the nginx and Caddy examples in the documentation — then makes
    the app see the prefix two times, for example
    `/trailarr/trailarr/api/v1/auth/login`. The user got "405 Method Not
    Allowed" for the login request, because that path went to the frontend
    catch-all route instead of the API.
    """

    @pytest.fixture
    def client(self, frontend_dir, monkeypatch, default_credentials):
        monkeypatch.setenv("URL_BASE", "/trailarr")
        return TestClient(_build_app(frontend_dir), root_path="/trailarr")

    def test_api_reachable_when_the_proxy_keeps_the_prefix(self, client):
        response = client.post("/trailarr/trailarr/api/v1/ping")
        assert response.status_code == 200
        assert response.json() == {"ping": "pong"}

    def test_login_works_when_the_proxy_keeps_the_prefix(
        self, client, default_credentials
    ):
        username, password = default_credentials
        response = client.post(
            "/trailarr/trailarr/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200

    def test_api_reachable_when_the_proxy_strips_the_prefix(self, client):
        assert client.post("/trailarr/api/v1/ping").status_code == 200

    def test_health_check_reachable_below_the_url_base(self, client):
        response = client.get("/trailarr/trailarr/status")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_index_still_served_for_a_frontend_path(self, client):
        response = client.get("/trailarr/trailarr/settings/general")
        assert response.status_code == 200
        assert _base_href(response.text) == "/trailarr/"


class TestSessionCookieWithUrlBase:
    """The session cookie must work at every path of the app."""

    @pytest.fixture
    def client(self, frontend_dir, monkeypatch, default_credentials):
        monkeypatch.setenv("URL_BASE", "/trailarr")
        return TestClient(_build_app(frontend_dir))

    def test_login_cookie_is_not_scoped_to_the_url_base(
        self, client, default_credentials
    ):
        username, password = default_credentials
        response = client.post(
            "/trailarr/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        assert response.status_code == 200
        set_cookie = response.headers["set-cookie"]
        assert "Path=/;" in set_cookie or set_cookie.endswith("Path=/")
        assert "Path=/trailarr" not in set_cookie

    def test_session_works_at_the_root_path_after_login(
        self, client, default_credentials
    ):
        # The user opens the app at the root path — for example to remove a
        # wrong URL base. The session from the login must still work there.
        username, password = default_credentials
        client.post(
            "/trailarr/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        response = client.get("/api/v1/auth/status")
        assert response.status_code == 200
        assert response.json() == {"authenticated": True}

    def test_session_works_below_the_url_base_after_login(
        self, client, default_credentials
    ):
        username, password = default_credentials
        client.post(
            "/trailarr/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        response = client.get("/trailarr/api/v1/auth/status")
        assert response.status_code == 200
        assert response.json() == {"authenticated": True}

    def test_logout_removes_the_cookie_at_the_root_path(
        self, client, default_credentials
    ):
        username, password = default_credentials
        client.post(
            "/trailarr/api/v1/auth/login",
            json={"username": username, "password": password},
        )
        response = client.post("/trailarr/api/v1/auth/logout")
        assert response.status_code == 200
        assert 'trailarr_session=""' in response.headers["set-cookie"]
        assert "Path=/trailarr" not in response.headers["set-cookie"]
        assert client.get("/api/v1/auth/status").status_code == 401
