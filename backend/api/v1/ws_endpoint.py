from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from api.v1.deps import validate_api_key_cookie
from ws.manager import ws_manager

ws_router = APIRouter(tags=["WebSocket"])


@ws_router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    authenticated: bool = Depends(validate_api_key_cookie),
):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
