from datetime import datetime, timedelta
import os
import time
import pickle

import pandas as pd
import requests

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/estimated-timetable"
TRAFFIC_API_KEY = os.getenv("TRAFFIC_API_KEY")

HEADERS = {"apikey": TRAFFIC_API_KEY, "Accept": "application/json"}

DESIRED_TRANSPORT_MODES = ["rail", "metro", "tram"]

CACHE_FILE = "traffic_cache.pkl"
CACHE_DURATION_MINUTES = 5


def _fetch_api_data(line_id: str) -> dict:
    params = {"LineRef": line_id}
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 400:
            logger.warning(f"Warning on line {line_id}: {response.status_code}, {response.text}")
            return None

        if response.status_code != 200:
            logger.error(f"Error on line {line_id}: {response.status_code}, {response.text}")
            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error on line {line_id}: {e}")
        return None


def _extract_traffic_data(data: dict) -> pd.DataFrame:
    line_names, line_refs, statuses, destinations, arrival_times = [], [], [], [], []

    if data is None:
        return pd.DataFrame()

    for delivery in data.get("Siri", {}).get("ServiceDelivery", {}).get("EstimatedTimetableDelivery", []):
        for journey in delivery.get("EstimatedJourneyVersionFrame", []):
            for vehicle in journey.get("EstimatedVehicleJourney", []):
                line_ref = vehicle.get("LineRef", {}).get("value", "Inconnu")
                line_name = vehicle.get("PublishedLineName", [{}])[0].get("value", "Inconnu")

                for call in vehicle.get("EstimatedCalls", {}).get("EstimatedCall", []):
                    arrival_status = call.get("ArrivalStatus", "Inconnu")
                    destination_display = call.get("DestinationDisplay", [])
                    station_name = destination_display[0].get("value", "Inconnu") if destination_display else "Inconnu"

                    expected_arrival_time = call.get("ExpectedArrivalTime", "Inconnu")

                    if expected_arrival_time != "Inconnu":
                        try:
                            dt = datetime.fromisoformat(expected_arrival_time.replace("Z", "+00:00"))
                            expected_arrival_time = dt.strftime("%H:%M")
                        except ValueError:
                            pass

                    line_names.append(line_name)
                    line_refs.append(line_ref)
                    statuses.append(arrival_status)
                    destinations.append(station_name)
                    arrival_times.append(expected_arrival_time)

    df = pd.DataFrame(
        {
            "line_name": line_names,
            "line_ref": line_refs,
            "statut": statuses,
            "destination": destinations,
            "expected_arrival_time": arrival_times,
        }
    )

    if not df.empty:
        df["line_ref"] = df["line_ref"].str.replace(r"[^0-9C]", "", regex=True)

    return df


def _extract_lines_data() -> pd.DataFrame:
    """Extracts lines data from the referential CSV file"""
    try:
        file_path = next(f for f in get_datalake_file("schedule", 2025, "") if "referentiel-des-lignes.csv" in f)
        return pd.read_csv(file_path, sep=";")
    except (StopIteration, FileNotFoundError) as e:
        logger.error(f"Failed to load row data : {e}")
        return pd.DataFrame()


def _is_cache_valid() -> bool:
    """hecks if cache exists and is still valid"""
    if not os.path.exists(CACHE_FILE):
        return False

    try:
        with open(CACHE_FILE, 'rb') as f:
            cached_data = pickle.load(f)

        cache_time = cached_data['timestamp']
        time_diff = datetime.now() - cache_time

        return time_diff < timedelta(minutes=CACHE_DURATION_MINUTES)
    except:
        return False


def _load_from_cache() -> pd.DataFrame:
    """Loads data from cache"""
    try:
        with open(CACHE_FILE, 'rb') as f:
            cached_data = pickle.load(f)

        logger.info(f"Données chargées depuis le cache (créé à {cached_data['timestamp'].strftime('%H:%M:%S')})")
        return cached_data['data']
    except Exception as e:
        logger.error(f"Erreur lors du chargement du cache: {e}")
        return pd.DataFrame()


def _save_to_cache(data: pd.DataFrame) -> None:
    """Saves data to cache"""
    try:
        cache_data = {
            'timestamp': datetime.now(),
            'data': data
        }

        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(cache_data, f)

        logger.info(f"Données sauvegardées en cache ({len(data)} enregistrements)")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du cache: {e}")


def _fetch_fresh_data() -> pd.DataFrame:
    """Retrieves fresh data from the API"""
    lines_df = _extract_lines_data()
    if lines_df.empty:
        return pd.DataFrame()

    filtered_lines_df = lines_df[
        lines_df["TransportMode"].isin(DESIRED_TRANSPORT_MODES)
    ].copy()

    if "NetworkName" in filtered_lines_df.columns:
        filtered_lines_df = filtered_lines_df[
            filtered_lines_df["NetworkName"].isna() |
            ~filtered_lines_df["NetworkName"].str.contains("TER", case=False, na=False)
            ]

    line_ids = ["STIF:Line::" + line_id + ":" for line_id in filtered_lines_df["ID_Line"].tolist()]

    all_line_data = []
    for i, line_id in enumerate(line_ids):
        if i > 0 and i % 5 == 0:
            time.sleep(1)

        api_data = _fetch_api_data(line_id)
        if api_data:
            traffic_data = _extract_traffic_data(api_data)
            if not traffic_data.empty:
                all_line_data.append(traffic_data)

    traffic_df = pd.concat(all_line_data, ignore_index=True) if all_line_data else pd.DataFrame()

    if traffic_df.empty:
        return pd.DataFrame()

    traffic_df = traffic_df.merge(
        filtered_lines_df,
        left_on="line_ref",
        right_on="ID_Line",
        how="left",
        suffixes=("_df", "_lines"),
    )

    return traffic_df[
        [
            "line_name",
            "line_ref",
            "statut",
            "destination",
            "expected_arrival_time",
            "TransportMode",
            "OperatorName",
            "NetworkName",
            "ShortName_GroupOfLines",
        ]
    ].rename(
        columns={
            "TransportMode": "transport_mode",
            "OperatorName": "operator_name",
            "NetworkName": "network_name",
            "ShortName_GroupOfLines": "full_line_name",
        }
    )


def extract_traffic_data() -> pd.DataFrame:
    """
    Main function that manages cache and retrieves traffic data
    """
    if _is_cache_valid():
        return _load_from_cache()

    logger.info("Cache expiré ou inexistant, récupération de nouvelles données...")
    fresh_data = _fetch_fresh_data()

    if not fresh_data.empty:
        _save_to_cache(fresh_data)

    return fresh_data
