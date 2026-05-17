import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("bikeride.requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every incoming request and outgoing response.
    Tracks response time in milliseconds.
    Skips WebSocket connections.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip WebSocket connections
        if request.url.path.startswith("/ws"):
            return await call_next(request)

        start_time = time.time()

        # Log incoming request
        logger.info(
            f"REQUEST  | {request.method} {request.url.path} "
            f"| IP: {request.client.host}"
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"RESPONSE | {request.method} {request.url.path} "
                f"| Status: {response.status_code} "
                f"| Duration: {duration_ms}ms"
            )

            return response

        except Exception as exc:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(
                f"ERROR    | {request.method} {request.url.path} "
                f"| Duration: {duration_ms}ms | Error: {exc}",
                exc_info=True
            )
            raise