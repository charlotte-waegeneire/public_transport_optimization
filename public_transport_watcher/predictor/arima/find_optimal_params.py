import json
import math
import os

import pandas as pd
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.arima.model import ARIMA

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.arima.preprocess_data import preprocess_data
from public_transport_watcher.predictor.configuration import ARIMA_CONFIG, get_station_params_file

logger = get_logger()


def _load_station_params(station_id, params_file):
    if os.path.exists(params_file):
        try:
            with open(params_file, "r") as f:
                params_dict = json.load(f)

            if str(station_id) in params_dict:
                params = tuple(params_dict[str(station_id)])
                logger.info(f"ARIMA parameters loaded for station {station_id} from consolidated file: {params}")
                return params
        except Exception as e:
            logger.error(f"Error loading ARIMA parameters from consolidated file for station {station_id}: {e}")

    station_params_file = get_station_params_file(station_id)

    if os.path.exists(station_params_file):
        try:
            with open(station_params_file, "r") as f:
                params = json.load(f)
            logger.info(f"ARIMA parameters loaded for station {station_id} from individual file: {params}")
            return tuple(params)
        except Exception as e:
            logger.error(f"Error loading ARIMA parameters for station {station_id}: {e}")

    return None


def _save_station_params(station_id, params, station_params, params_file):
    station_params[station_id] = params

    # Save to consolidated file
    params_dict = {str(station_id): list(params) for station_id, params in station_params.items()}
    try:
        with open(params_file, "w") as f:
            json.dump(params_dict, f, indent=2)
        logger.info(f"Saved consolidated ARIMA parameters for {len(station_params)} stations")
    except Exception as e:
        logger.error(f"Error saving consolidated ARIMA parameters: {e}")

    # Save to individual file
    station_params_file = get_station_params_file(station_id)
    try:
        with open(station_params_file, "w") as f:
            json.dump(params, f)
        logger.info(f"ARIMA parameters saved for station {station_id}: {params}")
    except Exception as e:
        logger.error(f"Error saving ARIMA parameters for station {station_id}: {e}")


def find_optimal_params(
    station_id: int,
    df: pd.DataFrame,
    p_range: list,
    d_range: list,
    q_range: list,
    station_params: dict,
    params_file: str,
    train_ratio: float = 0.8,
) -> tuple:
    """
    Find optimal ARIMA parameters for a station.

    Parameters
    ----------
    station_id : int
        Station ID
    df : pd.DataFrame
        Station data
    p_range : list
        Range of p values to try
    d_range : list
        Range of d values to try
    q_range : list
        Range of q values to try
    station_params : dict
        Dictionary of existing parameters
    params_file : str
        Path to consolidated parameters file
    train_ratio : float
        Ratio of data to use for training

    Returns
    -------
    tuple
        Optimal ARIMA parameters (p, d, q)
    """
    if station_id in station_params:
        return station_params[station_id]

    params = _load_station_params(station_id, params_file)
    if params:
        station_params[station_id] = params
        return params

    data_df = preprocess_data(df, station_id)
    time_series = data_df["validations"].copy()

    train_size = int(len(time_series) * train_ratio)
    train, test = time_series[:train_size], time_series[train_size:]

    best_score = float("inf")
    best_params = ARIMA_CONFIG["default_order"]

    try:
        for p in p_range:
            for d in d_range:
                for q in q_range:
                    # Skip the (0,0,0) model which doesn't make sense
                    if p == 0 and d == 0 and q == 0:
                        continue

                    try:
                        model = ARIMA(train, order=(p, d, q))
                        model_fit = model.fit()
                        predictions = model_fit.forecast(steps=len(test))
                        mse = mean_squared_error(test, predictions)
                        rmse = math.sqrt(mse)

                        if rmse < best_score:
                            best_score = rmse
                            best_params = (p, d, q)

                    except Exception as e:
                        logger.debug(f"Error with ARIMA({p},{d},{q}) for station {station_id}: {e}")
                        continue

        logger.info(f"Best ARIMA parameters for station {station_id}: {best_params} (RMSE: {best_score:.2f})")

        station_params[station_id] = best_params
        _save_station_params(station_id, best_params, station_params, params_file)

    except Exception as e:
        logger.error(f"Error finding optimal parameters for station {station_id}: {e}")

    return best_params
