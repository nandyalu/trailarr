from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.app_logger import logger
from backend.api.v1.routes import api_v1_router
from backend.web.routes import web_router

# TODO: Move these to main() function later and setup docker to run main.py
# No need to setup the logger and it's config, importing the logger from logger.py will do setup.

# Initialize the database - No need to do this if we are using alembic
# logger.debug("Initializing the database")
# init_db()
# Create the FastAPI application
logger.info("Creating the FastAPI application")
trailarr_api = FastAPI()

# Mount static files
trailarr_api.mount("/static", StaticFiles(directory="static"), name="static")

# Register API routes
trailarr_api.include_router(api_v1_router, prefix="/api/v1")

# Register Web routes
trailarr_api.include_router(web_router)


@trailarr_api.get("/")
def read_root():
    return {"Hello": "World"}


@trailarr_api.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    # Call some function to get the data
    # data = await some_function(item_id, q)
    return {"item_id": item_id, "q": q}
