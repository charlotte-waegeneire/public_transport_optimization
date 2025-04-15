import json
from datetime import datetime

import pandas as pd
import requests

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_env_variable

logger = get_logger()

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
_TOKEN = get_env_variable("INFOCLIMAT_API_KEY")
_URL_BASE = "https://www.infoclimat.fr/opendata/?version=2&method=get&format=json&stations[]={station}&start={start_date}&token={token}"


def _fetch_weather_data(url):
    try:
        headers = _HEADERS
        response = requests.get(url, headers=headers)

        if not response.text or not response.text.strip().startswith("{"):
            logger.error(f"The response is not a valid JSON. The response is:\n{response.text}")
            return None

        response.raise_for_status()
        return response.json()

    except json.JSONDecodeError as e:
        logger.error(f"Could not decode the JSON response: {e}")
        logger.error(f"The response is: \n{response.text}")
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP Error while fetching data: {e}")
        return None

    except Exception as e:
        logger.error(f"An error occurred while fetching data: {e}")
        return None


def extract_weather_data(config):
    station = config.get("station", "")
    if not station:
        logger.error("No station provided in the config")
        return None

    now = datetime.now()
    start_date = now.strftime("%Y-%m-%d")
    url = _URL_BASE.format(station=station, start_date=start_date, token=_TOKEN)
    raw_data = _fetch_weather_data(url)
    if not raw_data:
        logger.error("No weather data fetched")
        return None

    weather_df = pd.DataFrame(raw_data["hourly"][station])
    weather_df = weather_df[["dh_utc", "temperature"]]

    weather_df["dh_utc"] = pd.to_datetime(weather_df["dh_utc"])
    weather_df["temperature"] = weather_df["temperature"].astype(float)

    latest_weather_data = weather_df["dh_utc"].max()
    latest_weather_data = weather_df[weather_df["dh_utc"] == latest_weather_data]

    return latest_weather_data
