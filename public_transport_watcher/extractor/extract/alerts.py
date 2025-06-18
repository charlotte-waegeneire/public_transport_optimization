import os

import pandas as pd
import requests

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils.get_cache_utils import is_cache_valid, load_from_cache, save_to_cache

logger = get_logger()

API_URL = "https://prim.iledefrance-mobilites.fr/marketplace/disruptions_bulk/disruptions/v2"
API_KEY = os.getenv("TRAFFIC_API_KEY")
HEADERS = {"apikey": API_KEY, "Accept": "application/json"}


def _get_transport_mode_label(mode):
    """Converts technical mode to French label"""
    mode_mapping = {"LocalTrain": "Transilien", "RapidTransit": "RER", "Metro": "Métro", "Tramway": "Tramway"}
    return mode_mapping.get(mode, mode)


def _get_api_data():
    """Retrieves all data from API"""
    logger.info("🚀 Fetching API data...")

    if not API_KEY:
        logger.error("TRAFFIC_API_KEY not defined")
        return None

    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()

        data = response.json()
        logger.info("✅ Data retrieved successfully")
        return data

    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return None


def _process_api_data(data):
    """Processes API data to create final DataFrame (excluding bus/funicular, grouped by line)"""
    if not data:
        return pd.DataFrame()

    disruptions = data.get("disruptions", [])
    lines = data.get("lines", [])

    logger.info(f"Found {len(disruptions)} disruptions and {len(lines)} lines")

    filtered_lines = []
    excluded_count = 0

    for line in lines:
        mode = line.get("mode", "").strip()
        if mode.lower() in ["bus", "funicular"]:
            excluded_count += 1
            continue
        filtered_lines.append(line)

    logger.info(f"Bus/funicular lines excluded: {excluded_count}")
    logger.info(f"After filtering: {len(filtered_lines)} lines")

    disruptions_dict = {d["id"]: d for d in disruptions}
    lines_data = {}

    for line in filtered_lines:
        short_name = line.get("shortName", "")
        mode = line.get("mode", "")

        mode_label = _get_transport_mode_label(mode)
        line_key = f"{mode}_{short_name}"
        impacted_objects = line.get("impactedObjects", [])

        if impacted_objects:
            disruptions_info = {}

            for obj in impacted_objects:
                obj_name = obj.get("name", "")
                disruption_ids = obj.get("disruptionIds", [])

                for disruption_id in disruption_ids:
                    if disruption_id in disruptions_dict:
                        disruption = disruptions_dict[disruption_id]
                        short_message = disruption.get("shortMessage", "")
                        cause = disruption.get("cause", "")

                        disruption_key = f"{short_message}_{cause}"

                        if disruption_key not in disruptions_info:
                            disruptions_info[disruption_key] = {
                                "short_message": short_message,
                                "cause": cause,
                                "affected_stops": [],
                            }

                        disruptions_info[disruption_key]["affected_stops"].append(obj_name)

            for disruption_key, disruption_info in disruptions_info.items():
                affected_stops = list(set(disruption_info["affected_stops"]))
                filtered_stops = [stop for stop in affected_stops if str(stop).strip() != str(short_name).strip()]

                enhanced_message = disruption_info["short_message"]

                if len(filtered_stops) == 0:
                    impacted_objects_display = "Sur l'ensemble de la ligne"
                else:
                    impacted_objects_display = ", ".join(filtered_stops)

                unique_key = f"{line_key}_{disruption_key}"

                lines_data[unique_key] = {
                    "mode": mode_label,
                    "short_name": short_name,
                    "ligne_complete": f"{mode_label} {short_name}",
                    "impacted_object_name": impacted_objects_display,
                    "short_message": disruption_info["short_message"],
                    "enhanced_message": enhanced_message,
                    "cause": disruption_info["cause"],
                }
        else:
            lines_data[line_key] = {
                "mode": mode_label,
                "short_name": short_name,
                "ligne_complete": f"{mode_label} {short_name}",
                "impacted_object_name": "",
                "short_message": "",
                "enhanced_message": "",
                "cause": "",
            }

    results = list(lines_data.values())
    df = pd.DataFrame(results)

    logger.info(f"✅ Final DataFrame created with {len(df)} records")

    if not df.empty:
        modes_present = df["mode"].unique()
        logger.info(f"Modes present: {list(modes_present)}")

        disrupted_lines = len(df[df["short_message"].str.len() > 0])
        logger.info(f"Lines with disruptions: {disrupted_lines}")

    return df


def extract_traffic_alerts_informations(force_refresh=False):
    """
    Main entry point for extracting alerts data

    Args:
        force_refresh: If True, ignores cache and forces refresh

    Returns:
        pd.DataFrame: DataFrame with transport data without duplicates
    """
    if not force_refresh and is_cache_valid():
        return load_from_cache()

    logger.info("Cache expired or refresh forced, fetching new data...")

    api_data = _get_api_data()

    if not api_data:
        logger.error("Unable to retrieve API data")
        return pd.DataFrame()

    df = _process_api_data(api_data)

    if not df.empty:
        save_to_cache(df)

    return df
