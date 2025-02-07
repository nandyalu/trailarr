import asyncio
from fastapi import WebSocket


class WSConnectionManager:
    """Connection manager for websockets to keep track of active connections \n
    ***Singleton Class***
    """

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

    async def broadcast(self, message: str, type: str = "Success") -> None:
        """Send a message to all connected clients.
        Args:
            message (str): The message to send.
            type (str, optional): The type of message. Defaults to "Success".
        Returns:
            None
        """
        for connection in self.active_connections:
            await connection.send_json({"type": type, "message": message})


def broadcast(message: str, type: str = "Success") -> None:
    """Send a message to all connected clients. Non-Async function.
    Args:
        message (str): The message to send.
        type (str, optional): The type of message. Defaults to "Success".
    Returns:
        None
    """

    def send_message() -> None:
        """Run the async task in a separate event loop."""
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        new_loop.run_until_complete(ws_manager.broadcast(message, type))
        new_loop.close()
        return

    send_message()
    return


ws_manager = WSConnectionManager()
