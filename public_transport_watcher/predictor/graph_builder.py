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
from public_transport_watcher.utils import get_engine, get_query_result

logger = get_logger()

_MAPPING_STATIONS = get_query_result("mapping_stations")


class GraphBuilder:
    def __init__(self):
        self.prediction_config = PREDICTION_CONFIG
        self.graph_config = self.prediction_config.get("graph")
        self.last_weighted_graph_update = None
        self.mapping_stations = dict(zip(_MAPPING_STATIONS["transport_id"], _MAPPING_STATIONS["transport_name"]))

    def build_graph(self) -> str:
        engine = get_engine()
        stations_df = pd.read_sql("SELECT * FROM transport.station", engine)
        schedules_df = pd.read_sql("SELECT * FROM transport.schedule", engine)
        schedules_with_times = calculate_travel_time(schedules_df)
        return create_transport_network(stations_df, schedules_with_times)

    def _get_network_path(self, graph_type="base"):
        if graph_type == "base":
            path = self.graph_config.get("base_network_path")
        elif graph_type == "weighted":
            path = self.graph_config.get("weighted_network_path")
            if not path:
                # If no weighted path specified, use base path with _weighted suffix
                base_path = self.graph_config.get("base_network_path")
                if base_path:
                    path = (
                        base_path.replace(".pkl", "_weighted.pkl")
                        if base_path.endswith(".pkl")
                        else f"{base_path}_weighted"
                    )
        else:
            raise ValueError(f"Invalid graph_type: {graph_type}. Must be 'base' or 'weighted'")

        if not path:
            logger.error(f"Network path for {graph_type} graph is not set")
            raise ValueError(f"Network path for {graph_type} graph is not set")

        return path

    def save_graph(self, graph=None, graph_type="base") -> None:
        if graph_type == "base" and graph is None:
            graph = self.build_graph()
        elif graph is None:
            raise ValueError(f"Graph object is required when saving {graph_type} graph")

        network_path = self._get_network_path(graph_type)
        with open(network_path, "wb") as f:
            pickle.dump(graph, f)
        logger.info(f"{graph_type.title()} graph saved to {network_path}")

    def load_graph(self, graph_type="base"):
        network_path = self._get_network_path(graph_type)
        with open(network_path, "rb") as f:
            graph = pickle.load(f)
        logger.debug(f"{graph_type.title()} graph loaded from {network_path}")
        return graph

    def visualize_network(self, use_weighted=False) -> str:
        graph_type = "weighted" if use_weighted else "base"
        G = self.load_graph(graph_type)
        return visualize_network(G)

    def find_optimal_route(self, start_coords: tuple, end_coords: tuple, use_weighted=False) -> dict:
        graph_type = "weighted" if use_weighted else "base"
        G = self.load_graph(graph_type)
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

        if "segments" in route_info:
            for segment in route_info["segments"]:
                transport_id = segment.get("transport_id")
                if transport_id and transport_id in self.mapping_stations:
                    segment["transport_name"] = self.mapping_stations[transport_id]
                else:
                    segment["transport_name"] = "Unknown"

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
            "graph_type": "weighted" if use_weighted else "base",
        }

    def update_weighted_graph(self, frequency_data: pd.DataFrame):
        base_graph = self.load_graph("base")
        weighted_graph = adjust_station_weights(
            base_graph, frequency_data, **self.graph_config.get("adjust_station_weights", {})
        )
        self.save_graph(weighted_graph, "weighted")
        return weighted_graph


if __name__ == "__main__":
    graph_builder = GraphBuilder()
    graph_builder.save_graph()

    route_comparison = graph_builder.find_optimal_route((48.8566, 2.3522), (48.8637, 2.3488))
    print("Route comparison:", route_comparison)
