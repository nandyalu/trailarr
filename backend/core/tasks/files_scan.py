from app_logger import ModuleLogger
from core.base.database.manager.base import MediaDatabaseManager
import core.base.database.manager.connection as connection_manager
from core.base.database.models.connection import ArrType
from core.files_handler import FilesHandler
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager

logger = ModuleLogger("TrailersFilesScan")


async def scan_disk_for_trailers() -> None:
    """Scan the disk for trailers and update the database with the new status. \n
    Returns:
        None
    """
    logger.info("Scanning disk for trailers.")
    # # Get all media from the database
    db_handler = MediaDatabaseManager()
    all_media = db_handler.read_all()

    # # Get all root folders from the media folders
    # root_folders: set[str] = set()
    # root_folders = {
    #     os.path.dirname(media.folder_path) for media in all_media if media.folder_path
    # }

    root_folders: set[str] = set()

    # Get all connections from the database
    all_connections = connection_manager.read_all()

    # Get all root folders for each connection from API
    for connection in all_connections:
        if connection.arr_type == ArrType.RADARR:
            arr_manager = RadarrConnectionManager(connection)
        elif connection.arr_type == ArrType.SONARR:
            arr_manager = SonarrConnectionManager(connection)
        else:
            continue
        root_folders.update(await arr_manager.get_rootfolders())

    # Find all folders with trailers
    trailer_folders: set[str] = set()
    for root_folder in root_folders:
        trailer_folders.update(
            await FilesHandler.scan_root_folders_for_trailers(root_folder)
        )

    # Match the trailer folders to the media in the database
    updated_media: list[tuple[int, bool]] = []
    for media in all_media:
        if not media.folder_path:
            continue
        # Check if trailer was found
        _trailer_exists = media.trailer_exists
        for folder in trailer_folders:
            if folder.startswith(media.folder_path):
                _trailer_exists = True
                break
        # _trailer_exists = media.folder_path in trailer_folders
        if media.trailer_exists != _trailer_exists:
            updated_media.append((media.id, _trailer_exists))

    # Update the database with the new trailer status
    db_handler.update_trailer_exists_bulk(updated_media)
    if len(updated_media) == 0:
        logger.info("Media trailer statuses are up to date.")
        return None
    logger.info(
        f"Updated {len(updated_media)} media items with new trailer status."
    )
    return None
