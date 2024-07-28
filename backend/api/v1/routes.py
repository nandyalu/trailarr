import os
from fastapi import APIRouter, Depends, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
)
from fastapi.responses import FileResponse, HTMLResponse

from api.v1.authentication import validate_api_key
from api.v1.connections import connections_router
from api.v1.movies import movies_router
from api.v1.search import search_router
from api.v1.series import series_router
from api.v1.settings import settings_router
from api.v1.logs import logs_router
from api.v1.tasks import tasks_router

from app_logger import ModuleLogger

logging = ModuleLogger("API Routes")

logging.info("Creating API v1 Routes")

# Create an authenticated router and add all API routes that need authenentication to it
authenticated_router = APIRouter(
    dependencies=[Depends(validate_api_key)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "description": "API key is missing",
        }
    },
)
authenticated_router.include_router(connections_router)
authenticated_router.include_router(movies_router)
authenticated_router.include_router(search_router)
authenticated_router.include_router(series_router)
authenticated_router.include_router(settings_router)
authenticated_router.include_router(logs_router)
authenticated_router.include_router(tasks_router)

# Now create API router and add the authenticated router to it
api_v1_router = APIRouter()
api_v1_router.include_router(authenticated_router)


# Mount Custom API Documentation
APP_NAME = os.getenv("APP_NAME", "Trailarr")
STATIC_PATH = "/api/v1/static"
OPENAPI_URL = "/api/v1/openapi.json"
REDOC_URL = "redoc"
SWAGGER_URL = "docs"

# Check if the static directory exists, if not create it
static_dir = os.path.abspath("/app/assets")
if not os.path.exists(static_dir):
    logging.info(
        "API Documentation folder does not exist! API Documentation will not be available."
    )
else:
    logging.info("Mounting API Documentation static directory")

    @api_v1_router.get("/static/{file_path:path}", include_in_schema=False)
    async def serve_static(file_path: str):
        # logging.info(f"Requested file: {file_path}")
        file_path = os.path.join(static_dir, file_path)
        if os.path.isfile(file_path):
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
