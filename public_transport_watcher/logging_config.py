import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "transport_watcher.log")

os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("public_transport_watcher")
if not logger.handlers:  # Only configure if not already done
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)

    file_handler = TimedRotatingFileHandler(LOG_FILE, when="midnight", interval=1, backupCount=30)
    file_handler.setLevel(logging.DEBUG)
    file_handler.suffix = "%Y-%m-%d"

    console_format = logging.Formatter("%(levelname)s - %(message)s")
    file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def get_logger():
    """Get the pre-configured logger."""
    return logger
