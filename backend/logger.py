import atexit
import json
import logging
import logging.config
import pathlib

_is_logging_setup = False


def config_logging():
    """Setup the logging configuration using the config file.
    This will setup the root logger configuration and start the queue handler listener.
    """
    config_file = pathlib.Path("configs/backend_logger.json")
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()  # type: ignore
        atexit.register(queue_handler.listener.stop)  # type: ignore


def get_logger():
    return logging.getLogger("trailarr")  # __name__ is a common choice


if not _is_logging_setup:
    config_logging()
    _is_logging_setup = True
logger = get_logger()
