import os
from fastapi import APIRouter, Depends, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
)
from fastapi.responses import FileResponse, HTMLResponse

from api.v1.authentication import validate_api_key
from api.v1.connections import connections_router
from api.v1.customfilters import customfilters_router
from api.v1.files import files_router
from api.v1.media import media_router
from api.v1.settings import settings_router
from api.v1.logs import logs_router
from api.v1.tasks import tasks_router
from api.v1.trailerprofiles import trailerprofiles_router

from app_logger import ModuleLogger

logging = ModuleLogger("APIRoutes")

logging.info("Creating API v1 Routes")

# Create an authenticated router and add all API routes that
# need authenentication to it
authenticated_router = APIRouter(
    dependencies=[Depends(validate_api_key)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "API key is missing",
        }
    },
)
authenticated_router.include_router(connections_router)
authenticated_router.include_router(customfilters_router)
authenticated_router.include_router(files_router)
authenticated_router.include_router(media_router)
authenticated_router.include_router(settings_router)
authenticated_router.include_router(logs_router)
authenticated_router.include_router(tasks_router)
authenticated_router.include_router(trailerprofiles_router)

# Now create API router and add the authenticated router to it
api_v1_router = APIRouter()
api_v1_router.include_router(authenticated_router)


# Mount Custom API Documentation
APP_NAME = os.getenv("APP_NAME", "Trailarr")
URL_BASE = os.getenv("URL_BASE", "")
if URL_BASE and not URL_BASE.startswith("/"):
    URL_BASE = "/" + URL_BASE
if URL_BASE.endswith("/"):
    URL_BASE = URL_BASE[:-1]
STATIC_PATH = f"{URL_BASE}/api/v1/static"
OPENAPI_URL = f"{URL_BASE}/api/v1/openapi.json"
REDOC_URL = "redoc"
SWAGGER_URL = "docs"

# Check if the static directory exists, if not create it
static_dir = os.path.abspath("/opt/trailarr/assets")
if not os.path.exists(static_dir):
    static_dir = os.path.abspath("/app/assets")
if not os.path.exists(static_dir):
    logging.info(
        "API Documentation folder does not exist! API Documentation will not "
        "be available."
    )
else:
    logging.info("Mounting API Documentation static directory")

    @api_v1_router.get("/static/{file_path:path}", include_in_schema=False)
    async def serve_static(file_path: str):
        # logging.info(f"Requested file: {file_path}")
        file_path = os.path.normpath(os.path.join(static_dir, file_path))
        if file_path.startswith(static_dir) and os.path.isfile(file_path):
            # logging.info(f"Returning file: {file_path}")
            return FileResponse(file_path)
        # logging.info(f"File not found: {file_path}")
        return HTMLResponse(status_code=404)


# Add the API Documentation routes
@api_v1_router.get(f"/{SWAGGER_URL}", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=OPENAPI_URL,
        title=APP_NAME + " - Swagger UI",
        swagger_js_url=f"{STATIC_PATH}/openapi/swagger-ui-bundle.js",
        swagger_css_url=f"{STATIC_PATH}/openapi/swagger-dark-ui.css",
        swagger_favicon_url=f"{STATIC_PATH}/images/trailarr-64.png",
    )


@api_v1_router.get(f"/{REDOC_URL}", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=OPENAPI_URL,
        title=APP_NAME + " - ReDoc",
        redoc_js_url=f"{STATIC_PATH}/openapi/redoc.standalone.js",
        redoc_favicon_url=f"{STATIC_PATH}/images/trailarr-64.png",
    )
