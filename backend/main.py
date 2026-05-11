from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
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
from fastapi.openapi.utils import get_openapi

from config.logs.db_utils import flush_logs_to_db
from config.timing_middleware import setup_timing_middleware
from core.base.database.utils import init_db  # noqa: F401
from api.v1.authentication import validate_api_key_cookie
from app_logger import ModuleLogger
from api.utils import format_google_docstring
from api.v1.routes import api_v1_router
from api.v1.websockets import ws_manager
from config.settings import app_settings
from core.base.database.utils.engine import flush_records_to_db
from core.tasks import scheduler
from core.tasks.schedules import schedule_all_tasks
from frontend import setup_frontend

logging = ModuleLogger("Main")


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

# Set up frontend serving — must come after all API routes so the SPA
# catch-all does not shadow any API endpoints.
setup_frontend(trailarr_api)
