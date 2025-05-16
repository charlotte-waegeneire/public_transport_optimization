from datetime import datetime
from functools import wraps
import json
import logging
import os
import time
import uuid

from flask import request


# Configure API logger to write to a separate file
def setup_api_logger():
    """Set up the API logger to write to a separate file."""
    # Get logs root directory from environment variable
    logs_root = os.getenv("LOGS_ROOT", "logs")

    # Create the api logs directory if it doesn't exist
    api_log_dir = os.path.join(logs_root, "api")
    os.makedirs(api_log_dir, exist_ok=True)

    # Set up the logger
    api_logger = logging.getLogger("api_logger")
    api_logger.setLevel(logging.INFO)

    # Remove existing handlers if any
    for handler in api_logger.handlers[:]:
        api_logger.removeHandler(handler)

    # Create a file handler for the API logs
    log_file = os.path.join(api_log_dir, "api_logs.json")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    # Add the handler to the logger
    api_logger.addHandler(file_handler)

    # Prevent propagation to root logger
    api_logger.propagate = False

    # Set Flask's werkzeug logger to only show errors
    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    return api_logger


# Initialize the API logger
api_logger = setup_api_logger()


def generate_id():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def log_request(f):
    """Decorator to log API requests with consistent structure for DB ingestion."""

    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()

        # Execute the actual endpoint function
        response = f(*args, **kwargs)

        # Calculate execution time in milliseconds
        execution_time = (time.time() - start_time) * 1000

        # Determine status code and response content
        if isinstance(response, tuple):
            response_content = response[0]
            status_code = response[1]
        else:
            response_content = response
            status_code = 200

        # Generate IDs for log, response, and parameters
        log_id = generate_id()
        response_id = generate_id() if status_code != 204 else None

        # Build list of parameter dicts with unique IDs
        params = []
        # Query params
        for name, value in request.args.items():
            params.append({"id": generate_id(), "name": name, "value": value})

        # JSON body params if any
        if request.is_json:
            try:
                json_body = request.get_json()
                if isinstance(json_body, dict):
                    for name, value in json_body.items():
                        params.append({"id": generate_id(), "name": name, "value": str(value)})
            except Exception:
                # Ignore JSON parse errors, just skip body params
                pass

        # Compose the log entry in the expected JSON structure
        log_entry = {
            "log": {
                "id": log_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ip_address": request.remote_addr or "",
                "user_agent": request.user_agent.string or "",
                "execution_time": execution_time,
                "request_path": request.path,
                # Instead of generating method_id/status_id here, just store method name and status code
                # DB will resolve IDs via lookup queries in the insert statement
            },
            "method": {"name": request.method},
            "status": {
                "code": status_code,
            },
            "parameters": params,
            "response": {
                "id": response_id,
                "content": str(response_content) if response_id else None,
            },
        }

        # Log as JSON string
        api_logger.info(json.dumps(log_entry))

        return response

    return decorated
