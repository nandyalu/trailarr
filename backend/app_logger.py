import atexit
import json
import logging
import logging.config
import multiprocessing
import pathlib
import threading

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
    queue = multiprocessing.Queue(-1)
    parent_path = pathlib.Path(__file__).parent
    config_file = pathlib.Path(parent_path, "config", "logger_config.json")
    if config_file.exists():
        with open(config_file) as f_in:
            config = json.load(f_in)
    else:
        logging.debug(f"Logger config file not found: {config_file}")

    logging.config.dictConfig(config)
    logger_thread = threading.Thread(target=handle_logs, args=(queue,))
    logger_thread.daemon = True
    logger_thread.start()
    atexit.register(stop_logging, queue)


def get_logger():
    return logging.getLogger("trailarr")  # __name__ is a common choice


if not _is_logging_setup:
    config_logging()
    _is_logging_setup = True
logger = get_logger()
