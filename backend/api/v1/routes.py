import os

from fastapi import APIRouter, Depends, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import FileResponse, HTMLResponse

from api.v1.deps import validate_api_key
from api.v1.endpoints.auth import auth_router
from api.v1.endpoints.connections import connections_router
from api.v1.endpoints.custom_filters import customfilters_router
from api.v1.endpoints.events import events_router
from api.v1.endpoints.files import files_router
from api.v1.endpoints.issues import issues_router
from api.v1.endpoints.logs import logs_router
from api.v1.endpoints.media import media_router
from api.v1.endpoints.settings import settings_router
from api.v1.endpoints.tasks import tasks_router
from api.v1.endpoints.trailer_profiles import trailerprofiles_router
from app_logger import ModuleLogger

logging = ModuleLogger("APIRoutes")
logging.info("Creating API v1 Routes")

authenticated_router = APIRouter(
    dependencies=[Depends(validate_api_key)],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "API key is missing"},
    },
)
authenticated_router.include_router(connections_router)
authenticated_router.include_router(customfilters_router)
authenticated_router.include_router(events_router)
authenticated_router.include_router(files_router)
authenticated_router.include_router(issues_router)
authenticated_router.include_router(logs_router)
authenticated_router.include_router(media_router)
authenticated_router.include_router(settings_router)
authenticated_router.include_router(tasks_router)
authenticated_router.include_router(trailerprofiles_router)

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)  # public — no API key required
api_v1_router.include_router(authenticated_router)

# Custom API documentation
APP_NAME = os.getenv("APP_NAME", "Trailarr")
URL_BASE = os.getenv("URL_BASE", "")
if URL_BASE and not URL_BASE.startswith("/"):
    URL_BASE = "/" + URL_BASE
if URL_BASE.endswith("/"):
    URL_BASE = URL_BASE[:-1]
STATIC_PATH = f"{URL_BASE}/api/v1/static"
OPENAPI_URL = f"{URL_BASE}/api/v1/openapi.json"

static_dir = os.path.abspath("/opt/trailarr/assets")
if not os.path.exists(static_dir):
    static_dir = os.path.abspath("/app/assets")
if not os.path.exists(static_dir):
    logging.info("API Documentation folder does not exist! API Documentation will not be available.")
else:
    logging.info("Mounting API Documentation static directory")

    @api_v1_router.get("/static/{file_path:path}", include_in_schema=False)
    async def serve_static(file_path: str):
        file_path = os.path.normpath(os.path.join(static_dir, file_path))
        if file_path.startswith(static_dir) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return HTMLResponse(status_code=404)


@api_v1_router.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=OPENAPI_URL,
        title=APP_NAME + " - Swagger UI",
        swagger_js_url=f"{STATIC_PATH}/openapi/swagger-ui-bundle.js",
        swagger_css_url=f"{STATIC_PATH}/openapi/swagger-dark-ui.css",
        swagger_favicon_url=f"{STATIC_PATH}/images/trailarr-64.png",
    )


@api_v1_router.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=OPENAPI_URL,
        title=APP_NAME + " - ReDoc",
        redoc_js_url=f"{STATIC_PATH}/openapi/redoc.standalone.js",
        redoc_favicon_url=f"{STATIC_PATH}/images/trailarr-64.png",
    )
