import logging

from public_transport_watcher.api.routes import app
from public_transport_watcher.logging_config import get_logger

# Suppress Flask development server warnings
logging.getLogger("werkzeug").setLevel(logging.ERROR)

logger = get_logger()

if __name__ == "__main__":
    logger.info("Starting the Public Transport API...")
    print("Starting the Public Transport API...")
    app.run(debug=True, host="0.0.0.0", port=5001)
