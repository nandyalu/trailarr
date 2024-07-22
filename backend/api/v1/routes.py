from fastapi import APIRouter
from api.v1.connections import connections_router
from api.v1.movies import movies_router
from api.v1.search import search_router
from api.v1.series import series_router
from api.v1.settings import settings_router
from api.v1.logs import logs_router
from api.v1.tasks import tasks_router

api_v1_router = APIRouter()
api_v1_router.include_router(connections_router)
api_v1_router.include_router(movies_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(series_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(logs_router)
api_v1_router.include_router(tasks_router)
