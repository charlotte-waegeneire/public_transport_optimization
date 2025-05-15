"""ARIMA configuration module."""

import os
from pathlib import Path

CONFIG_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
ARIMA_DIR = CONFIG_DIR.parent

ARIMA_CONFIG = {
    "graphs_dir": os.path.join(ARIMA_DIR, "model_performance", "graphs"),
    "params_station_file": os.path.join(CONFIG_DIR, "station_arima_params.json"),
    "p_range": [0, 1, 2],
    "d_range": [0, 1],
    "q_range": [0, 1, 2],
    "default_order": (1, 1, 1),
}


def get_station_params_file(station_id):
    """
    Get the path to a station-specific parameters file.

    Args:
        station_id (int): The station ID

    Returns:
        str: Path to the station parameters file
    """
    station_params_dir = ARIMA_CONFIG["params_dir"]
    station_params_file = os.path.join(station_params_dir, f"station_{station_id}_params.json")
    return station_params_file
