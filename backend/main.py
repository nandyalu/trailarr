from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
import shutil

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi

from app_logger import ModuleLogger
from api.v1.routes import api_v1_router
from api.v1.ws_endpoint import ws_router
from config.logs.db_utils import flush_logs_to_db
from config.settings import app_settings
from config.timing_middleware import setup_timing_middleware
from db.engine import flush_records_to_db
from db.init_db import init_db
from frontend import setup_frontend
from tasks.scheduler import scheduler
from tasks.schedules import schedule_all_tasks

logging = ModuleLogger("Main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting Trailarr application")
    init_db()
    schedule_all_tasks()
    scheduler.start()
    yield
    scheduler.shutdown()
    flush_records_to_db()
    flush_logs_to_db()
    logging.info("Trailarr application shutdown complete")


APP_NAME = "Trailarr"
APP_VERSION = app_settings.version

logging.info("Creating Trailarr application")
trailarr_api = FastAPI(
    lifespan=lifespan,
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


@trailarr_api.get("/status", tags=["Health Check"])
async def health_check():
    """Health check endpoint."""
    try:
        global last_check_time
        current_time = datetime.now(timezone.utc)
        if (
            current_time - last_check_time > timedelta(hours=1)
            and app_settings.gpu_available_nvidia
            and app_settings.gpu_enabled_nvidia
        ):
            last_check_time = current_time
            if not shutil.which("nvidia-smi"):
                raise EnvironmentError("nvidia-smi command not found")
        return {"status": "healthy"}
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        raise HTTPException(404, detail=f"unhealthy. Error: {e}")


# API routes
trailarr_api.include_router(api_v1_router, prefix="/api/v1")
# WebSocket at /ws/{client_id} — top-level, not nested under /api/v1
trailarr_api.include_router(ws_router)


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
    trailarr_api.openapi_schema = openapi_schema
    return trailarr_api.openapi_schema


trailarr_api.openapi = custom_openapi

# Frontend serving — must come after all API routes so the SPA catch-all
# does not shadow any API endpoints.
setup_frontend(trailarr_api)
