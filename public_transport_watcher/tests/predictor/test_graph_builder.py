import pickle
from unittest.mock import Mock, patch

import networkx as nx
import pandas as pd
import pytest

from public_transport_watcher.predictor.graph_builder import GraphBuilder


class TestGraphBuilderInitialization:
    """Tests for GraphBuilder initialization."""

    def test_initialization(self, graph_builder):
        """Test GraphBuilder initialization."""
        assert hasattr(graph_builder, "prediction_config")
        assert hasattr(graph_builder, "graph_config")
        assert hasattr(graph_builder, "mapping_stations")
        assert isinstance(graph_builder.mapping_stations, dict)

    @patch("public_transport_watcher.predictor.graph_builder._MAPPING_STATIONS")
    def test_mapping_stations_loading(self, mock_mapping):
        """Test that mapping stations are loaded correctly."""
        mock_df = pd.DataFrame(
            {"transport_id": [1, 2, 3], "transport_name": ["Metro Line 1", "Metro Line 2", "Bus Line 1"]}
        )

        mock_mapping.__getitem__.return_value = mock_df

        with patch("public_transport_watcher.predictor.graph_builder.dict") as mock_dict:
            mock_dict.return_value = {1: "Metro Line 1", 2: "Metro Line 2", 3: "Bus Line 1"}

            builder = GraphBuilder()

            assert len(builder.mapping_stations) == 3
            assert builder.mapping_stations[1] == "Metro Line 1"


class TestGraphBuilderPathHandling:
    """Tests for graph path handling."""

    def test_get_network_path_base(self, graph_builder):
        """Test getting base network path."""
        with patch.dict(graph_builder.graph_config, {"base_network_path": "/test/base.pkl"}):
            path = graph_builder._get_network_path("base")
            assert path == "/test/base.pkl"

    def test_get_network_path_weighted(self, graph_builder):
        """Test getting weighted network path."""
        with patch.dict(graph_builder.graph_config, {"weighted_network_path": "/test/weighted.pkl"}):
            path = graph_builder._get_network_path("weighted")
            assert path == "/test/weighted.pkl"

    def test_get_network_path_weighted_fallback(self, graph_builder):
        """Test getting weighted network path with fallback to base path."""
        with patch.dict(
            graph_builder.graph_config, {"base_network_path": "/test/base.pkl", "weighted_network_path": None}
        ):
            path = graph_builder._get_network_path("weighted")
            assert path == "/test/base_weighted.pkl"

    def test_get_network_path_invalid_type(self, graph_builder):
        """Test getting network path with invalid graph type."""
        with pytest.raises(ValueError, match="Invalid graph_type"):
            graph_builder._get_network_path("invalid")

    def test_get_network_path_missing_config(self, graph_builder):
        """Test getting network path when config is missing."""
        with patch.dict(graph_builder.graph_config, {}, clear=True):
            with pytest.raises(ValueError, match="Network path for base graph is not set"):
                graph_builder._get_network_path("base")


class TestGraphBuilderGraphOperations:
    """Tests for graph building, saving, and loading operations."""

    @patch("public_transport_watcher.predictor.graph_builder.get_engine")
    @patch("public_transport_watcher.predictor.graph_builder.calculate_travel_time")
    @patch("public_transport_watcher.predictor.graph_builder.create_transport_network")
    def test_build_graph(self, mock_create_network, mock_calculate_time, mock_get_engine):
        """Test building a graph from database data."""
        mock_stations_df = pd.DataFrame(
            {
                "id": [1, 2],
                "name": ["Station 1", "Station 2"],
                "latitude": [48.8566, 48.8637],
                "longitude": [2.3522, 2.3488],
            }
        )

        mock_schedules_df = pd.DataFrame(
            {
                "arrival_timestamp": ["2024-01-01 10:00:00", "2024-01-01 10:05:00"],
                "stop_id": [1, 2],
                "next_station_id": [2, 3],
                "line_numeric_id": [1, 1],
                "journey_id": ["TRIP1", "TRIP1"],
            }
        )

        mock_engine = Mock()
        mock_get_engine.return_value = mock_engine

        with patch("pandas.read_sql") as mock_read_sql:
            mock_read_sql.side_effect = [mock_stations_df, mock_schedules_df]

            mock_calculate_time.return_value = mock_schedules_df
            mock_graph = nx.DiGraph()
            mock_create_network.return_value = mock_graph

            graph_builder = GraphBuilder()
            result = graph_builder.build_graph()

            assert result == mock_graph

            mock_calculate_time.assert_called_once_with(mock_schedules_df)
            mock_create_network.assert_called_once_with(mock_stations_df, mock_schedules_df)

    def test_save_graph_base(self, graph_builder, mock_base_graph, tmp_path):
        """Test saving base graph."""
        graph_file = tmp_path / "test_base.pkl"

        with patch.object(graph_builder, "_get_network_path", return_value=str(graph_file)):
            graph_builder.save_graph(graph=mock_base_graph, graph_type="base")

            assert graph_file.exists()

            with open(graph_file, "rb") as f:
                loaded_graph = pickle.load(f)

            assert isinstance(loaded_graph, nx.DiGraph)
            assert loaded_graph.number_of_nodes() == 3

    def test_save_graph_base_without_graph(self, graph_builder, tmp_path):
        """Test saving base graph without providing graph object."""
        graph_file = tmp_path / "test_base.pkl"

        with patch.object(graph_builder, "_get_network_path", return_value=str(graph_file)):
            with patch.object(graph_builder, "build_graph", return_value=nx.DiGraph()):
                graph_builder.save_graph(graph_type="base")

                assert graph_file.exists()

    def test_save_graph_weighted_without_graph(self, graph_builder):
        """Test saving weighted graph without providing graph object."""
        with pytest.raises(ValueError, match="Graph object is required when saving weighted graph"):
            graph_builder.save_graph(graph_type="weighted")

    def test_load_graph(self, graph_builder, mock_base_graph, tmp_path):
        """Test loading a graph from file."""
        graph_file = tmp_path / "test_load.pkl"

        with open(graph_file, "wb") as f:
            pickle.dump(mock_base_graph, f)

        with patch.object(graph_builder, "_get_network_path", return_value=str(graph_file)):
            loaded_graph = graph_builder.load_graph("base")

            assert isinstance(loaded_graph, nx.DiGraph)
            assert loaded_graph.number_of_nodes() == 3
            assert loaded_graph.number_of_edges() == 3

    def test_load_graph_file_not_found(self, graph_builder):
        """Test loading a graph from non-existent file."""
        with patch.object(graph_builder, "_get_network_path", return_value="/nonexistent/file.pkl"):
            with pytest.raises(FileNotFoundError):
                graph_builder.load_graph("base")


class TestGraphBuilderRouteFinding:
    """Tests for route finding functionality."""

    @patch("public_transport_watcher.predictor.graph_builder.find_nearest_station_with_walk")
    @patch("public_transport_watcher.predictor.graph_builder.find_optimal_route")
    def test_find_optimal_route_success(self, mock_find_route, mock_find_nearest, graph_builder, mock_base_graph):
        """Test successful route finding."""
        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        mock_find_nearest.side_effect = [
            {"station_id": 1, "walking_distance": 300.0, "walking_duration": 4.0},
            {"station_id": 2, "walking_distance": 200.0, "walking_duration": 2.0},
        ]

        mock_find_route.return_value = (
            [1, 2],  # optimal_path
            15.0,  # network_time
            {  # route_info
                "segments": [{"transport_id": 1, "duration": 15}]
            },
        )

        with patch.object(graph_builder, "load_graph", return_value=mock_base_graph):
            result = graph_builder.find_optimal_route(start_coords, end_coords, use_weighted=False)

            assert "walking_distance" in result
            assert "walking_duration" in result
            assert "network_time" in result
            assert "total_time" in result
            assert "optimal_path" in result
            assert "route_info" in result
            assert "graph_type" in result

            assert result["walking_distance"] == 500.0
            assert result["walking_duration"] == 6.0
            assert result["network_time"] == 15.0
            assert result["total_time"] == 21.0
            assert result["graph_type"] == "base"

            assert "transport_name" in result["route_info"]["segments"][0]

    @patch("public_transport_watcher.predictor.graph_builder.find_nearest_station_with_walk")
    def test_find_optimal_route_no_start_station(self, mock_find_nearest, graph_builder, mock_base_graph):
        """Test route finding when no start station is found."""
        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        mock_find_nearest.return_value = None

        with patch.object(graph_builder, "load_graph", return_value=mock_base_graph):
            with pytest.raises(ValueError, match="Impossible to find a starting or ending station"):
                graph_builder.find_optimal_route(start_coords, end_coords)

    @patch("public_transport_watcher.predictor.graph_builder.find_nearest_station_with_walk")
    def test_find_optimal_route_no_end_station(self, mock_find_nearest, graph_builder, mock_base_graph):
        """Test route finding when no end station is found."""
        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        mock_find_nearest.side_effect = [{"station_id": 1, "walking_distance": 300.0, "walking_duration": 4.0}, None]

        with patch.object(graph_builder, "load_graph", return_value=mock_base_graph):
            with pytest.raises(ValueError, match="Impossible to find a starting or ending station"):
                graph_builder.find_optimal_route(start_coords, end_coords)

    def test_find_optimal_route_weighted_graph(self, graph_builder, mock_weighted_graph):
        """Test route finding with weighted graph."""
        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        with patch.object(graph_builder, "load_graph", return_value=mock_weighted_graph):
            with patch.object(graph_builder, "find_optimal_route") as mock_find_route:
                mock_find_route.return_value = {
                    "walking_distance": 500.0,
                    "walking_duration": 6.0,
                    "network_time": 15.0,
                    "total_time": 21.0,
                    "optimal_path": [1, 2],
                    "route_info": {"segments": []},
                    "graph_type": "weighted",
                }

                result = graph_builder.find_optimal_route(start_coords, end_coords, use_weighted=True)
                assert result["graph_type"] == "weighted"


class TestGraphBuilderWeightedGraphUpdate:
    """Tests for weighted graph update functionality."""

    @patch("public_transport_watcher.predictor.graph_builder.adjust_station_weights")
    def test_update_weighted_graph(self, mock_adjust_weights, graph_builder, mock_base_graph, mock_predictions_data):
        """Test updating weighted graph with predictions data."""
        mock_weighted_graph = nx.DiGraph()
        mock_adjust_weights.return_value = mock_weighted_graph

        with patch.object(graph_builder, "load_graph", return_value=mock_base_graph):
            with patch.object(graph_builder, "save_graph") as mock_save:
                result = graph_builder.update_weighted_graph(mock_predictions_data)

                assert result == mock_weighted_graph

                mock_adjust_weights.assert_called_once()
                mock_save.assert_called_once_with(mock_weighted_graph, "weighted")


class TestGraphBuilderVisualization:
    """Tests for network visualization functionality."""

    def test_visualize_network_base(self, graph_builder, mock_base_graph):
        """Test network visualization for base graph."""
        with patch.object(graph_builder, "load_graph", return_value=mock_base_graph):
            with patch("public_transport_watcher.predictor.graph_builder.visualize_network") as mock_viz:
                mock_viz.return_value = "network_visualization.html"

                result = graph_builder.visualize_network(use_weighted=False)

                assert result == "network_visualization.html"
                mock_viz.assert_called_once_with(mock_base_graph)

    def test_visualize_network_weighted(self, graph_builder, mock_weighted_graph):
        """Test network visualization for weighted graph."""
        with patch.object(graph_builder, "load_graph", return_value=mock_weighted_graph):
            with patch("public_transport_watcher.predictor.graph_builder.visualize_network") as mock_viz:
                mock_viz.return_value = "weighted_network_visualization.html"

                result = graph_builder.visualize_network(use_weighted=True)

                assert result == "weighted_network_visualization.html"
                mock_viz.assert_called_once_with(mock_weighted_graph)
