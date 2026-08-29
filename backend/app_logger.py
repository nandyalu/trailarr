"""Set up logging, and give each module a logger with its own name.

`ModuleLogger` also carries the media id a log line is about. Use
`logger.info(msg, **logger.media(media.id))`: the Logs page links a line to
a title from that field, and the message itself needs no id in it.
"""

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

    # Set aiosqlite logger to critical level
    aiosqlite_logger = logging.getLogger("aiosqlite")
    aiosqlite_logger.setLevel(logging.CRITICAL)

    # FastAPI logger
    queue = multiprocessing.Queue(-1)
    parent_path = pathlib.Path(__file__).parent
    config_file = pathlib.Path(parent_path, "config", "logger_config.json")
    config = {}
    if config_file.exists():
        with open(config_file) as f_in:
            config = json.load(f_in)
        # config["handlers"]["file"][
        #     "filename"
        # ] = f"{app_settings.app_data_dir}/logs/trailarr.log"
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

    def process(self, msg, kwargs):
        """Keep the fields the caller passed in `extra`.

        The default LoggerAdapter replaces `kwargs["extra"]` with the
        adapter's own, which is None here, so
        `logger.info(msg, extra={"mediaid": 42})` was thrown away without a
        word. The database handler needs that field to link a log line to
        its media item.
        """
        caller_extra = kwargs.get("extra")
        if self.extra and caller_extra:
            kwargs["extra"] = {**self.extra, **caller_extra}
        elif self.extra:
            kwargs["extra"] = dict(self.extra)
        # A caller's extra with no adapter extra is already in kwargs
        return msg, kwargs

    def media(self, media_id: int | None) -> dict:
        """Build the `extra` that links a log line to a media item.

        Use it as `logger.info("...", **logger.media(media.id))`. The
        message can then say whatever reads best: the link comes from this
        field, not from the wording.

        Args:
            media_id (int | None): The media item the line is about.

        Returns:
            dict: The keyword arguments to pass to the logging call.
        """
        if media_id is None:
            return {}
        return {"extra": {"mediaid": media_id}}


if not _is_logging_setup:
    config_logging()
    _is_logging_setup = True
logger = get_logger()

uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.getLevelName(logging.DEBUG))
