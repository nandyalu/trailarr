
from fastapi import APIRouter, HTTPException, status

from api.v1 import errors
from app_logger import ModuleLogger
from api.v1.models import ErrorResponse
from api.v1 import websockets

import database.manager.connection as connection_manager
from services.connections import probe as connection_probe
from services.connections import service as connection_service
from database.models.connection import (
    ArrType,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)
from services.diagnostics import connection_doctor
from services.diagnostics.models import DoctorReport, SuggestedMapping
from tasks.api_refresh import api_refresh_by_id_job, delete_connection_job
from tasks.schedules import ensure_plex_trailer_refresh_scheduled

def _schedule_refresh(connection_id: int) -> None:
    """Sync a connection after its path mapping is fixed.

    `api_refresh_by_id_job` only registers the task with the scheduler
    and returns at once, so this does not delay the response.
    """
    try:
        api_refresh_by_id_job(connection_id)
    except Exception as e:
        connection_doctor.logger.error(
            "Refresh after a mapping fix failed for connection"
            f" {connection_id}: {e}"
        )


logger = ModuleLogger("ConnectionsAPI")

connections_router = APIRouter(prefix="/connections", tags=["Connections"])


@connections_router.get("/doctor")
async def get_doctor_reports() -> list[DoctorReport]:
    """Last Connection Doctor report of every checked connection.

    Trailarr stores the reports on disk, so a report stays after a
    restart. A connection that was never checked has no report.
    """
    return connection_doctor.get_all_reports()


@connections_router.post(
    "/doctor/preview",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Could not check the connection",
        },
    },
)
async def preview_connection_doctor(
    connection: ConnectionCreate, connection_id: int = 0
) -> DoctorReport:
    """Run the Connection Doctor for a connection that is not saved yet.

    The Add/Edit Connection page calls this, so the user can find the
    right path mappings before saving. Nothing is stored.

    Args:
        connection: The connection as entered on the form.
        connection_id: The id when an existing connection is edited, so
            the suggester can use its already synced media folders.
    """
    try:
        return await connection_doctor.preview_doctor(
            connection, connection_id
        )
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Check the connection",
            safe_status=status.HTTP_400_BAD_REQUEST,
        )


@connections_router.post("/doctor/run-all")
async def run_all_connection_doctors() -> list[DoctorReport]:
    """Run the Connection Doctor for every connection, all at once.

    Saves the user from opening one dialog per connection.
    """
    return await connection_doctor.run_doctor_for_all()


@connections_router.post(
    "/{connection_id}/doctor",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        },
    },
)
async def run_connection_doctor(connection_id: int) -> DoctorReport:
    """Run the Connection Doctor for one connection and return the report."""
    try:
        return await connection_doctor.run_doctor(connection_id)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Run the Connection Doctor",
            safe_status=status.HTTP_404_NOT_FOUND,
        )


@connections_router.post(
    "/{connection_id}/doctor/mappings",
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        },
    },
)
async def apply_doctor_mapping(
    connection_id: int, mapping: SuggestedMapping
) -> DoctorReport:
    """Apply a suggested path mapping, re-check, and refresh the library.

    Creates the PathMapping row on the connection (or updates the row
    with the same `path_from`) and returns the fresh report.

    A correct mapping is not sufficient. Until the next sync runs,
    the media still points at paths Trailarr cannot see. The refresh
    starts right away, so the library fills in instead of staying
    broken until the next scheduled sync.
    """
    try:
        report = await connection_doctor.apply_mapping_and_recheck(
            connection_id, mapping.path_from, mapping.path_to
        )
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Apply the path mapping",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    if report.status == "healthy":
        _schedule_refresh(connection_id)
    return report


@connections_router.get("/")
async def get_connections() -> list[ConnectionRead]:
    connections = connection_manager.read_all()
    return connections


@connections_router.post(
    "/test",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_200_OK: {
            "description": "Radarr Connection Successful Version: 3.x.x.x",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Connection Failed",
        },
    },
)
async def test_connection(connection: ConnectionCreate) -> str:
    try:
        result = await connection_probe.validate_connection(connection)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Test the connection",
            safe_status=status.HTTP_400_BAD_REQUEST,
        )
    return result


@connections_router.post(
    "/rootfolders",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_200_OK: {
            "description": "Root Folders Retrieved Successfully!",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Root Folders Not Retrieved",
        },
    },
)
async def get_rootfolders(connection: ConnectionCreate) -> list[str]:
    try:
        result = await connection_probe.get_rootfolders(connection)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Read the root folders",
            safe_status=status.HTTP_400_BAD_REQUEST,
        )
    return result


@connections_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_201_CREATED: {
            "description": (
                "Connection Created Successfully! "
                "Radarr Connection Successful Version: 3.x.x.x"
            ),
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Connection Not Created",
        },
    },
)
async def create_connection(connection: ConnectionCreate) -> str:
    try:
        result, connection_id = await connection_service.create(connection)
        await refresh_connection(connection_id)
        if connection.arr_type == ArrType.PLEX:
            ensure_plex_trailer_refresh_scheduled(delay_seconds=180.0)
        # Check folder visibility and permissions in the background
        connection_doctor.schedule_doctor(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Failed to add Connection!", "Error"
        )
        raise errors.as_http_error(
            e, logger=logger, action="Create the connection",
            safe_status=status.HTTP_400_BAD_REQUEST,
        )
    await websockets.ws_manager.broadcast(
        "Connection Created Successfully!", "Success", reload="connections"
    )
    return f"Connection Created Successfully! {result}"


@connections_router.get(
    "/{connection_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        }
    },
)
async def get_connection(connection_id: int) -> ConnectionRead:
    try:
        connection = connection_manager.read(connection_id)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Read the connection",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    return connection


@connections_router.put(
    "/{connection_id}",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_201_CREATED: {
            "description": "Connection Updated Successfully!",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Updated",
        },
    },
)
async def update_connection(
    connection_id: int, connection: ConnectionUpdate
) -> str:
    try:
        # Update the connection in the database
        await connection_service.update(connection_id, connection)
        # Refresh data from API for the connection
        await refresh_connection(connection_id)
        # Check folder visibility and permissions in the background
        connection_doctor.schedule_doctor(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Failed to update Connection!", "Error"
        )
        raise errors.as_http_error(
            e, logger=logger, action="Update the connection",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    await websockets.ws_manager.broadcast(
        "Connection Updated Successfully!", "Success", reload="connections"
    )
    return "Connection Updated Successfully!"


@connections_router.delete(
    "/{connection_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": ErrorResponse,
            "description": "Unexpected error",
        },
        status.HTTP_200_OK: {
            "description": "Connection deletion scheduled.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        },
    },
)
async def delete_connection(connection_id: int) -> str:
    try:
        msg = delete_connection_job(connection_id)
    except Exception as e:
        raise errors.as_http_error(
            e, logger=logger, action="Delete the connection",
            safe_status=status.HTTP_404_NOT_FOUND,
        )
    connection_doctor.forget_report(connection_id)
    return msg


@connections_router.get(
    "/{connection_id}/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        }
    },
)
async def refresh_connection(connection_id: int) -> str:
    return api_refresh_by_id_job(connection_id)
