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

    pass
