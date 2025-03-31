import logging
import sys
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "transport_watcher.log")

os.makedirs(LOG_DIR, exist_ok=True)

# Configure logger once at module level
logger = logging.getLogger("public_transport_watcher")
if not logger.handlers:  # Only configure if not already done
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10485760, backupCount=5)
    file_handler.setLevel(logging.DEBUG)

    console_format = logging.Formatter("%(levelname)s - %(message)s")
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

def get_logger():
    """Get the pre-configured logger."""
    return logger