from contextlib import asynccontextmanager
import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app_logger import ModuleLogger
from api.v1.routes import api_v1_router
from core.tasks import scheduler
from core.tasks.schedules import schedule_all_tasks

logging = ModuleLogger("Main")
# from web.routes import web_router

# TODO: Move these to main() function later and setup docker to run main.py
# No need to setup the logger and it's config, importing the logger from app_logger.py will do setup

# Get the timezone from the environment variable
timezone = os.getenv("TZ", "ETC")

# Set the timezone
logging.info(f"Setting up timezone for the application as '{timezone}'")
os.environ["TZ"] = timezone
time.tzset()


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
APP_NAME = os.getenv("APP_NAME", "Indexarr")
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
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    terms_of_service="https://github.com/UNCode101/trailarr2",
    contact={
        "url": "https://github.com/UNCode101/trailarr2",
    },
    license_info={
        "name": "GNU GPL 3.0",
        "url": "https://github.com/UNCode101/trailarr2/blob/main/LICENSE",
    },
)

origins = [
    # "http://localhost",
    # "http://localhost:4200",  # Angular app
    # "http://10.0.10.131:7889",  # FastAPI app
    "*"  # TODO: Change this before deploying, Allow all origins for testing
]

trailarr_api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
trailarr_api.include_router(api_v1_router, prefix="/api/v1")

# Register Web routes
# trailarr_api.include_router(web_router)

# Mount images folders - Load these before mountic frontend
images_dir = os.path.abspath("/data/web/images")
if not os.path.exists(images_dir):
    logging.info("Creating images directory")
    os.makedirs(images_dir)
    trailarr_api.mount(
        "/data/web/images", StaticFiles(directory=images_dir), name="images"
    )
else:
    logging.info(f"Static directory exists at '{images_dir}'")
    trailarr_api.mount(
        "/data/web/images", StaticFiles(directory=images_dir), name="images"
    )


# Mount static files
# Mount these at the end so that it won't interfere with other routes
# @trailarr_api.get("/", include_in_schema=False)
# @trailarr_api.get("/home", include_in_schema=False)
# @trailarr_api.get("/movies", include_in_schema=False)
# @trailarr_api.get("/series", include_in_schema=False)
# @trailarr_api.get("/tasks", include_in_schema=False)
# @trailarr_api.get("/logs", include_in_schema=False)
# @trailarr_api.get("/settings", include_in_schema=False)
# async def root():
#     return RedirectResponse(url="/index.html")


@trailarr_api.get("/{rest_of_path:path}", include_in_schema=False)
async def serve_frontend(rest_of_path: str = ""):
    if rest_of_path.startswith("api"):
        # If the path starts with "api", it's an API request and not meant for the frontend
        return HTMLResponse(status_code=404)
    else:
        # Otherwise, it's a frontend request and should be handled by Angular
        file_path = os.path.join(static_dir, rest_of_path)
        if os.path.isfile(file_path):
            # If the path corresponds to a static file, return the file
            return FileResponse(file_path)
        else:
            # If the path corresponds to a directory, return the index.html file in the directory
            return HTMLResponse(content=open(f"{static_dir}/index.html").read())


static_dir = os.path.abspath("/app/frontend/dist/frontend/browser")
if not os.path.exists(static_dir):
    logging.info("Creating static directory")
    os.makedirs(static_dir)
else:
    logging.info(f"Static directory exists at '{static_dir}'")
    trailarr_api.mount("/", StaticFiles(directory=static_dir), name="frontend")
