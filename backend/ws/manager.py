from typing import Any
from fastapi import WebSocket
from pydantic import BaseModel


class WSConnectionManager:
    """Singleton WebSocket connection manager."""

    _instance = None

    def __new__(cls) -> "WSConnectionManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(
        self, message: str, type: str = "Success", reload: str = "none"
    ) -> None:
        """Broadcast a notification to all clients. Used for bulk background ops.

        Kept for backwards compatibility with existing task/reload patterns.
        """
        for connection in self.active_connections:
            await connection.send_json(
                {"type": type, "message": message, "reload": reload}
            )

    async def push(self, event: str, data: BaseModel | dict[str, Any]) -> None:
        """Push a typed data object to all clients.

        Used for interactive single-object writes so the frontend can patch
        its in-memory signal without issuing a full table re-fetch.

        Args:
            event: entity:action string, e.g. "media:updated", "connection:deleted"
            data: The updated object (Pydantic model or plain dict).
                  For deletions, pass {"id": <id>}.
        """
        if not self.active_connections:
            return
        payload = data.model_dump(mode="json") if isinstance(data, BaseModel) else data
        for connection in self.active_connections:
            await connection.send_json({"event": event, "data": payload})

    async def notify(
        self, message: str, *, type: str = "Success", reload: str = "none"
    ) -> None:
        """Named alias for broadcast — clearer at call sites in services/tasks."""
        await self.broadcast(message, type=type, reload=reload)


ws_manager = WSConnectionManager()


def broadcast(message: str, type: str = "Success", reload: str = "none") -> None:
    """Non-async broadcast for contexts that cannot await (e.g. sync callbacks)."""
    from quiv import run_on_main
    run_on_main(ws_manager.broadcast, message, type, reload)
