from starlette.types import ASGIApp, Receive, Scope, Send

from config.settings import app_settings

# Routes handled server-side — strip the URL_BASE prefix for these so local
# access works without a reverse proxy doing the stripping.
_SERVER_PREFIXES = ("/api/", "/ws/", "/status", "/images/")


class URLBasePrefixMiddleware:
    """
    Strips the URL_BASE prefix from server-side request paths so the app is
    reachable locally at both / and /{url_base}/ without a reverse proxy.

    Only strips for known server-side paths (API, WebSocket, health, images).
    SPA/asset paths are left intact so the catch-all route can serve the
    correct index.html (patched vs root) based on the prefix.

    The prefix can also occur more than once. The app starts with
    `uvicorn --root-path {url_base}`, and uvicorn adds the root path to the
    request path. A reverse proxy that keeps the prefix then sends, for example,
    `/trailarr/trailarr/api/v1/...`. The middleware removes every copy of the prefix.

    The URL base is read for each request. The user can change the setting
    while the app runs, and the new value applies without a restart.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] in ("http", "websocket"):
            prefix = app_settings.url_base.rstrip("/")  # e.g. "/trailarr"
            path: str = scope.get("path", "")
            remainder = path
            while prefix and remainder.startswith(prefix + "/"):
                remainder = remainder[len(prefix):]  # e.g. "/api/v1/..."
            if remainder != path and any(
                remainder.startswith(p) for p in _SERVER_PREFIXES
            ):
                scope = dict(scope)
                scope["path"] = remainder
                scope["raw_path"] = remainder.encode("latin-1")
        await self.app(scope, receive, send)
