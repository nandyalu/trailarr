from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import os
import shutil
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from config.logs.db_utils import flush_logs_to_db
from config.timing_middleware import setup_timing_middleware
from core.base.database.utils import init_db  # noqa: F401
from api.v1.authentication import validate_api_key_cookie, validate_api_key
from app_logger import ModuleLogger
from api.v1.routes import api_v1_router
from api.v1.websockets import ws_manager
from config.settings import app_settings
from core.base.database.utils.engine import flush_records_to_db
from core.tasks import scheduler
from core.tasks.schedules import schedule_all_tasks

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
APP_NAME = os.getenv("APP_NAME", "Trailarr")
APP_VERSION = os.getenv("APP_VERSION", "0.0.1")

# Initialize the database - No need to do this if we are using alembic
# logger.debug("Initializing the database")
# init_db()
# Create the FastAPI application
logging.info("Starting Trailarr application")
logging.debug("Creating the FastAPI application")
trailarr_api = FastAPI(
    lifespan=lifespan,
    title=f"{APP_NAME} API",
    description=f"API for {APP_NAME} application.",
    summary=f"{APP_NAME} API available commands.",
    version=APP_VERSION,
    root_path=f"{app_settings.url_base}",
    openapi_url="/api/v1/openapi.json",
    docs_url=None,
    redoc_url=None,
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
            "url": "{protocol}://{hostpath}",
            "variables": {
                "protocol": {"default": "http", "enum": ["http", "https"]},
                "hostpath": {"default": "127.0.0.1:7889"},
            },
        }
    ],
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

# Mount images folders - Load these before mountic frontend
images_dir = os.path.join(app_settings.app_data_dir, "web", "images")
if not os.path.exists(images_dir):
    logging.debug("Creating images directory")
    os.makedirs(images_dir)
    trailarr_api.mount(
        images_dir, StaticFiles(directory=images_dir), name="images"
    )
else:
    logging.debug("Mounting images directory for frontend!")
    trailarr_api.mount(
        images_dir, StaticFiles(directory=images_dir), name="images"
    )


# Mount Frontend 'assets/manifest.json' without authorization
@trailarr_api.get("/assets/manifest.json", include_in_schema=False)
async def serve_manifest():
    file_path = os.path.normpath(
        os.path.join(static_dir, "assets", "manifest.json")
    )
    if os.path.isfile(file_path):
        # If the path corresponds to a static file, return the file
        return FileResponse(file_path)
    else:
        return HTMLResponse(status_code=404)


# Mount static frontend files to serve frontend
# Mount these at the end so that it won't interfere with other routes
login_enabled = os.getenv("WEBUI_DISABLE_AUTH", "false").lower() != "true"
if login_enabled:
    # Authentication is enabled
    @trailarr_api.get(
        "/{rest_of_path:path}",
        include_in_schema=False,
        dependencies=[Depends(validate_api_key)],
    )
    async def serve_frontend(rest_of_path: str = ""):
        return await get_frontend(rest_of_path)

else:
    # Authentication is disabled - Serve frontend without authentication
    logging.info(
        "WebUI Authentication is disabled - Frontend will be served without"
        " authentication"
    )

    @trailarr_api.get("/{rest_of_path:path}", include_in_schema=False)
    async def serve_frontend2(rest_of_path: str = ""):
        return await get_frontend(rest_of_path)


async def get_frontend(rest_of_path: str = ""):
    if rest_of_path.startswith("api"):
        # If the path starts with "api", it's an API request and not \
        # meant for the frontend
        return HTMLResponse(status_code=404)
    else:
        # Otherwise, it's a frontend request and should be handled by Angular
        file_path = os.path.normpath(os.path.join(static_dir, rest_of_path))
        # Check if the path is within the static directory
        if not file_path.startswith(static_dir):
            return HTMLResponse(status_code=404)
        if os.path.isfile(file_path):
            # If the path corresponds to a static file, return the file
            return FileResponse(file_path)
        else:
            # If the path corresponds to a directory, return the \
            # index.html file in the directory
            # headers = {"X-API-KEY": app_settings.api_key}
            headers = {
                "Set-Cookie": (
                    f"trailarr_api_key={app_settings.api_key};"
                    " SameSite=Strict; Path=/"
                )
            }
            return HTMLResponse(
                content=open(f"{static_dir}/index.html").read(),
                headers=headers,
            )


# Check if the frontend directory exists, if not create it
# Support both Docker (/app) and bare metal (/opt/trailarr) paths
static_dirs = [
    "/opt/trailarr/frontend-build/browser",  # Bare metal
    "/app/frontend-build/browser",  # Docker
]

static_dir = None
for dir_path in static_dirs:
    if os.path.exists(dir_path):
        static_dir = os.path.abspath(dir_path)
        break

if static_dir is None:
    # Fallback to first option and create it
    static_dir = os.path.abspath(static_dirs[0])
    logging.debug(f"Creating static directory: {static_dir}")
    os.makedirs(static_dir, exist_ok=True)
else:
    logging.debug(f"Using frontend directory: {static_dir}")
    trailarr_api.mount("/", StaticFiles(directory=static_dir), name="frontend")
