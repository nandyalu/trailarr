from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
from urllib.parse import unquote
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config.logs.db_utils import flush_logs_to_db
from config.timing_middleware import setup_timing_middleware
from core.base.database.utils import init_db  # noqa: F401
from api.v1.authentication import validate_api_key_cookie, validate_login
from app_logger import ModuleLogger
from api.utils import format_google_docstring
from api.v1.routes import api_v1_router
from api.v1.websockets import ws_manager
from config.settings import app_settings
from core.base.database.utils.engine import flush_records_to_db
from core.tasks import scheduler
from core.tasks.schedules import schedule_all_tasks
from frontend.utils import update_base_href

logging = ModuleLogger("Main")
# from web.routes import web_router
# TODO: Move these to main() function later and setup docker to run main.py
# No need to setup the logger and it's config, importing the logger from \
#    app_logger.py will do setup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before startup
    # Schedule all tasks
    logging.debug("Scheduling tasks")
    schedule_all_tasks()
    scheduler.start()

    # Yield to let the app run
    yield

    # Before shutdown
    logging.debug("Shutting down the scheduler and flushing logs to DB")
    scheduler.shutdown()
    flush_records_to_db()
    flush_logs_to_db()
    logging.debug("Trailarr shutdown complete")


# Get APP_NAME and APP_VERSION from environment variables
APP_NAME = "Trailarr"
APP_VERSION = app_settings.version

# Initialize the database - No need to do this if we are using alembic
# logger.debug("Initializing the database")
# init_db()

# Create the FastAPI application
logging.info("Starting Trailarr application")
logging.debug("Creating the FastAPI application")
trailarr_api = FastAPI(
    lifespan=lifespan,
    # root_path=f"{app_settings.url_base}",
    openapi_url="/api/v1/openapi.json",
    docs_url=None,
    redoc_url=None,
)

trailarr_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

trailarr_api.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=7)
setup_timing_middleware(trailarr_api)

last_check_time = datetime.now(timezone.utc)


# Health check route
@trailarr_api.get("/status", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint.
    Runs 'nvidia-smi' to check for NVIDIA GPU availability (if hw accel enabled).
    Returns 'unhealthy' if the command fails.
    """
    try:
        # Run nvidia-smi to check for NVIDIA GPU presence once every hour
        global last_check_time
        current_time = datetime.now(timezone.utc)
        if (
            current_time - last_check_time > timedelta(hours=1)
            and app_settings.gpu_available_nvidia
            and app_settings.gpu_enabled_nvidia
        ):
            last_check_time = current_time
            logging.debug("Checking NVIDIA GPU availability")
            # Check if nvidia-smi is available
            if not shutil.which("nvidia-smi"):
                raise EnvironmentError("nvidia-smi command not found")
        return {"status": "healthy"}
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        raise HTTPException(404, detail=f"unhealthy. Error: {e}")


# Register API routes
trailarr_api.include_router(api_v1_router, prefix="/api/v1")


def custom_openapi():
    if trailarr_api.openapi_schema:
        return trailarr_api.openapi_schema

    openapi_schema = get_openapi(
        title=f"{APP_NAME} API",
        description=f"API for {APP_NAME} application.",
        summary=f"{APP_NAME} API available commands.",
        version=APP_VERSION,
        openapi_version=trailarr_api.openapi_version,
        routes=trailarr_api.routes,
        terms_of_service="https://github.com/nandyalu/trailarr",
        contact={
            "name": "Trailarr - Github",
            "url": "https://github.com/nandyalu/trailarr",
        },
        license_info={
            "name": "GNU GPL 3.0",
            "url": "https://github.com/nandyalu/trailarr/blob/main/LICENSE",
        },
        servers=[
            {
                # Use current page host as default
                "url": f"{app_settings.url_base}/",
                "description": "Current host",
            },
            {
                "url": "{protocol}://{hostpath}",
                "variables": {
                    "protocol": {"default": "http", "enum": ["http", "https"]},
                    "hostpath": {"default": "127.0.0.1:7889"},
                },
            },
        ],
    )

    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "description" in method:
                # trailarr_apily the enhanced formatter
                method["description"] = format_google_docstring(
                    method["description"]
                )

    trailarr_api.openapi_schema = openapi_schema
    return trailarr_api.openapi_schema


# Assign the custom OpenAPI function to the FastAPI app for generating formatted docs
trailarr_api.openapi = custom_openapi


# Websockets
@trailarr_api.websocket(
    "/ws/{client_id}",
    dependencies=[Depends(validate_api_key_cookie)],
)
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await ws_manager.connect(websocket)
    logging.debug(f"Client #{client_id} connected!")
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_personal_message(
                f"You wrote: {data}", websocket
            )
            await ws_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logging.debug(f"Client #{client_id} disconnected!")
        # await ws_manager.broadcast(f"Client #{client_id} disconnected!")


# Register other routes here (if any)

# Mount images folders - Load these before mounting frontend
images_dir = Path(app_settings.app_data_dir, "web", "images")
if not images_dir.exists():
    logging.warning(
        f"Images directory not found at '{images_dir}'. Creating images"
        " directory"
    )
    images_dir.mkdir(parents=True, exist_ok=True)
else:
    logging.debug("Mounting images directory for frontend!")
images_mount_path = images_dir.as_posix()
logging.debug(
    f"Mounting images directory '{images_dir}' at '{images_mount_path}'"
)
trailarr_api.mount(
    images_mount_path, StaticFiles(directory=images_dir), name="images"
)

# Get frontend dir path as frontend-build/browser in this file's parent dirs
frontend_dir = (
    Path(__file__).resolve().parents[1] / "frontend-build" / "browser"
)
if not frontend_dir.exists():
    logging.warning(
        f"Frontend directory not found at '{frontend_dir}', using fallback."
    )
    frontend_dir = Path("/app/frontend-build/browser")
frontend_dir = frontend_dir.resolve()
logging.debug(f"Using frontend directory: {frontend_dir}")


# Mount Frontend 'assets/manifest.json' without authorization
@trailarr_api.get("/assets/manifest.json", include_in_schema=False)
async def serve_manifest():
    file_path = Path(frontend_dir, "assets", "manifest.json").resolve()
    if file_path.is_file():
        # If the path corresponds to a static file, return the file
        return FileResponse(file_path)
    else:
        return HTMLResponse(status_code=404)


index_html_path = Path(frontend_dir, "index.html").resolve()
if not index_html_path.is_file():
    logging.warning(
        f"index.html not found at '{index_html_path}'. Frontend may not work."
    )
update_base_href(index_html_path, app_settings.url_base)


def get_sanitized_path(messy_path: str) -> Path | None:
    """Sanitize a file path to ensure it is within the base directory."""
    resolved_base_dir = frontend_dir.resolve()
    # Decode URL-encoded characters
    messy_path = unquote(messy_path)
    # Normalize input: ensure a relative path and reject empty/whitespace-only values
    if not messy_path or not messy_path.strip():
        return None

    # Remove leading slashes to prevent absolute path issues
    clean_path = messy_path.lstrip("/")
    try:
        file_path = (resolved_base_dir / clean_path).resolve()
    except (OSError, RuntimeError):
        # Any resolution error results in rejecting the path
        return None

    # Check if the path is within the static directory
    if not file_path.is_relative_to(resolved_base_dir):
        return None
    return file_path


def serve_index_html_with_cookie():
    response = FileResponse(index_html_path)
    response.set_cookie(
        key="trailarr_api_key",
        value=app_settings.api_key,
        path=app_settings.url_base or "/",
        samesite="lax",
        httponly=True,  # Frontend JS needs access
    )
    return response


# Mount static frontend files to serve frontend
# Mount these at the end so that it won't interfere with other routes
@trailarr_api.get(
    "/{rest_of_path:path}",
    include_in_schema=False,
    dependencies=[Depends(validate_login)],
)
async def serve_frontend(rest_of_path: str = ""):
    if rest_of_path.startswith("api"):
        # If the path starts with "api", it's an API request and not \
        # meant for the frontend
        return HTMLResponse(status_code=404)
    else:
        # Otherwise, it's a frontend request and should be handled by Angular
        if rest_of_path == "":
            # If no specific path is provided, serve index.html
            return serve_index_html_with_cookie()
        # Sanitize the rest_of_path to prevent directory traversal attacks
        file_path = get_sanitized_path(rest_of_path)
        if file_path is None:
            return HTMLResponse(status_code=404)
        if file_path.is_file():
            # If the path corresponds to a static file, return the file
            return FileResponse(file_path)
        return serve_index_html_with_cookie()
