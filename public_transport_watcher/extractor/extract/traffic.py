import json
import os
import requests
import pandas as pd
from datetime import datetime
import time

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_datalake_file

logger = get_logger()

BASE_URL = "https://prim.iledefrance-mobilites.fr/marketplace/estimated-timetable"
TRAFFIC_API_KEY = os.getenv("TRAFFIC_API_KEY")

HEADERS = {"apikey": TRAFFIC_API_KEY, "Accept": "application/json"}


def _fetch_api_data(line_id: str) -> dict:
    """
    Fetches data from the API for a given line ID.
    """
    params = {"LineRef": line_id}
    try:
        response = requests.get(BASE_URL, headers=HEADERS, params=params)

        if response.status_code == 400:
            logger.warning(
                f"Warning on line {line_id}: {response.status_code}, {response.text}"
            )
            return None

        if response.status_code != 200:
            logger.error(
                f"Error on line {line_id}: {response.status_code}, {response.text}"
            )
            return None

        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error on line {line_id}: {e}")
        return None


def _extract_traffic_data(data: dict) -> pd.DataFrame:
    """
    Processes API data for a single line into a DataFrame and cleans the line_ref.
    """
    line_names, line_refs, statuses, destinations, arrival_times = [], [], [], [], []

    if data is None:
        return pd.DataFrame()

    for delivery in (
        data.get("Siri", {})
        .get("ServiceDelivery", {})
        .get("EstimatedTimetableDelivery", [])
    ):
        for journey in delivery.get("EstimatedJourneyVersionFrame", []):
            for vehicle in journey.get("EstimatedVehicleJourney", []):
                line_ref = vehicle.get("LineRef", {}).get("value", "Inconnu")
                line_name = vehicle.get("PublishedLineName", [{}])[0].get(
                    "value", "Inconnu"
                )

                for call in vehicle.get("EstimatedCalls", {}).get("EstimatedCall", []):
                    arrival_status = call.get("ArrivalStatus", "Inconnu")
                    destination_display = call.get("DestinationDisplay", [])
                    station_name = (
                        destination_display[0].get("value", "Inconnu")
                        if destination_display
                        else "Inconnu"
                    )

                    expected_arrival_time = call.get("ExpectedArrivalTime", "Inconnu")

                    if expected_arrival_time != "Inconnu":
                        try:
                            dt = datetime.fromisoformat(
                                expected_arrival_time.replace("Z", "+00:00")
                            )
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
    """
    Loads lines data from the CSV file.
    """
    try:
        file_path = next(
            f
            for f in get_datalake_file("schedule", 2025, "")
            if "referentiel-des-lignes.csv" in f
        )
        return pd.read_csv(file_path, sep=";")
    except (StopIteration, FileNotFoundError) as e:
        logger.error(f"Failed to load row data : {e}")
        return pd.DataFrame()


def process_traffic_data() -> pd.DataFrame:
    """
    Processes traffic data for rail lines and merges with lines data.
    """
    lines_df = _extract_lines_data()
    if lines_df.empty:
        return pd.DataFrame()

    rail_lines_df = lines_df[lines_df["TransportMode"] == "rail"]
    rail_line_ids = [
        "STIF:Line::" + line_id + ":" for line_id in rail_lines_df["ID_Line"].tolist()
    ]

    all_line_data = [
        _extract_traffic_data(_fetch_api_data(line_id))
        for line_id in rail_line_ids
        if _fetch_api_data(line_id)
    ]
    traffic_df = (
        pd.concat(all_line_data, ignore_index=True) if all_line_data else pd.DataFrame()
    )

    if traffic_df.empty:
        return pd.DataFrame()

    traffic_df = traffic_df.merge(
        rail_lines_df,
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
