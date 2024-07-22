import atexit
import json
import logging
import logging.config
import multiprocessing
import pathlib
import threading

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


def set_handler_level(handler_name, level: int):
    """Set the level for a specific handler."""
    logger = logging.getLogger()
    for handler in logger.handlers:
        if handler.get_name() == handler_name:
            handler.setLevel(level)
            break
    return


def set_logger_level() -> None:
    """Set the log level for the root logger."""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    _log_level = "DEBUG" if app_settings.debug else "INFO"
    level = log_levels.get(_log_level, logging.INFO)
    logging.getLogger().setLevel(level)
    set_handler_level("console", level)
    set_handler_level("file", level)
    logging.info(f"Log level set to '{_log_level}'")
    return


def config_logging():
    """Setup the logging configuration using the config file.
    This will setup the root logger configuration and start the queue handler listener.
    """
    queue = multiprocessing.Queue(-1)
    parent_path = pathlib.Path(__file__).parent
    config_file = pathlib.Path(parent_path, "config", "logger_config.json")
    if config_file.exists():
        with open(config_file) as f_in:
            config = json.load(f_in)
    else:
        logging.debug(f"Logger config file not found: {config_file}")

    logging.config.dictConfig(config)
    set_logger_level()
    logger_thread = threading.Thread(target=handle_logs, args=(queue,))
    logger_thread.daemon = True
    logger_thread.start()
    atexit.register(stop_logging, queue)


def get_logger():
    return logging.getLogger("trailarr")  # __name__ is a common choice


class ModuleLogger(logging.LoggerAdapter):
    """A custom logger adapter to add a prefix to log messages."""

    def __init__(self, log_prefix: str):
        """Use this logger to add a prefix to log messages. \n
        Args:
            log_prefix (str): The prefix to add to log messages."""
        self.log_prefix = log_prefix
        logger = logging.getLogger(__name__)
        super(ModuleLogger, self).__init__(logger, {})

    def process(self, msg, kwargs):
        return "%s: %s" % (self.log_prefix, msg), kwargs


if not _is_logging_setup:
    config_logging()
    _is_logging_setup = True
logger = get_logger()
