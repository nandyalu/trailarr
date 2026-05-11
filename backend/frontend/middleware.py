from starlette.types import ASGIApp, Receive, Scope, Send

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
    """

    def __init__(self, app: ASGIApp, url_base: str) -> None:
        self.app = app
        self.prefix = url_base.rstrip("/")         # e.g. "/trailarr"
        self.prefix_slash = self.prefix + "/"      # e.g. "/trailarr/"

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.prefix and scope["type"] in ("http", "websocket"):
            path: str = scope.get("path", "")
            if path == self.prefix or path.startswith(self.prefix_slash):
                remainder = path[len(self.prefix):]  # e.g. "/api/v1/..."
                if any(remainder.startswith(p) for p in _SERVER_PREFIXES):
                    scope = dict(scope)
                    scope["path"] = remainder
                    scope["raw_path"] = remainder.encode("latin-1")
        await self.app(scope, receive, send)
