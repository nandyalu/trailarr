import http
import time

from fastapi import FastAPI, Request

from app_logger import uvicorn_logger as logger
from config.logging_context import with_logging_context

# Inspiration: https://medium.com/@roy-pstr/fastapi-server-errors-and-logs-take-back-control-696405437983  # noqa: E501


class ColorCodes:
    informational = "\x1b[1;34m"  # blue
    # grey = "\x1b[38;21m"  # 1xx - Informational
    success = "\x1b[1;32m"  # green
    redirection = "\x1b[33;21m"  # yellow
    client_error = "\x1b[31;21m"  # red
    server_error = "\x1b[31;1m"  # bold_red
    light_blue = "\x1b[1;36m"
    purple = "\x1b[1;35m"
    reset = "\x1b[0m"


def get_colored_status(status_code: int) -> str:
    # Default status code to return if the status code is not recognized
    _default = f"{ColorCodes.purple}000 Unknown{ColorCodes.reset}"
    if status_code is None:
        return _default
    if not isinstance(status_code, int):
        try:
            status_code = int(status_code)
        except ValueError:
            return _default

    color = ColorCodes.reset
    if 100 <= status_code < 200:
        color = ColorCodes.informational
    elif 200 <= status_code < 300:
        color = ColorCodes.success
    elif 300 <= status_code < 400:
        color = ColorCodes.redirection
    elif 400 <= status_code < 500:
        color = ColorCodes.client_error
    elif 500 <= status_code < 600:
        color = ColorCodes.server_error
    else:
        color = ColorCodes.reset
    try:
        status_phrase = http.HTTPStatus(status_code).phrase
    except ValueError:
        status_phrase = ""
    return f"{color}{status_code} {status_phrase}{ColorCodes.reset}"


def get_colored_status_method(method: str) -> str:
    if method is None:
        return f"{ColorCodes.purple}Unknown{ColorCodes.reset}"
    if not isinstance(method, str):
        return f"{ColorCodes.purple}Unknown{ColorCodes.reset}"
    if method.upper() == "GET":
        return f"{ColorCodes.light_blue}{method}{ColorCodes.reset}"
    if method.upper() == "POST":
        return f"{ColorCodes.success}{method}{ColorCodes.reset}"
    if method.upper() == "PUT":
        return f"{ColorCodes.redirection}{method}{ColorCodes.reset}"
    if method.upper() == "DELETE":
        return f"{ColorCodes.client_error}{method}{ColorCodes.reset}"
    return f"{ColorCodes.purple}{method}{ColorCodes.reset}"


@with_logging_context
async def log_timing_middleware(request: Request, call_next):
    """
    This middleware will log all requests and their processing time.
    E.g. log:
    0.0.0.0:1234 - GET /ping 200 OK 1.00ms
    """
    # logger.debug("middleware: log_request_middleware")
    url = (
        f"{request.url.path}?{request.query_params}"
        if request.query_params
        else request.url.path
    )
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    process_time = (  # Convert to milliseconds
        f"{round(process_time * 1000, 2)}ms"
    )

    # Set the X-Process-Time header to the response
    response.headers["X-Process-Time"] = process_time

    host = getattr(getattr(request, "client", None), "host", None)
    port = getattr(getattr(request, "client", None), "port", None)

    method = get_colored_status_method(request.method)
    status = get_colored_status(response.status_code)
    logger.info(f'{host}:{port} - "{method} {url}" {status} {process_time}')
    return response


def setup_timing_middleware(app: FastAPI) -> None:
    app.middleware("http")(log_timing_middleware)

    return None
