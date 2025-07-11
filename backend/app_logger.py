import atexit
import json
import logging
import logging.config
import multiprocessing
import pathlib
import threading

from config import app_logger_opts
from config.settings import app_settings

_is_logging_setup = False


def handle_logs(q: multiprocessing.Queue):
    while True:
        record = q.get()
        # if record is None:
        #     break
        logger = logging.getLogger(record.name)
        logger.handle(record)


def stop_logging(queue: multiprocessing.Queue):
    # queue.put_nowait(None) # Did not work, raising an exception
    queue.close()


def config_logging():
    """Setup the logging configuration using the config file.
    This will setup the root logger configuration and start the queue handler listener.
    """
    # Disable uvicorn access logger
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers = []
    uvicorn_access.disabled = True

    # FastAPI logger
    queue = multiprocessing.Queue(-1)
    parent_path = pathlib.Path(__file__).parent
    config_file = pathlib.Path(parent_path, "config", "logger_config.json")
    config = {}
    if config_file.exists():
        with open(config_file) as f_in:
            config = json.load(f_in)
        config["handlers"]["file"][
            "filename"
        ] = f"{app_settings.app_data_dir}/logs/trailarr.log"
    else:
        logging.debug(f"Logger config file not found: {config_file}")

    logging.config.dictConfig(config)
    app_logger_opts.set_logger_level(app_settings.log_level)
    logger_thread = threading.Thread(target=handle_logs, args=(queue,))
    logger_thread.daemon = True
    logger_thread.start()
    atexit.register(stop_logging, queue)


def get_logger():
    return logging.getLogger("trailarr")  # __name__ is a common choice


TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


class ModuleLogger(logging.LoggerAdapter):
    """A custom logger adapter to add a prefix to log messages."""

    def __init__(self, log_prefix: str):
        """Use this logger to add a prefix to log messages. \n
        Args:
            log_prefix (str): The prefix to add to log messages."""
        self.log_prefix = log_prefix
        logger = logging.getLogger(log_prefix)
        super().__init__(logger)

    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(TRACE_LEVEL):
            self._log(TRACE_LEVEL, message, args, **kwargs)

    # def process(self, msg, kwargs):
    #     return "%s: %s" % (self.log_prefix, msg), kwargs


if not _is_logging_setup:
    config_logging()
    _is_logging_setup = True
logger = get_logger()

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.getLevelName(logging.DEBUG))
