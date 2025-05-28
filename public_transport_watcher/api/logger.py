from datetime import datetime
from functools import wraps
import json
import logging
import os
import time
import uuid

from flask import Response, request


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


def extract_response_content(response, status_code):
    """Extract the actual response content that will be sent to the user."""
    if status_code == 204:
        return None

    # Si c'est un tuple (response, status_code)
    if isinstance(response, tuple):
        actual_response = response[0]
    else:
        actual_response = response

    # Si c'est un objet Response de Flask
    if isinstance(actual_response, Response):
        try:
            # Pour les Response objects, on peut accéder aux données
            if hasattr(actual_response, "get_data"):
                data = actual_response.get_data(as_text=True)
                # Essayer de parser en JSON si possible
                try:
                    return json.loads(data)
                except (json.JSONDecodeError, ValueError):
                    return data
            elif hasattr(actual_response, "data"):
                return (
                    actual_response.data.decode("utf-8")
                    if isinstance(actual_response.data, bytes)
                    else actual_response.data
                )
        except Exception:
            pass

    # Si c'est déjà un dictionnaire (typique pour les API JSON)
    if isinstance(actual_response, dict):
        return actual_response

    # Si c'est une liste
    if isinstance(actual_response, list):
        return actual_response

    # Si c'est une chaîne
    if isinstance(actual_response, str):
        # Essayer de parser en JSON si ça ressemble à du JSON
        try:
            return json.loads(actual_response)
        except (json.JSONDecodeError, ValueError):
            return actual_response

    # Pour tout autre type, convertir en string en dernier recours
    return str(actual_response)


def log_request(f):
    """Decorator to log API requests with consistent structure for DB ingestion."""

    @wraps(f)
    def decorated(*args, **kwargs):
        start_time = time.time()

        response = f(*args, **kwargs)

        execution_time = (time.time() - start_time) * 1000

        if isinstance(response, tuple):
            status_code = response[1] if len(response) > 1 else 200
        else:
            status_code = 200

        response_content = extract_response_content(response, status_code)

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

        elif request.form:
            for name, value in request.form.items():
                params.append({"id": generate_id(), "name": name, "value": value})

        log_entry = {
            "log": {
                "id": log_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "ip_address": request.remote_addr or "",
                "user_agent": request.user_agent.string or "",
                "execution_time": execution_time,
                "request_path": request.path,
                "response": response_content,
            },
            "method": {"name": request.method},
            "status": {
                "code": status_code,
            },
            "parameters": params,
        }

        api_logger.info(json.dumps(log_entry, ensure_ascii=False, default=str))

        return response

    return decorated
