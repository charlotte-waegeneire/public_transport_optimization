from datetime import datetime
from functools import wraps
import json
import logging
import os
import time
import uuid

from flask import request


def setup_api_logger():
    """Set up the API logger to write to a separate file."""
    logs_root = os.getenv("LOGS_ROOT", "logs")

    api_log_dir = os.path.join(logs_root, "api")
    os.makedirs(api_log_dir, exist_ok=True)

    api_logger = logging.getLogger("api_logger")
    api_logger.setLevel(logging.INFO)

    for handler in api_logger.handlers[:]:
        api_logger.removeHandler(handler)

    log_file = os.path.join(api_log_dir, "api_logs.json")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)

    api_logger.addHandler(file_handler)

    api_logger.propagate = False

    logging.getLogger("werkzeug").setLevel(logging.ERROR)

    return api_logger


api_logger = setup_api_logger()


def generate_id():
    """Generate a unique UUID string."""
    return str(uuid.uuid4())


def log_request(f):
    """Decorator to log API requests with consistent structure for DB ingestion."""

    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()

        response = f(*args, **kwargs)

        execution_time = (time.time() - start_time) * 1000

        if isinstance(response, tuple):
            response_content = response[0]
            status_code = response[1]
        else:
            response_content = response
            status_code = 200

        log_id = generate_id()

        params = []
        for name, value in request.args.items():
            params.append({"id": generate_id(), "name": name, "value": value})

        if request.is_json:
            try:
                json_body = request.get_json()
                if isinstance(json_body, dict):
                    for name, value in json_body.items():
                        params.append({"id": generate_id(), "name": name, "value": str(value)})
            except Exception:
                pass

        log_entry = {
            "log": {
                "id": log_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ip_address": request.remote_addr or "",
                "user_agent": request.user_agent.string or "",
                "execution_time": execution_time,
                "request_path": request.path,
                "response": str(response_content) if status_code != 204 else None,
            },
            "method": {"name": request.method},
            "status": {
                "code": status_code,
            },
            "parameters": params,
        }

        api_logger.info(json.dumps(log_entry))

        return response

    return decorated
