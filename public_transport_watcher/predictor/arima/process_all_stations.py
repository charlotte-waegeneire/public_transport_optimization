import argparse
import json
import os

import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.configuration.prediction_config import PREDICTION_CONFIG
from public_transport_watcher.utils import get_engine

logger = get_logger()

PARAMS_FILE = PREDICTION_CONFIG["arima"]["params_station_file"]


def get_all_stations_with_traffic():
    """
    Retrieves a list of all station IDs that have traffic data in the database.

    Returns:
        list: List of station IDs
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    stations_query = """
    SELECT DISTINCT s.id, s.name
    FROM transport.station s
    JOIN transport.traffic t ON s.id = t.station_id
    """
    stations_df = pd.read_sql(stations_query, engine)
    session.close()

    if stations_df.empty:
        logger.error("No stations with traffic data found in the database")
        return []

    logger.info(f"Found {len(stations_df)} stations with traffic data")
    return stations_df["id"].tolist()


def load_existing_params():
    """
    Load existing ARIMA parameters from the JSON file.

    Returns:
        dict: Dictionary of station_id -> params
    """
    if os.path.exists(PARAMS_FILE):
        try:
            with open(PARAMS_FILE, "r") as f:
                station_params = json.load(f)
            logger.info(f"Loaded parameters for {len(station_params)} stations from {PARAMS_FILE}")
            return station_params
        except Exception as e:
            logger.error(f"Error loading station parameters from {PARAMS_FILE}: {e}")

    return {}


def save_params(station_params):
    """
    Save the ARIMA parameters to the JSON file.

    Args:
        station_params (dict): Dictionary of station_id -> params
    """
    try:
        os.makedirs(os.path.dirname(PARAMS_FILE), exist_ok=True)

        with open(PARAMS_FILE, "w") as f:
            json.dump(station_params, f, indent=2)
        logger.info(f"Saved parameters for {len(station_params)} stations to {PARAMS_FILE}")
    except Exception as e:
        logger.error(f"Error saving station parameters to {PARAMS_FILE}: {e}")


def run_all_stations(optimize=False, limit=None):
    """
    Run ARIMA predictions for all stations.

    Args:
        optimize (bool): If True, re-optimize parameters for each station
        limit (int): Maximum number of stations to process
    """
    from public_transport_watcher.predictor.arima_predictions import ArimaPredictor

    predictor = ArimaPredictor()

    station_ids = get_all_stations_with_traffic()

    if limit and len(station_ids) > limit:
        logger.info(f"Limiting to {limit} stations out of {len(station_ids)}")
        station_ids = station_ids[:limit]

    station_params = load_existing_params()

    results = {}

    for i, station_id in enumerate(station_ids, 1):
        logger.info(f"Processing station {station_id} ({i}/{len(station_ids)})")

        try:
            predictions, total = predictor.predict_for_station(station_id, optimize_params=optimize)

            if predictions is not None:
                results[station_id] = {
                    "total_validations": int(total),
                    "arima_params": predictor.station_params.get(station_id),
                }

                if station_id in predictor.station_params:
                    station_params[str(station_id)] = predictor.station_params[station_id]

        except Exception as e:
            logger.error(f"Error processing station {station_id}: {e}")

    # Save all parameters
    save_params(station_params)

    logger.info(f"Completed predictions for {len(results)} stations")

    logger.info("=== Prediction Summary ===")
    for station_id, data in results.items():
        logger.info(
            f"Station {station_id}: {data['total_validations']} validations predicted (ARIMA params: {data['arima_params']})"
        )

    return results


def main():
    parser = argparse.ArgumentParser(description="Run ARIMA predictions for all stations")
    parser.add_argument("--optimize", action="store_true", help="Re-optimize ARIMA parameters for each station")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of stations to process")

    args = parser.parse_args()

    logger.info("Starting ARIMA predictions for all stations")
    logger.info(f"Optimize parameters: {args.optimize}")
    if args.limit:
        logger.info(f"Limiting to {args.limit} stations")
    logger.info(f"Using parameters file: {PARAMS_FILE}")

    run_all_stations(optimize=args.optimize, limit=args.limit)

    logger.info("ARIMA predictions completed")
