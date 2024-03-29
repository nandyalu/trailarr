import atexit
import json
import logging
import logging.config
import pathlib
from fastapi import FastAPI


logger = logging.getLogger("trailarr")  # __name__ is a common choice


def setup_logging():
    config_file = pathlib.Path("configs/backend_logger.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()  # type: ignore
        atexit.register(queue_handler.listener.stop)  # type: ignore


# TODO: Move these to main() function later and setup docker to run main.py
# Setup the logging
setup_logging()
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
