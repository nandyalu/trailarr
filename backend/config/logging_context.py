from contextvars import ContextVar, Token
from functools import wraps
import uuid

# Define a ContextVar to hold the Trace ID
trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)


def get_trace_id() -> str | None:
    """Returns the current Trace ID."""
    return trace_id_var.get()


def get_new_trace_id() -> str:
    """Generates and returns a new Trace ID without setting it in the context."""
    return str(uuid.uuid4())


def generate_trace_id(trace_id: str | None = None) -> Token:
    """Generates a new Trace ID and sets it in the context."""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    return trace_id_var.set(trace_id)


def clear_trace_id(token: Token) -> None:
    """Clears the Trace ID from the context."""
    trace_id_var.reset(token)


def with_logging_context(func):
    """Decorator to add a Trace ID to the logging context for the duration of the function call.
    Args:
        func: The function to decorate.
    Returns:
        The decorated function with Trace ID management.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the trace_id from kwargs if provided and
        # generate/set it for the logging context
        trace_id = kwargs.get("trace_id")
        token = generate_trace_id(trace_id)
        try:
            return func(*args, **kwargs)
        finally:
            clear_trace_id(token)

    return wrapper
