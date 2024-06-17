from fastapi import APIRouter, HTTPException, status

from api.v1.models import ErrorResponse
from core.base.database.manager.connection import ConnectionDatabaseManager
from core.base.database.models.connection import (
    ConnectionCreate,
    ConnectionRead,
    ConnectionUpdate,
)
from core.tasks.api_refresh import api_refresh_by_id

connections_router = APIRouter(prefix="/connections", tags=["Connections"])


@connections_router.get("/")
async def get_connections() -> list[ConnectionRead]:
    db_handler = ConnectionDatabaseManager()
    connections = db_handler.read_all()
    return connections


@connections_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Connection Created Successfully! "
            "Radarr Connection Successful Version: 3.0.1.4252"
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
        result = await db_handler.create(connection)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        await db_handler.update(connection_id, connection)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
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
    return api_refresh_by_id(connection_id)


# @connections_router.post("/")
# async def create_connection(
#     connection_name: str,
#     arr_type: ArrType,
#     arr_url: str,
#     arr_api_key: str,
#     monitor: MonitorType,
# ) -> str:
#     connection = ConnectionCreate(
#         name=connection_name,
#         arr_type=arr_type,
#         url=arr_url,
#         api_key=arr_api_key,
#         monitor=monitor,
#     )
#     db_handler = ConnectionDatabaseManager()
#     connection1 = await db_handler.create(connection)
#     return connection1
