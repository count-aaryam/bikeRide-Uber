import asyncio
import logging
from app.services.redis_service import cleanup_stale_drivers
from app.websocket.connection_manager import manager

logger = logging.getLogger("bikeride.background")

async def cleanup_stale_drivers_task():
    while True:
        await asyncio.sleep(300)
        try:
            await cleanup_stale_drivers()
            logger.info("Background: stale driver cleanup complete")
        except Exception as e:
            logger.error(f"Background: cleanup error: {e}", exc_info=True)

async def cleanup_empty_rooms_task():
    while True:
        await asyncio.sleep(600)
        try:
            empty_rooms = [
                ride_id
                for ride_id, users in manager.ride_rooms.items()
                if not users
            ]
            for ride_id in empty_rooms:
                del manager.ride_rooms[ride_id]

            if empty_rooms:
                logger.info(f"Background: removed {len(empty_rooms)} empty ride rooms")
        except Exception as e:
            logger.error(f"Background: room cleanup error: {e}", exc_info=True)

async def driver_heartbeat_check_task():
    while True:
        await asyncio.sleep(120)
        try:
            connected = list(manager.active_connections.keys())
            logger.info(f"Background: {len(connected)} active WebSocket connections")
        except Exception as e:
            logger.error(f"Background: heartbeat error: {e}", exc_info=True)