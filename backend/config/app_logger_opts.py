import logging


def set_handler_level(handler_name, log_level: int):
    """Set the level for a specific handler."""
    logger = logging.getLogger()
    for handler in logger.handlers:
        if handler.get_name() == handler_name:
            handler.setLevel(log_level)
            break
    return


def set_logger_level(log_level: str) -> None:
    """Set the log level for the root logger."""
    log_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    # _log_level = "DEBUG" if app_settings.debug else "INFO"
    level = log_levels.get(log_level, logging.INFO)
    # logging.getLogger().setLevel(level) # log everything on root logger
    set_handler_level("console", level)
    # set_handler_level("file", level)
    logging.info(f"Log level set to '{log_level}'")
    return
