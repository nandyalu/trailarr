from fastapi import APIRouter
from api.v1.connections import connections_router
from api.v1.movies import movies_router
from api.v1.series import series_router

api_v1_router = APIRouter()
api_v1_router.include_router(connections_router)
api_v1_router.include_router(movies_router)
api_v1_router.include_router(series_router)


@api_v1_router.get("/your_endpoint")
async def your_function():
    # Your function implementation
    return {"Hello": "From Endpoint!"}
