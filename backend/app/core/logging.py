import logging
import sys
from datetime import datetime

def setup_logging():
    """
    Configure structured logging for the entire app.
    Replaces all print() statements.
    """
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console output
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Silence noisy third party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger("bikeride")

# Global logger instance
logger = setup_logging()