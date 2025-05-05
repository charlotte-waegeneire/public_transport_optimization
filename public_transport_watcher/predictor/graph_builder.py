import pickle

import pandas as pd

from public_transport_watcher.predictor.configuration import PREDICTION_CONFIG
from public_transport_watcher.predictor.graph import (
    calculate_travel_time,
    create_transport_network,
    find_optimal_route,
    visualize_network,
)
from public_transport_watcher.utils import get_engine


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
            raise ValueError("Network path is not set")
        with open(network_path, "wb") as f:
            pickle.dump(G, f)

    def load_graph(self) -> str:
        network_path = self.graph_config.get("network_path", "")
        if not network_path:
            raise ValueError("Network path is not set")
        with open(network_path, "rb") as f:
            return pickle.load(f)

    def visualize_network(self) -> str:
        G = self.load_graph()
        return visualize_network(G)

    def find_optimal_route(self, start_station_id: int, end_station_id: int) -> str:
        G = self.load_graph()
        return find_optimal_route(G, start_station_id, end_station_id)


if __name__ == "__main__":
    graph_builder = GraphBuilder()
    graph_builder.save_graph()
    graph = graph_builder.load_graph()
    optimal_path, total_time, route_info = graph_builder.find_optimal_route(1, 2)
