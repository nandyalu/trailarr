from fastapi import APIRouter

api_v1_router = APIRouter()


@api_v1_router.get("/your_endpoint")
async def your_function():
    # Your function implementation
    pass
