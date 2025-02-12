from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from api.v1 import websockets
from core.base.database.manager.connection import (
    ConnectionDatabaseManager,
    validate_connection,
    get_connection_rootfolders,
)
from core.base.database.models.connection import (
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)
from core.tasks.api_refresh import api_refresh_by_id_job

connections_router = APIRouter(prefix="/connections", tags=["Connections"])


@connections_router.get("/")
async def get_connections() -> list[ConnectionRead]:
    db_handler = ConnectionDatabaseManager()
    connections = db_handler.read_all()
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
        result = await validate_connection(connection)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        result = await get_connection_rootfolders(connection)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return result


@connections_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Connection Created Successfully! "
            "Radarr Connection Successful Version: 3.x.x.x",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": "Connection Not Created",
        },
    },
)
async def create_connection(connection: ConnectionCreate) -> str:
    db_handler = ConnectionDatabaseManager()
    try:
        result, connection_id = await db_handler.create(connection)
        await refresh_connection(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast("Failed to add Connection!", "Error")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    await websockets.ws_manager.broadcast("Connection Created Successfully!", "Success")
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
    db_handler = ConnectionDatabaseManager()
    try:
        connection = db_handler.read(connection_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
async def update_connection(connection_id: int, connection: ConnectionUpdate) -> str:
    db_handler = ConnectionDatabaseManager()
    try:
        # Update the connection in the database
        await db_handler.update(connection_id, connection)
        # Refresh data from API for the connection
        await refresh_connection(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast("Failed to update Connection!", "Error")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    await websockets.ws_manager.broadcast("Connection Updated Successfully!", "Success")
    return "Connection Updated Successfully!"


@connections_router.delete(
    "/{connection_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": "Connection Deleted Successfully!",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "Connection Not Found",
        },
    },
)
async def delete_connection(connection_id: int) -> str:
    db_handler = ConnectionDatabaseManager()
    try:
        db_handler.delete(connection_id)
    except Exception as e:
        await websockets.ws_manager.broadcast("Failed to delete Connection!", "Error")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    await websockets.ws_manager.broadcast("Connection Deleted Successfully!", "Success")
    return "Connection Deleted Successfully!"


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
