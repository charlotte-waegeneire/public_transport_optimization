from datetime import timedelta
import json

import networkx as nx
import pandas as pd
import pytest

from public_transport_watcher.predictor.arima_predictions import ArimaPredictor
from public_transport_watcher.predictor.graph_builder import GraphBuilder
from public_transport_watcher.predictor.predictor import Predictor


@pytest.fixture
def mock_station_params():
    """Create mock station ARIMA parameters."""
    return {
        "70671": [1, 1, 2],
        "59403": [2, 0, 2],
        "59420": [2, 1, 2],
        "59429": [2, 1, 1],
    }


@pytest.fixture
def mock_station_params_file(mock_station_params, tmp_path):
    """Create a temporary station parameters file."""
    params_file = tmp_path / "station_arima_params.json"
    with open(params_file, "w") as f:
        json.dump(mock_station_params, f)
    return str(params_file)


@pytest.fixture
def mock_traffic_data():
    """Create mock traffic data for testing."""
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="h")
    data = []

    for date in dates:
        data.append(
            {
                "station_id": 70671,
                "station_name": "Test Station",
                "time_bin_id": len(data) + 1,
                "cat_day": "JOHV",
                "start_timestamp": date,
                "end_timestamp": date + timedelta(hours=1),
                "validations": 100 + (len(data) % 50),  # Varying validation counts
                "datetime": date,
            }
        )

    df = pd.DataFrame(data)
    df.set_index("datetime", inplace=True)
    return df


@pytest.fixture
def mock_empty_traffic_data():
    """Create empty traffic data for testing."""
    return pd.DataFrame()


@pytest.fixture
def mock_predictions_data():
    """Create mock predictions data for testing."""
    return pd.DataFrame(
        {
            "station_id": [70671, 59403, 59420],
            "predictions": [
                [120, 130, 140, 150],  # 4-hour predictions
                [90, 100, 110, 120],
                [80, 85, 90, 95],
            ],
            "total": [540, 420, 350],
        }
    )


@pytest.fixture
def mock_base_graph():
    """Create a mock base transport network graph."""
    G = nx.DiGraph()

    stations = [
        (1, {"name": "Station 1", "latitude": 48.8566, "longitude": 2.3522}),
        (2, {"name": "Station 2", "latitude": 48.8637, "longitude": 2.3488}),
        (3, {"name": "Station 3", "latitude": 48.8584, "longitude": 2.2945}),
    ]
    G.add_nodes_from(stations)

    edges = [
        (1, 2, {"line_id": 1, "travel_time": 5, "transport_id": 1}),
        (2, 3, {"line_id": 1, "travel_time": 8, "transport_id": 1}),
        (1, 3, {"line_id": 2, "travel_time": 12, "transport_id": 2}),
    ]
    G.add_edges_from(edges)

    return G


@pytest.fixture
def mock_weighted_graph():
    """Create a mock weighted transport network graph."""
    G = nx.DiGraph()

    stations = [
        (1, {"name": "Station 1", "latitude": 48.8566, "longitude": 2.3522, "weight": 1.0}),
        (2, {"name": "Station 2", "latitude": 48.8637, "longitude": 2.3488, "weight": 1.2}),
        (3, {"name": "Station 3", "latitude": 48.8584, "longitude": 2.2945, "weight": 0.8}),
    ]
    G.add_nodes_from(stations)

    edges = [
        (1, 2, {"line_id": 1, "travel_time": 5, "transport_id": 1, "weight": 1.1}),
        (2, 3, {"line_id": 1, "travel_time": 8, "transport_id": 1, "weight": 1.3}),
        (1, 3, {"line_id": 2, "travel_time": 12, "transport_id": 2, "weight": 0.9}),
    ]
    G.add_edges_from(edges)

    return G


@pytest.fixture
def mock_graph_file(tmp_path):
    """Create a temporary graph file for testing."""
    graph_file = tmp_path / "test_graph.pkl"
    return str(graph_file)


@pytest.fixture
def arima_predictor(mock_station_params_file):
    """Create an ArimaPredictor instance for testing."""
    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": mock_station_params_file,
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        )
        return ArimaPredictor()


@pytest.fixture
def graph_builder():
    """Create a GraphBuilder instance for testing."""
    return GraphBuilder()


@pytest.fixture
def mock_predictor(mock_base_graph, mock_weighted_graph, tmp_path):
    """Create a Predictor instance with mocked graphs for testing."""
    base_graph_file = tmp_path / "base_graph.pkl"
    weighted_graph_file = tmp_path / "weighted_graph.pkl"

    import pickle

    with open(base_graph_file, "wb") as f:
        pickle.dump(mock_base_graph, f)
    with open(weighted_graph_file, "wb") as f:
        pickle.dump(mock_weighted_graph, f)

    with pytest.MonkeyPatch().context() as m:
        m.setenv("BASE_NETWORK_PATH", str(base_graph_file))
        m.setenv("WEIGHTED_NETWORK_PATH", str(weighted_graph_file))

        with pytest.MonkeyPatch().context() as m2:
            m2.setattr(
                "public_transport_watcher.predictor.graph_builder.GraphBuilder.load_graph",
                lambda self, graph_type: mock_base_graph if graph_type == "base" else mock_weighted_graph,
            )
            return Predictor()


@pytest.fixture
def mock_coordinates():
    """Create mock coordinates for route testing."""
    return {
        "start": (48.8566, 2.3522),  # Paris coordinates
        "end": (48.8637, 2.3488),  # Another Paris location
        "far_away": (43.2965, 5.3698),  # Marseille coordinates
    }


@pytest.fixture
def mock_route_info():
    """Create mock route information for testing."""
    return {
        "walking_distance": 500.0,
        "walking_duration": 6.0,
        "walking_distance_start": 300.0,
        "walking_duration_start": 4.0,
        "walking_distance_end": 200.0,
        "walking_duration_end": 2.0,
        "network_time": 15.0,
        "total_time": 21.0,
        "optimal_path": [1, 2, 3],
        "route_info": {
            "segments": [
                {"transport_id": 1, "transport_name": "Metro Line 1", "duration": 5},
                {"transport_id": 1, "transport_name": "Metro Line 1", "duration": 8},
            ]
        },
        "graph_type": "base",
    }
