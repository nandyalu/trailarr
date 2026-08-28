from pathlib import Path
from urllib.parse import unquote

from fastapi import APIRouter, FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request
from starlette.responses import Response

from app_logger import ModuleLogger
from config.settings import app_settings
from frontend.middleware import URLBasePrefixMiddleware
from frontend.utils import setup_url_base_folder, update_base_href

logging = ModuleLogger("Frontend")


def _resolve_frontend_dir() -> Path:
    candidate = Path(__file__).resolve().parents[2] / "frontend-build" / "browser"
    if not candidate.exists():
        logging.warning(f"Frontend dir not found at '{candidate}', using fallback.")
        candidate = Path("/app/frontend-build/browser")
    return candidate.resolve()


# Cache of the index.html created for each URL base, to keep the catch-all
# route off the disk on every request.
_sub_index_cache: dict[str, Path] = {}


def _url_base_name() -> str:
    """Return the current URL base as a folder name, e.g. 'trailarr'."""
    return app_settings.url_base.strip("/")


def _ensure_sub_index(frontend_dir: Path, url_base_name: str) -> Path:
    """Return the index.html for the given URL base, and create it if missing."""
    cached = _sub_index_cache.get(url_base_name)
    if cached is not None and cached.is_file():
        return cached
    subfolder = setup_url_base_folder(frontend_dir, url_base_name)
    sub_index = subfolder / "index.html"
    _sub_index_cache[url_base_name] = sub_index
    logging.debug(f"URL_BASE folder ready at '{subfolder}'")
    return sub_index


def _sanitize_path(base_dir: Path, messy_path: str) -> Path | None:
    """Return a resolved path only if it is safely inside base_dir."""
    if not messy_path or not messy_path.strip():
        return None
    clean = unquote(messy_path).lstrip("/")
    try:
        resolved = (base_dir / clean).resolve()
    except (OSError, RuntimeError):
        return None
    if not resolved.is_relative_to(base_dir):
        return None
    return resolved


def setup_frontend(app: FastAPI) -> None:
    """
    Configure all frontend serving:
      - Resets root index.html to <base href="/">
      - Creates /{url_base}/ subfolder with patched index.html when URL_BASE is set
      - Adds URLBasePrefixMiddleware for local access without a reverse proxy
      - Mounts the /images directory
      - Registers the manifest and SPA catch-all routes

    Must be called after all API routes are registered so the catch-all
    does not shadow any API endpoints.
    """
    frontend_dir = _resolve_frontend_dir()

    # Always ensure root index.html has <base href="/"> so local / access works.
    root_index = frontend_dir / "index.html"
    if root_index.is_file():
        update_base_href(root_index, "/")

    # Register the middleware always. The user can change the URL base while
    # the app runs. The middleware reads the setting for each request, so the
    # API stays reachable at /{url_base}/api/... without an app restart.
    _sub_index_cache.clear()
    app.add_middleware(URLBasePrefixMiddleware)
    logging.debug("URLBasePrefixMiddleware registered")

    # When URL_BASE is set, create the subfolder with the prefixed index.html.
    url_base_name = _url_base_name()     # e.g. "trailarr" or ""
    if url_base_name:
        _ensure_sub_index(frontend_dir, url_base_name)

    # Mount /images — must come before the catch-all route.
    images_dir = Path(app_settings.app_data_dir, "web", "images")
    images_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/images", StaticFiles(directory=images_dir), name="images")
    logging.debug(f"Mounted /images from '{images_dir}'")

    # Build and include the frontend router.
    router = _build_router(frontend_dir, root_index)
    app.include_router(router)
    logging.debug("Frontend router registered")


def _build_router(frontend_dir: Path, root_index: Path) -> APIRouter:
    router = APIRouter(include_in_schema=False)

    @router.get("/assets/manifest.json", response_model=None)
    async def serve_manifest() -> Response:
        file_path = (frontend_dir / "assets" / "manifest.json").resolve()
        if file_path.is_file():
            return FileResponse(file_path)
        return HTMLResponse(status_code=404)

    @router.get("/{rest_of_path:path}", response_model=None)
    async def serve_frontend(
        request: Request, rest_of_path: str = ""
    ) -> Response:
        # Read the URL base for each request — the user can change the setting
        # while the app runs.
        url_base_name = _url_base_name()

        # ── Local access at /{url_base}/* ────────────────────────────────────
        # The browser loaded the app at http://localhost:7889/{url_base}/ and
        # Angular resolves assets/routes relative to <base href="/{url_base}/">.
        if url_base_name and (
            rest_of_path == url_base_name
            or rest_of_path.startswith(url_base_name + "/")
        ):
            sub_index = _ensure_sub_index(frontend_dir, url_base_name)
            sub_path = rest_of_path[len(url_base_name):].lstrip("/")
            if not sub_path:
                return FileResponse(sub_index)
            # Assets live in frontend_dir; sub_path is safe to resolve there.
            file_path = _sanitize_path(frontend_dir, sub_path)
            if file_path and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(sub_index)

        # ── Reverse-proxy access (proxy strips prefix, sends X-Forwarded-Prefix) ──
        # The proxy already stripped /{url_base} so rest_of_path has no prefix,
        # but X-Forwarded-Prefix tells us which index.html the browser expects.
        if url_base_name:
            fwd_prefix = request.headers.get("X-Forwarded-Prefix", "").strip("/")
            if fwd_prefix == url_base_name:
                sub_index = _ensure_sub_index(frontend_dir, url_base_name)
                if not rest_of_path:
                    return FileResponse(sub_index)
                file_path = _sanitize_path(frontend_dir, rest_of_path)
                if file_path and file_path.is_file():
                    return FileResponse(file_path)
                return FileResponse(sub_index)

        # ── Normal root access at / ───────────────────────────────────────────
        if rest_of_path.startswith("api"):
            return HTMLResponse(status_code=404)
        if not rest_of_path:
            return FileResponse(root_index)
        file_path = _sanitize_path(frontend_dir, rest_of_path)
        if file_path is None:
            return HTMLResponse(status_code=404)
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(root_index)

    return router
