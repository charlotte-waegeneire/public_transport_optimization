import os

from public_transport_watcher.logging_config import logger
from public_transport_watcher.predictor.arima import get_data_from_db, predict_validations
from public_transport_watcher.predictor.arima.visualize_predictions import visualize_predictions


class ArimaPredictor:
    def __init__(self, graphs_dir="graphs"):
        self.graphs_dir = graphs_dir
        os.makedirs(graphs_dir, exist_ok=True)
        logger.info(f"ArimaPredictor initialized. Graphs stored in: {graphs_dir}")

    def predict_for_station(self, station_id):
        return self._predict_station_validations(station_id)

    def _predict_station_validations(self, station_id):
        try:
            logger.info(f"Starting prediction for station {station_id}")
            df = get_data_from_db(station_id)

            if df.empty:
                logger.error(f"No data available for station {station_id}")
                return None, 0

            from public_transport_watcher.predictor.arima.preprocess_data import preprocess_data

            data_df = preprocess_data(df, station_id)

            predictions, total = predict_validations(df, station_id)

            if predictions is not None:
                from datetime import datetime

                current_time = datetime.now()

                hourly_avg = self._calculate_hourly_profile(data_df, current_time)

                graph_path = visualize_predictions(
                    station_id=station_id,
                    hourly_avg=hourly_avg,
                    forecast_df=predictions,
                    current_time=current_time,
                    data_df=data_df,
                    save_dir=self.graphs_dir,
                )
                logger.info(f"Prediction graph saved: {graph_path}")

            logger.info(f"Prediction completed successfully for station {station_id}")
            return predictions, total

        except Exception as e:
            logger.error(f"Error during prediction for station {station_id}: {str(e)}")
            return None, 0

    def _calculate_hourly_profile(self, data_df, current_time):
        import calendar
        import pandas as pd

        current_month = current_time.month
        current_day_of_week = current_time.weekday()

        similar_hours = data_df[(data_df["month"] == current_month) & (data_df["day_of_week"] == current_day_of_week)]

        if not similar_hours.empty:
            hourly_avg = similar_hours.groupby("hour")["validations"].mean()
        else:
            hourly_avg = pd.Series(dtype=float)

        return hourly_avg


if __name__ == "__main__":
    from public_transport_watcher.logging_config import get_logger

    logger = get_logger()

    arima_predictor = ArimaPredictor()
    station_id = 70671
    predictions, total = arima_predictor.predict_for_station(station_id=station_id)
    logger.info(f"Predictions for station {station_id}: {predictions}")
    logger.info(f"Total predicted validations: {total}")
