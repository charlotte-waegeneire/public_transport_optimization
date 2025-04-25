from dotenv import load_dotenv
import requests

from public_transport_watcher.logging_config import get_logger

logger = get_logger()

load_dotenv()


def fetch_generic_api_data(url, headers=None, params=None, method="GET"):
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, params=params)
        else:
            raise ValueError("HTTP method not supported.")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error during API request: {e}")
        return None
