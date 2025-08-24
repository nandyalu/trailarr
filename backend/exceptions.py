class ConnectionTimeoutError(Exception):
    """Raised when a connection times out"""

    pass


class ConversionFailedError(Exception):
    """Raised when a video conversion fails"""

    pass


class DownloadFailedError(Exception):
    """Raised when a video download fails"""

    pass


class FileMoveFailedError(Exception):
    """Raised when a file move operation fails"""

    pass


class FolderPathEmptyError(Exception):
    """Raised when a folder path is empty or invalid"""

    pass


class FolderNotFoundError(Exception):
    """Raised when a folder is not found"""

    def __init__(self, folder_path: str) -> None:
        message = f"Folder not found in the system: {folder_path}"
        super().__init__(message)

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
