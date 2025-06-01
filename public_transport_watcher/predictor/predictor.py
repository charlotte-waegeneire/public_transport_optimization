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
            self.base_graph = self.graph_builder.load_graph("base")
            logger.info("Successfully loaded existing base transport network graph")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Could not load base graph: {e}")
            if build_graph_if_missing:
                logger.info("Building new base transport network graph")
                self.graph_builder.save_graph(graph_type="base")
                self.base_graph = self.graph_builder.load_graph("base")
                logger.info("Successfully built and loaded new base transport network graph")
            else:
                logger.error("Base transport network graph not available and could not build it")
                raise ValueError("Base transport network graph not available")

        try:
            self.weighted_graph = self.graph_builder.load_graph("weighted")
            logger.info("Successfully loaded existing weighted transport network graph")
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Weighted graph not available: {e}. Will be created during first prediction update.")
            self.weighted_graph = None

    def predict_and_update_graph(self, optimize_arima_params=False):
        try:
            logger.info("Starting hourly prediction and graph update")

            predictions_df = self.arima_predictor.predict_for_all_stations(optimize_params=optimize_arima_params)

            if predictions_df.empty:
                logger.error("Failed to generate predictions for stations")
                return False

            logger.info(f"Generated predictions for {predictions_df.shape[0]} stations")

            self.weighted_graph = self.graph_builder.update_weighted_graph(predictions_df)
            logger.info("Successfully updated weighted graph based on predictions")

            return True

        except Exception as e:
            logger.error(f"Error during prediction and graph update: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return False

    def find_optimal_route(self, start_coords, end_coords, use_weighted=None):
        try:
            if use_weighted is None:
                use_weighted = self.weighted_graph is not None
            elif use_weighted and self.weighted_graph is None:
                logger.warning("Weighted graph requested but not available. Using base graph.")
                use_weighted = False

            logger.info(
                f"Finding optimal route from {start_coords} to {end_coords} using {'weighted' if use_weighted else 'base'} graph"
            )
            route_info = self.graph_builder.find_optimal_route(start_coords, end_coords, use_weighted=use_weighted)
            logger.info(
                f"Found optimal route with total time: {route_info['total_time']} minutes using {route_info['graph_type']} graph"
            )
            return route_info
        except Exception as e:
            logger.error(f"Error finding optimal route: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def rebuild_base_graph(self):
        try:
            logger.info("Rebuilding base graph from database")
            self.graph_builder.save_graph(graph_type="base")
            self.base_graph = self.graph_builder.load_graph("base")
            logger.info("Successfully rebuilt base graph")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding base graph: {e}")
            return False

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
        predictions_df = self.arima_predictor.predict_for_all_stations(optimize_params=True)
        logger.info(f"Completed optimization for {predictions_df.shape[0]} stations")
        return predictions_df

    def get_graph_info(self):
        """Get information about the current state of both graphs."""
        info = {
            "base_graph_available": self.base_graph is not None,
            "weighted_graph_available": self.weighted_graph is not None,
        }

        if self.base_graph:
            info["base_graph_nodes"] = self.base_graph.number_of_nodes()
            info["base_graph_edges"] = self.base_graph.number_of_edges()

        if self.weighted_graph:
            info["weighted_graph_nodes"] = self.weighted_graph.number_of_nodes()
            info["weighted_graph_edges"] = self.weighted_graph.number_of_edges()

        return info


if __name__ == "__main__":
    predictor = Predictor()

    predictor.predict_and_update_graph()

    start_coords = (48.855089551123996, 2.394484471898831)
    end_coords = (48.8272425814562, 2.3787827042461736)
    base_route = predictor.find_optimal_route(start_coords, end_coords, use_weighted=False)
    weighted_route = predictor.find_optimal_route(start_coords, end_coords, use_weighted=True)

    # save both routes info to a json file each
    import json

    with open("base_route.json", "w") as f:
        json.dump(base_route, f)

    with open("weighted_route.json", "w") as f:
        json.dump(weighted_route, f)

    # predictor.schedule_hourly_updates()
    # predictor.run_scheduled_tasks()
