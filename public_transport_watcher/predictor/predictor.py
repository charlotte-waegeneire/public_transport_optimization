import time

import schedule

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.arima_predictions import ArimaPredictor
from public_transport_watcher.predictor.graph_builder import GraphBuilder

logger = get_logger()


class Predictor:
    def __init__(self, build_graph_if_missing=True):
        self.arima_predictor = ArimaPredictor()
        self.graph_builder = GraphBuilder()

        try:
            self.graph = self.graph_builder.load_graph()
            logger.info("Successfully loaded existing transport network graph")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not load graph: {e}")
            if build_graph_if_missing:
                logger.info("Building new transport network graph")
                self.graph_builder.save_graph()
                self.graph = self.graph_builder.load_graph()
                logger.info("Successfully built and loaded new transport network graph")
            else:
                logger.error("Transport network graph not available could not build it")
                raise ValueError

    def predict_and_update_graph(self, optimize_arima_params=False):
        try:
            logger.info("Starting hourly prediction and graph update")

            predictions_df = self.arima_predictor.predict_for_all_stations(optimize_params=optimize_arima_params)

            if predictions_df.empty:
                logger.error("Failed to generate predictions for stations")
                return False

            logger.info(f"Generated predictions for {predictions_df.shape[0]} stations")

            self.graph = self.graph_builder.adjust_station_weights(predictions_df)
            logger.info("Successfully updated graph weights based on predictions")

            self.graph_builder.save_graph()
            logger.info("Successfully saved updated graph")

            return True

        except Exception as e:
            logger.error(f"Error during prediction and graph update: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def find_optimal_route(self, start_coords, end_coords):
        try:
            logger.info(f"Finding optimal route from {start_coords} to {end_coords}")
            route_info = self.graph_builder.find_optimal_route(start_coords, end_coords)
            logger.info(f"Found optimal route with total time: {route_info['total_time']} minutes")
            return route_info
        except Exception as e:
            logger.error(f"Error finding optimal route: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def schedule_hourly_updates(self):
        logger.info("Setting up hourly prediction and graph update schedule")
        schedule.every().hour.do(self.predict_and_update_graph)

        logger.info("Hourly prediction schedule is set")
        return True

    def run_scheduled_tasks(self, run_forever=True):
        logger.info("Starting scheduled task runner")

        self.predict_and_update_graph()

        if run_forever:
            logger.info("Entering scheduled task loop")
            while True:
                schedule.run_pending()
                time.sleep(60)
        else:
            schedule.run_pending()
            logger.info("Completed one-time run of scheduled tasks")

    def optimize_all_arima_models(self):
        logger.info("Starting optimization of ARIMA parameters for all stations")
        predictions_df = self.arima_predictor.predict_for_all_stations(optimize_params=False)
        logger.info(f"Completed optimization for {predictions_df.shape[0]} stations")
        return predictions_df


if __name__ == "__main__":
    predictor = Predictor()

    predictor.predict_and_update_graph()

    start_coords = (48.855089551123996, 2.394484471898831)
    end_coords = (48.8272425814562, 2.3787827042461736)
    route = predictor.find_optimal_route(start_coords, end_coords)

    if route:
        print("Optimal route found:")
        print(f"- Total time: {route['total_time']} minutes")
        print(f"- Transit time: {route['network_time']} minutes")
        print(f"- Walking time: {route['walking_duration']} minutes")
        print(f"- Walking distance: {route['walking_distance']} meters")
        print(f"- Path: {route['optimal_path']}")

    predictor.schedule_hourly_updates()
    predictor.run_scheduled_tasks()
