import asyncio
from datetime import datetime, timedelta
from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.connection import ArrType, ConnectionRead
from core.radarr.connection_manager import RadarrConnectionManager
from core.sonarr.connection_manager import SonarrConnectionManager
from app_logger import ModuleLogger
from core.tasks.image_refresh import refresh_images
from core.tasks import scheduler

logger = ModuleLogger("APIRefreshTasks")


async def api_refresh() -> None:
    logger.info("Refreshing data from APIs")
    # Get all connections from database
    connnections = ConnectionDatabaseManager().read_all()
    if len(connnections) == 0:
        logger.warning("No connections found in the database")
        return
    
    # Refresh data from API for each connection
    for connection in connnections:
        await api_refresh_by_id(connection, image_refresh=False)
    
    # Refresh images after API refresh to download/update images for new media
    await refresh_images(recent_only=True)
    logger.info("API Refresh completed!")


async def api_refresh_by_id(connection: ConnectionRead, image_refresh=True) -> None:
    logger.info(f"Refreshing data from API for connection: {connection.name}")
    # Get connection manager based on connection type
    if connection.arr_type == ArrType.SONARR:
        connection_db_manager = SonarrConnectionManager(connection)
    elif connection.arr_type == ArrType.RADARR:
        connection_db_manager = RadarrConnectionManager(connection)
    else:
        logger.warning(
            f"Invalid connection type: {connection.arr_type} for connection: {connection}"
        )
        return
    
    # Refresh data from API
    await connection_db_manager.refresh()
    logger.info(f"Data refreshed for connection: {connection.name}")
    
    # Refresh images after API refresh to download/update images for new media
    if image_refresh:
        await refresh_images(recent_only=True)
        logger.info("Images refreshed")
        logger.info("API Refresh completed!")


def api_refresh_by_id_job(connection_id: int):
    def run_async(conn: ConnectionRead) -> None:
        """Run the async task in a separate event loop."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(api_refresh_by_id(conn))
        new_loop.close()
        return

    logger.info(f"Refreshing data from API for connection ID: {connection_id}")
    # Get connection from database
    try:
        connection = ConnectionDatabaseManager().read(connection_id)
    except Exception as e:
        msg = f"Failed to get connection with ID: {connection_id}"
        logger.error(f"{msg}. Error: {e}")
        return msg
    
    # Refresh data from API for the connection
    msg = f"Refreshing data from API for connection: {connection.name}"
    logger.info(msg)
    scheduler.add_job(
        func=run_async,
        args=(connection,),
        trigger='date',
        run_date=datetime.now() + timedelta(seconds=3),
        id=f"refresh_api_data_by_connection_{connection_id}",
        name=f"Arr Data Refresh for {connection.name}",
        max_instances=1,
    )
    return msg
