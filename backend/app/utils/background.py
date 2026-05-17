import asyncio
from app.services.redis_service import cleanup_stale_drivers
from app.websocket.connection_manager import manager

async def cleanup_stale_drivers_task():
    """
    Runs every 5 minutes.
    Removes drivers from online_drivers set
    if their TTL key has expired in Redis.
    """
    while True:
        await asyncio.sleep(300)  # every 5 minutes
        try:
            await cleanup_stale_drivers()
            print("Background: stale driver cleanup complete")
        except Exception as e:
            print(f"Background: cleanup error: {e}")

async def cleanup_empty_rooms_task():
    """
    Runs every 10 minutes.
    Removes empty ride rooms from connection manager.
    """
    while True:
        await asyncio.sleep(600)  # every 10 minutes
        try:
            empty_rooms = [
                ride_id
                for ride_id, users in manager.ride_rooms.items()
                if not users
            ]
            for ride_id in empty_rooms:
                del manager.ride_rooms[ride_id]

            if empty_rooms:
                print(f"Background: removed {len(empty_rooms)} empty ride rooms")
        except Exception as e:
            print(f"Background: room cleanup error: {e}")

async def driver_heartbeat_check_task():
    """
    Runs every 2 minutes.
    Checks all WebSocket-connected drivers are still
    actually online in Redis. Cleans up ghost connections.
    """
    while True:
        await asyncio.sleep(120)  # every 2 minutes
        try:
            connected_user_ids = list(manager.active_connections.keys())
            print(f"Background: {len(connected_user_ids)} active WebSocket connections")
        except Exception as e:
            print(f"Background: heartbeat error: {e}")