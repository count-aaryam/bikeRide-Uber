from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        # user_id → websocket
        self.active_connections: Dict[int, WebSocket] = {}
        
        # ride_id → set of user_ids in that room
        self.ride_rooms: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove user from all ride rooms
        for ride_id in list(self.ride_rooms.keys()):
            self.ride_rooms[ride_id].discard(user_id)
            # Clean up empty rooms
            if not self.ride_rooms[ride_id]:
                del self.ride_rooms[ride_id]
        
        print(f"User {user_id} disconnected")

    def join_ride_room(self, ride_id: int, user_id: int):
        if ride_id not in self.ride_rooms:
            self.ride_rooms[ride_id] = set()
        self.ride_rooms[ride_id].add(user_id)
        print(f"User {user_id} joined ride room {ride_id}")

    def leave_ride_room(self, ride_id: int, user_id: int):
        if ride_id in self.ride_rooms:
            self.ride_rooms[ride_id].discard(user_id)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user."""
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)

    async def broadcast_to_ride_room(self, ride_id: int, message: dict):
        """Send message to all users in a ride room."""
        user_ids = self.ride_rooms.get(ride_id, set())
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def broadcast_to_all_drivers(self, message: dict, online_driver_ids: list):
        """Broadcast new ride request to all online drivers."""
        for driver_id in online_driver_ids:
            await self.send_to_user(driver_id, message)


# Single global instance shared across the app
manager = ConnectionManager()