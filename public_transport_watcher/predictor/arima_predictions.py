import json
import os

import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.arima import (
    find_optimal_params,
    get_data_from_db,
    predict_navigo_validations,
)
from public_transport_watcher.predictor.configuration import ARIMA_CONFIG

logger = get_logger()


class ArimaPredictor:
    def __init__(self):
        self.params_file = ARIMA_CONFIG["params_station_file"]
        self.p_range = ARIMA_CONFIG["p_range"]
        self.d_range = ARIMA_CONFIG["d_range"]
        self.q_range = ARIMA_CONFIG["q_range"]
        self._load_all_station_params()

    def _load_all_station_params(self):
        self.station_params = {}
        if os.path.exists(self.params_file):
            try:
                with open(self.params_file, "r") as f:
                    params_dict = json.load(f)

                for station_id, params in params_dict.items():
                    self.station_params[int(station_id)] = tuple(params)

                logger.info(f"Loaded ARIMA parameters for {len(self.station_params)} stations from consolidated file")
            except Exception as e:
                logger.error(f"Error loading consolidated ARIMA parameters: {e}")
        else:
            logger.error("No consolidated ARIMA parameters file found")

    def predict_for_station(self, station_id, optimize_params=False):
        try:
            logger.info(f"Starting prediction for station {station_id}")
            data_raw = get_data_from_db(station_id)

            if data_raw.empty:
                logger.error(f"No data available for station {station_id}")
                return None, 0

            if str(station_id) in self.station_params:
                self.station_params[station_id] = self.station_params[str(station_id)]

            if optimize_params or station_id not in self.station_params:
                arima_params = find_optimal_params(
                    station_id,
                    data_raw,
                    self.p_range,
                    self.d_range,
                    self.q_range,
                    self.station_params,
                    self.params_file,
                )
            else:
                arima_params = self.station_params[station_id]

            logger.info(f"Using ARIMA{arima_params} model for station {station_id}")

            predictions, total = predict_navigo_validations(data_raw, station_id, arima_params)

            logger.info(f"Prediction completed successfully for station {station_id}")
            return predictions, total

        except Exception as e:
            logger.error(f"Error during prediction for station {station_id}: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None, 0

    def predict_for_all_stations(self, optimize_params=False):
        logger.info("Starting predictions for all stations")

        try:
            station_ids = [int(station_id) for station_id in self.station_params.keys()]
            if not station_ids:
                logger.error("No stations found in the parameters file")
                return pd.DataFrame()

            logger.info(f"Found {len(station_ids)} stations to process")
            all_predictions = pd.DataFrame(columns=["station_id", "predictions", "total"])

            for station_id in station_ids:
                logger.info(f"Processing station {station_id}")
                predictions, total = self.predict_for_station(station_id, optimize_params)

                if predictions is not None:
                    new_row = pd.DataFrame([{"station_id": station_id, "predictions": predictions, "total": total}])
                    all_predictions = pd.concat([all_predictions, new_row], ignore_index=True)
                else:
                    logger.warning(f"Could not generate predictions for station {station_id}")

            logger.info(f"Successfully generated predictions for {all_predictions.shape[0]} stations")
            return all_predictions

        except Exception as e:
            logger.error(f"Error during prediction for all stations: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return pd.DataFrame()


if __name__ == "__main__":
    logger = get_logger()

    arima_predictor = ArimaPredictor()
    station_id = 70671
    predictions, total = arima_predictor.predict_for_station(station_id=station_id)
    logger.info(f"Predictions for station {station_id}: {predictions}")
    logger.info(f"Total predicted validations: {total}")

    all_predictions = arima_predictor.predict_for_all_stations()  # needs to be scheduled
