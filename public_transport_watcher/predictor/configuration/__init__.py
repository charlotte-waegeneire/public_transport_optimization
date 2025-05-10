"""Prediction configuration module."""

from .arima_config import ARIMA_CONFIG, get_station_params_file
from .prediction_config import PREDICTION_CONFIG

__all__ = [
    "PREDICTION_CONFIG",
    "ARIMA_CONFIG",
    "get_station_params_file",
]
