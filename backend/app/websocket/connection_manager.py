from fastapi import WebSocket
from typing import Dict, Set
import logging

logger = logging.getLogger("bikeride.websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.ride_rooms: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        logger.info(f"WebSocket connected: user_id={user_id}")

    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]

        for ride_id in list(self.ride_rooms.keys()):
            self.ride_rooms[ride_id].discard(user_id)
            if not self.ride_rooms[ride_id]:
                del self.ride_rooms[ride_id]

        logger.info(f"WebSocket disconnected: user_id={user_id}")

    def join_ride_room(self, ride_id: int, user_id: int):
        if ride_id not in self.ride_rooms:
            self.ride_rooms[ride_id] = set()
        self.ride_rooms[ride_id].add(user_id)
        logger.info(f"User {user_id} joined ride room {ride_id}")

    def leave_ride_room(self, ride_id: int, user_id: int):
        if ride_id in self.ride_rooms:
            self.ride_rooms[ride_id].discard(user_id)
            logger.info(f"User {user_id} left ride room {ride_id}")

    async def send_to_user(self, user_id: int, message: dict):
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json(message)
            logger.debug(f"Sent to user {user_id}: {message.get('event')}")

    async def broadcast_to_ride_room(self, ride_id: int, message: dict):
        user_ids = self.ride_rooms.get(ride_id, set())
        logger.info(
            f"Broadcasting '{message.get('event')}' "
            f"to ride room {ride_id}: users={user_ids}"
        )
        for user_id in user_ids:
            await self.send_to_user(user_id, message)

    async def broadcast_to_all_drivers(self, message: dict, online_driver_ids: list):
        logger.info(
            f"Broadcasting '{message.get('event')}' "
            f"to {len(online_driver_ids)} drivers"
        )
        for driver_id in online_driver_ids:
            await self.send_to_user(driver_id, message)

manager = ConnectionManager()