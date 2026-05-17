"""Connection service — external API calls and orchestration.

Pure DB CRUD lives in db.repos.connection.
This module owns:
- validate_connection() — hits external APIs (Arr/Plex) to test connectivity
- get_rootfolders()     — hits external APIs to fetch root folder list
- create()             — validate → fetch machine_identifier (Plex) → save to DB
- update()             — validate → update machine_identifier → save to DB
- delete()             — fire PLEX_UNLINKED events before deleting
- refresh_connection() — run Arr/Plex sync, track failures, upsert/resolve issues
"""
from app_logger import ModuleLogger
from db.models.connection import ArrType, ConnectionBase, ConnectionCreate, ConnectionRead, ConnectionUpdate
from db.models.issue import EntityType, IssueType
import db.repos.connection as connection_repo
import db.repos.issue as issue_repo
from services.event_service import track_plex_unlinked
from db.models.event import EventSource
from exceptions import ItemNotFoundError

logger = ModuleLogger("ConnectionService")

_CONNECTION_FAILURE_THRESHOLD = 3
_consecutive_failures: dict[int, int] = {}
_AUTH_ERROR_KEYWORDS = ("unauthorized", "access restricted", "api key")


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(kw in msg for kw in _AUTH_ERROR_KEYWORDS)


async def validate_connection(connection: ConnectionBase) -> str:
    """Test connectivity to the Arr/Plex server. Returns version string."""
    if not connection:
        raise ItemNotFoundError("Connection", 0)
    if connection.arr_type == ArrType.RADARR:
        from integrations.arr.radarr import RadarrManager
        return await RadarrManager(connection.url, connection.api_key).get_system_status()
    elif connection.arr_type == ArrType.SONARR:
        from integrations.arr.sonarr import SonarrManager
        return await SonarrManager(connection.url, connection.api_key).get_system_status()
    elif connection.arr_type == ArrType.PLEX:
        from integrations.plex.client import PlexAPI
        return await PlexAPI(connection.url, connection.api_key, identifier="trailarr_1234").get_system_status()
    return ""


async def get_rootfolders(connection: ConnectionBase) -> list[str]:
    """Return the root folders from the Arr/Plex server."""
    if not connection:
        raise ItemNotFoundError("Connection", 0)
    if connection.arr_type == ArrType.RADARR:
        from integrations.arr.radarr import RadarrManager
        return await RadarrManager(connection.url, connection.api_key).get_rootfolders()
    elif connection.arr_type == ArrType.SONARR:
        from integrations.arr.sonarr import SonarrManager
        return await SonarrManager(connection.url, connection.api_key).get_rootfolders()
    elif connection.arr_type == ArrType.PLEX:
        from integrations.plex.client import PlexAPI
        return await PlexAPI(connection.url, connection.api_key, identifier="trailarr_1234").get_library_folders()
    return []


async def create(connection_create: ConnectionCreate) -> tuple[ConnectionRead, int]:
    """Validate, fetch Plex machine_identifier if needed, then persist."""
    status_msg = await validate_connection(connection_create)
    machine_identifier: str | None = None
    if connection_create.arr_type == ArrType.PLEX:
        from integrations.plex.client import PlexAPI
        plex_api = PlexAPI(connection_create.url, connection_create.api_key, identifier="trailarr_1234")
        machine_identifier = await plex_api.get_machine_identifier()

    from db.models.connection import Connection
    from utils.path_utils import normalize_trailing_slash
    from db.models.connection import PathMapping

    path_mappings = []
    for pm in connection_create.path_mappings:
        db_pm = PathMapping.model_validate(pm)
        db_pm.path_from = normalize_trailing_slash(db_pm.path_from)
        db_pm.path_to = normalize_trailing_slash(db_pm.path_to)
        path_mappings.append(db_pm)

    connection_create.path_mappings = []
    db_conn = Connection.model_validate(connection_create)
    db_conn.path_mappings = path_mappings
    if machine_identifier is not None:
        db_conn.machine_identifier = machine_identifier

    new_id = connection_repo.save(db_conn)
    return connection_repo.read(new_id), new_id


async def update(connection_id: int, connection_update: ConnectionUpdate) -> ConnectionRead:
    """Validate, refresh Plex machine_identifier, then update DB row."""
    await validate_connection(connection_update)
    machine_identifier: str | None = None
    if connection_update.arr_type == ArrType.PLEX:
        from integrations.plex.client import PlexAPI
        plex_id = f"trailarr_{connection_id}"
        plex_api = PlexAPI(connection_update.url, connection_update.api_key, identifier=plex_id)
        machine_identifier = await plex_api.get_machine_identifier()
    return connection_repo.update(connection_id, connection_update, machine_identifier)


def delete(connection_id: int) -> bool:
    """Fire PLEX_UNLINKED events for linked media, then delete the connection."""
    conn = connection_repo.read(connection_id)
    if conn.arr_type == ArrType.PLEX:
        linked = connection_repo.read_arr_linked_to_plex(connection_id)
        for media in linked:
            track_plex_unlinked(
                media_id=media.id,
                connection_name=conn.name,
                source=EventSource.SYSTEM,
                source_detail="ConnectionDeleted",
            )
    return connection_repo.delete(connection_id)


async def refresh_connection(connection: ConnectionRead) -> None:
    """Run Arr/Plex sync for one connection. Tracks consecutive failures and upserts/resolves issues."""
    logger.info(f"Refreshing data from API for connection: {connection.name}")
    if connection.arr_type == ArrType.SONARR:
        from integrations.arr.sonarr import SonarrConnectionManager
        manager = SonarrConnectionManager(connection)
    elif connection.arr_type == ArrType.RADARR:
        from integrations.arr.radarr import RadarrConnectionManager
        manager = RadarrConnectionManager(connection)
    elif connection.arr_type == ArrType.PLEX:
        from integrations.plex.sync import PlexConnectionManager
        manager = PlexConnectionManager(connection)
    else:
        logger.warning(f"Invalid connection type: {connection.arr_type} for connection: {connection}")
        return

    try:
        await manager.refresh()
    except Exception as exc:
        _consecutive_failures[connection.id] = _consecutive_failures.get(connection.id, 0) + 1
        failures = _consecutive_failures[connection.id]
        logger.error(
            f"Connection '{connection.name}' refresh failed "
            f"({failures} consecutive failure(s)): {exc}"
        )
        if _is_auth_error(exc):
            issue_repo.upsert(
                issue_type=IssueType.TOKEN_INVALID,
                entity_type=EntityType.CONNECTION,
                entity_id=connection.id,
                description=(
                    f"API token for connection '{connection.name}' was rejected."
                    " Update the API key in Settings → Connections."
                ),
                details=str(exc),
            )
        elif failures >= _CONNECTION_FAILURE_THRESHOLD:
            issue_repo.upsert(
                issue_type=IssueType.CONNECTION_FAILED,
                entity_type=EntityType.CONNECTION,
                entity_id=connection.id,
                description=(
                    f"Connection '{connection.name}' has failed {failures} consecutive time(s)."
                    " Check the URL and network access in Settings → Connections."
                ),
                details=str(exc),
            )
        return

    if connection.id in _consecutive_failures:
        del _consecutive_failures[connection.id]
    issue_repo.resolve(IssueType.CONNECTION_FAILED, EntityType.CONNECTION, connection.id)
    issue_repo.resolve(IssueType.TOKEN_INVALID, EntityType.CONNECTION, connection.id)
    logger.info(f"Data refreshed for connection: {connection.name}")
