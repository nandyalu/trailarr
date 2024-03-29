class ConnectionTimeoutError(Exception):
    """Raised when a connection times out"""

    pass


class InvalidResponseError(Exception):
    """Raised when a connection returns an invalid response"""

    pass


class ItemExistsError(Exception):
    """Raised when an Item already exists in the database"""

    pass


class ItemNotFoundError(Exception):
    """Raised when an Item is not found in the database"""

    def __init__(self, model_name: str, id: int) -> None:
        message = f"{model_name} with id {id} not found"
        super().__init__(message)

    pass
