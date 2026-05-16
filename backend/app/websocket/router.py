from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.websocket.connection_manager import manager
from app.core.jwt import verify_access_token

router = APIRouter()

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = Query(...)):
    """
    Main WebSocket connection endpoint.
    
    Connect with:
    ws://localhost:8000/ws/{user_id}?token=<jwt_token>
    
    Once connected, user can:
    - join a ride room
    - send location updates (drivers)
    - receive real-time events
    """

    # Verify JWT token before accepting connection
    payload = verify_access_token(token)
    if not payload or payload.get("user_id") != user_id:
        await websocket.close(code=4001)
        return

    # Accept and register connection
    await manager.connect(websocket, user_id)

    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_json()
            event = data.get("event")

            # Driver or rider joins a specific ride room
            if event == "join_ride":
                ride_id = data.get("ride_id")
                if ride_id:
                    manager.join_ride_room(ride_id, user_id)
                    await manager.send_to_user(user_id, {
                        "event": "joined_ride_room",
                        "ride_id": ride_id
                    })

            # Driver sends live location
            elif event == "location_update":
                ride_id = data.get("ride_id")
                latitude = data.get("latitude")
                longitude = data.get("longitude")

                if ride_id and latitude and longitude:
                    # Broadcast driver location to everyone in the ride room
                    await manager.broadcast_to_ride_room(ride_id, {
                        "event": "driver_location_updated",
                        "ride_id": ride_id,
                        "latitude": latitude,
                        "longitude": longitude
                    })

            # Leave a ride room
            elif event == "leave_ride":
                ride_id = data.get("ride_id")
                if ride_id:
                    manager.leave_ride_room(ride_id, user_id)

            else:
                await manager.send_to_user(user_id, {
                    "event": "error",
                    "message": f"Unknown event: {event}"
                })

    except WebSocketDisconnect:
        manager.disconnect(user_id)