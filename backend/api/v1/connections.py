import asyncio

from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from api.v1 import websockets

import core.base.database.manager.connection as connection_manager
from core.base.database.models.connection import (
    ArrType,
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)
from core.diagnostics import connection_doctor
from core.diagnostics.models import DoctorReport, SuggestedMapping
from core.tasks.api_refresh import api_refresh_by_id_job, delete_connection_job
from core.tasks.schedules import ensure_plex_trailer_refresh_scheduled


def _schedule_doctor(connection_id: int) -> None:
    """Run the Connection Doctor in the background after a save.

    A failed check must never fail the save — errors show up in the
    report itself, or only in the log for unexpected ones.
    """

    async def _run() -> None:
        try:
            await connection_doctor.run_doctor(connection_id)
        except Exception as e:
            connection_doctor.logger.error(
                f"Doctor run failed for connection {connection_id}: {e}"
            )

    asyncio.create_task(_run())


connections_router = APIRouter(prefix="/connections", tags=["Connections"])


@connections_router.get("/doctor")
async def get_doctor_reports() -> list[DoctorReport]:
    """Last Connection Doctor report of every checked connection.

    Reports live in memory: after a restart the list is empty until a
    connection is saved or a check is run.
    """
    return connection_doctor.get_all_reports()


@connections_router.post(
    "/{connection_id}/doctor",
    responses={
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@connections_router.post(
    "/{connection_id}/doctor/mappings",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        },
    },
)
async def apply_doctor_mapping(
    connection_id: int, mapping: SuggestedMapping
) -> DoctorReport:
    """Apply a suggested path mapping, then re-run the check.

    Creates the PathMapping row on the connection (or updates the row
    with the same `path_from`) and returns the fresh report.
    """
    try:
        connection_manager.add_path_mapping(
            connection_id, mapping.path_from, mapping.path_to
        )
        return await connection_doctor.run_doctor(connection_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@connections_router.get("/")
async def get_connections() -> list[ConnectionRead]:
    connections = connection_manager.read_all()
    return connections


@connections_router.post(
    "/test",
    status_code=status.HTTP_200_OK,
    responses={
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
        result = await connection_manager.validate_connection(connection)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return result


@connections_router.post(
    "/rootfolders",
    status_code=status.HTTP_200_OK,
    responses={
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
        result = await connection_manager.get_rootfolders(connection)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return result


@connections_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
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
        result, connection_id = await connection_manager.create(connection)
        await refresh_connection(connection_id)
        if connection.arr_type == ArrType.PLEX:
            ensure_plex_trailer_refresh_scheduled(delay_seconds=180.0)
        # Check folder visibility and permissions in the background
        _schedule_doctor(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Failed to add Connection!", "Error"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    await websockets.ws_manager.broadcast(
        "Connection Created Successfully!", "Success", reload="connections"
    )
    return f"Connection Created Successfully! {result}"


@connections_router.get(
    "/{connection_id}",
    status_code=status.HTTP_200_OK,
    responses={
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    return connection


@connections_router.put(
    "/{connection_id}",
    status_code=status.HTTP_201_CREATED,
    responses={
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
        await connection_manager.update(connection_id, connection)
        # Refresh data from API for the connection
        await refresh_connection(connection_id)
        # Check folder visibility and permissions in the background
        _schedule_doctor(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast(
            "Failed to update Connection!", "Error"
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )
    await websockets.ws_manager.broadcast(
        "Connection Updated Successfully!", "Success", reload="connections"
    )
    return "Connection Updated Successfully!"


@connections_router.delete(
    "/{connection_id}",
    status_code=status.HTTP_200_OK,
    responses={
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
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
