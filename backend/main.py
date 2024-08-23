from contextlib import asynccontextmanager
import os
from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from api.v1.authentication import validate_api_key_cookie
from app_logger import ModuleLogger
from api.v1.routes import api_v1_router
from api.v1.websockets import ws_manager
from config.settings import app_settings
from core.tasks import scheduler
from core.tasks.schedules import schedule_all_tasks

logging = ModuleLogger("Main")
# from web.routes import web_router
# TODO! Remove sensitive information from historic commits
# TODO: Move these to main() function later and setup docker to run main.py
# No need to setup the logger and it's config, importing the logger from app_logger.py will do setup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Before startup
    # Schedule all tasks
    logging.info("Scheduling tasks")
    schedule_all_tasks()
    scheduler.start()

    # Yield to let the app run
    yield

    # Before shutdown
    scheduler.shutdown()


# Get APP_NAME and APP_VERSION from environment variables
APP_NAME = os.getenv("APP_NAME", "Trailarr")
APP_VERSION = os.getenv("APP_VERSION", "0.0.1")

# Initialize the database - No need to do this if we are using alembic
# logger.debug("Initializing the database")
# init_db()
# Create the FastAPI application
logging.info("Creating the FastAPI application")
trailarr_api = FastAPI(
    lifespan=lifespan,
    title=f"{APP_NAME} API",
    description=f"API for {APP_NAME} application.",
    summary=f"{APP_NAME} API available commands.",
    version=APP_VERSION,
    openapi_url="/api/v1/openapi.json",
    docs_url=None,
    redoc_url=None,
    terms_of_service="https://github.com/nandyalu/trailarr",
    contact={
        "url": "https://github.com/nandyalu/trailarr",
    },
    license_info={
        "name": "GNU GPL 3.0",
        "url": "https://github.com/nandyalu/trailarr/blob/main/LICENSE",
    },
)

trailarr_api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check route
@trailarr_api.get("/status", tags=["Health Check"])
async def health_check():
    return {"status": "healthy"}


# Register API routes
trailarr_api.include_router(api_v1_router, prefix="/api/v1")


# Websockets
@trailarr_api.websocket(
    "/ws/{client_id}",
    dependencies=[Depends(validate_api_key_cookie)],
)
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await ws_manager.connect(websocket)
    logging.info(f"Client #{client_id} connected!")
    try:
        while True:
            data = await websocket.receive_text()
            await ws_manager.send_personal_message(f"You wrote: {data}", websocket)
            await ws_manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logging.info(f"Client #{client_id} disconnected!")
        # await ws_manager.broadcast(f"Client #{client_id} disconnected!")


# Register other routes here (if any)

# Mount images folders - Load these before mountic frontend
images_dir = os.path.join(app_settings.app_data_dir, "web", "images")
if not os.path.exists(images_dir):
    logging.info("Creating images directory")
    os.makedirs(images_dir)
    trailarr_api.mount(images_dir, StaticFiles(directory=images_dir), name="images")
else:
    logging.info("Mounting images directory for frontend!")
    trailarr_api.mount(images_dir, StaticFiles(directory=images_dir), name="images")


# Mount static frontend files to serve frontend
# Mount these at the end so that it won't interfere with other routes
@trailarr_api.get("/{rest_of_path:path}", include_in_schema=False)
async def serve_frontend(rest_of_path: str = ""):
    if rest_of_path.startswith("api"):
        # If the path starts with "api", it's an API request and not meant for the frontend
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
            # If the path corresponds to a directory, return the index.html file in the directory
            # headers = {"X-API-KEY": app_settings.api_key}
            headers = {
                "Set-Cookie": f"trailarr_api_key={app_settings.api_key}; SameSite=Strict; Path=/"
            }
            return HTMLResponse(
                content=open(f"{static_dir}/index.html").read(), headers=headers
            )


# Check if the frontend directory exists, if not create it
static_dir = os.path.abspath("/app/frontend-build/browser")
if not os.path.exists(static_dir):
    logging.info("Creating static directory")
    os.makedirs(static_dir)
else:
    logging.info("Mounting frontend directory for frontend files!")
    trailarr_api.mount("/", StaticFiles(directory=static_dir), name="frontend")
