from fastapi import FastAPI

from backend.logger import logger


# TODO: Move these to main() function later and setup docker to run main.py
# No need to setup the logger and it's config, importing the logger from logger.py will do setup.

# Initialize the database - No need to do this if we are using alembic
# logger.debug("Initializing the database")
# init_db()
# Create the FastAPI application
logger.debug("Creating the FastAPI application")
trailarr_api = FastAPI()


@trailarr_api.get("/")
def read_root():
    return {"Hello": "World"}


@trailarr_api.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    # Call some function to get the data
    # data = await some_function(item_id, q)
    return {"item_id": item_id, "q": q}
