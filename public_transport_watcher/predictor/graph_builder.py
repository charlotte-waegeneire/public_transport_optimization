import pickle

import pandas as pd

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.predictor.configuration import PREDICTION_CONFIG
from public_transport_watcher.predictor.graph import (
    adjust_station_weights,
    calculate_travel_time,
    create_transport_network,
    find_nearest_station_with_walk,
    find_optimal_route,
    visualize_network,
)
from public_transport_watcher.utils import get_engine

logger = get_logger()


class GraphBuilder:
    def __init__(self):
        self.prediction_config = PREDICTION_CONFIG
        self.graph_config = self.prediction_config.get("graph")

    def build_graph(self) -> str:
        engine = get_engine()
        stations_df = pd.read_sql("SELECT * FROM transport.station", engine)
        schedules_df = pd.read_sql("SELECT * FROM transport.schedule", engine)
        schedules_with_times = calculate_travel_time(schedules_df)
        return create_transport_network(stations_df, schedules_with_times)

    def save_graph(self) -> str:
        G = self.build_graph()
        network_path = self.graph_config.get("network_path", "")
        if not network_path:
            logger.error("Network path is not set")
            raise ValueError("Network path is not set")
        with open(network_path, "wb") as f:
            pickle.dump(G, f)

    def load_graph(self) -> str:
        network_path = self.graph_config.get("network_path", "")
        if not network_path:
            logger.error("Network path is not set")
            raise ValueError("Network path is not set")
        with open(network_path, "rb") as f:
            return pickle.load(f)

    def visualize_network(self) -> str:
        G = self.load_graph()
        return visualize_network(G)

    def find_optimal_route(self, start_coords: tuple, end_coords: tuple) -> str:
        G = self.load_graph()
        (start_lat, start_lon) = start_coords
        (end_lat, end_lon) = end_coords

        start_station = find_nearest_station_with_walk(start_lat, start_lon, G)
        end_station = find_nearest_station_with_walk(end_lat, end_lon, G)

        if not start_station or not end_station:
            logger.error("Impossible to find a starting or ending station")
            raise ValueError("Impossible to find a starting or ending station")

        walking_distance_start = start_station["walking_distance"]
        walking_duration_start = start_station["walking_duration"]

        walking_distance_end = end_station["walking_distance"]
        walking_duration_end = end_station["walking_duration"]

        optimal_path, network_time, route_info = find_optimal_route(
            G, start_station["station_id"], end_station["station_id"]
        )

        total_walking_distance = walking_distance_start + walking_distance_end
        total_walking_duration = walking_duration_start + walking_duration_end
        total_time = total_walking_duration + network_time

        return {
            "walking_distance": total_walking_distance,
            "walking_duration": total_walking_duration,
            "network_time": network_time,
            "total_time": total_time,
            "optimal_path": optimal_path,
            "route_info": route_info,
        }

    def adjust_station_weights(self, frequency_data: pd.DataFrame):
        G = self.load_graph()
        return adjust_station_weights(G, frequency_data, **self.graph_config.get("adjust_station_weights", {}))


if __name__ == "__main__":
    graph_builder = GraphBuilder()
    graph_builder.save_graph()
    graph = graph_builder.load_graph()
    route_info = graph_builder.find_optimal_route((48.8566, 2.3522), (48.8637, 2.3488))
