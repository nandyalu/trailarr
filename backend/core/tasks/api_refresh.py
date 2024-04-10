from backend.core.base.database.manager.connection import ConnectionDatabaseManager
from backend.core.base.database.models.connection import ArrType
from backend.core.radarr.connection_manager import RadarrConnectionManager
from backend.core.sonarr.connection_manager import SonarrConnectionManager
from backend.app_logger import logger
from backend.core.tasks.image_refresh import refresh_images


async def api_refresh():
    logger.info("Refreshing data from APIs")
    # Get all connections from database
    connnections = ConnectionDatabaseManager().read_all()
    if len(connnections) == 0:
        logger.warning("No connections found in the database")
        return
    # Refresh data from API for each connection
    for connection in connnections:
        logger.info(f"Refreshing data from API for connection: {connection.name}")
        # Call the API to get the latest data
        if connection.arr_type == ArrType.SONARR:
            connection_db_manager = SonarrConnectionManager(connection)
        elif connection.arr_type == ArrType.RADARR:
            connection_db_manager = RadarrConnectionManager(connection)
        else:
            logger.warning(
                f"Invalid connection type: {connection.arr_type} for connection: {connection}"
            )
            continue
        await connection_db_manager.refresh()
        logger.info(f"Data refreshed for connection: {connection.name}")
    # Refresh images after API refresh to download/update images for new media
    await refresh_images(recent_only=True)
    logger.info("API Refresh completed!")
