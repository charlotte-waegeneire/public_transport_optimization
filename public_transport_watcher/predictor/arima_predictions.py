import numpy as np

from public_transport_watcher.logging_config import get_logger
import datetime

from public_transport_watcher.predictor.arima.get_data import prepare_data, get_data_from_db
from public_transport_watcher.predictor.arima.model import build_arima_model, predict_traffic

logger = get_logger()


def _calculate_rmse(model_fit, timeseries):
    """
    "Calculates the RMSE between the observed values and those predicted by the ARIMA model (in-sample)."
    """
    try:
        predictions = model_fit.predict(start=0, end=len(timeseries) - 1)
        rmse = np.sqrt(np.mean((predictions - timeseries) ** 2))
        return rmse
    except Exception as e:
        logger.error(f"Error while calculating the RMSE: {e}")
        return None


def run_arima_analysis(station_id=None):
    """
    Executes the complete ARIMA analysis to forecast traffic.

    Args:
        station_id (int, optional): ID of the station for analysis. If None,
                                    uses all stations.

    Returns:
        dict or None: Prediction results or None in case of an error
    """
    try:
        current_time = datetime.datetime.now()
        next_full_hour = current_time.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
        next_hour_end = next_full_hour + datetime.timedelta(hours=1)

        logger.info(f"Generating prediction for: {current_time.strftime('%H:%M')} - {next_hour_end.strftime('%H:%M')}")

        df = get_data_from_db(station_id)
        if df is None or df.empty:
            logger.warning("No data available")
            return None

        timeseries = prepare_data(df, station_id)
        if len(timeseries) < 48:
            logger.warning("Insufficient data (minimum 48 points)")
            return None

        model_fit = build_arima_model(timeseries)

        # Calcul et log de la RMSE
        rmse = _calculate_rmse(model_fit, timeseries)
        if rmse is not None:
            logger.info(f"📉 RMSE (in-sample): {rmse:.2f}")

        forecast_means, conf_ints = predict_traffic(model_fit, timeseries, steps=1)

        next_hour_prediction = int(forecast_means[0])
        next_hour_conf_int = [int(conf_ints[0][0]), int(conf_ints[0][1])]

        logger.info(f"TRAFFIC FORECAST: {current_time.strftime('%H:%M')} - {next_hour_end.strftime('%H:%M')}")
        logger.info(f"▶ Expected validations: {next_hour_prediction}")
        logger.info(f"▶ Confidence interval: [{next_hour_conf_int[0]} - {next_hour_conf_int[1]}]")

        return {
            "model": model_fit,
            "prediction": next_hour_prediction,
            "conf_int": next_hour_conf_int,
            "start_time": current_time,
            "end_time": next_hour_end,
            "station_id": station_id,
        }

    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        import traceback

        traceback.print_exc()
        return None


class ArimaPredictor:
    def predict_for_station(self, station_id):
        """
        Predicts traffic for a specific station.

        Args:
            station_id (int): ID of the station

        Returns:
            dict: Prediction results
        """
        return run_arima_analysis(station_id=station_id)
