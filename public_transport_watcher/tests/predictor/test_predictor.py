from unittest.mock import Mock, patch

import pandas as pd
import pytest
import schedule

from public_transport_watcher.predictor.predictor import Predictor


class TestPredictorInitialization:
    """Tests for Predictor initialization."""

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_initialization_success(self, mock_arima_class, mock_graph_class):
        """Test successful Predictor initialization with existing graphs."""
        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = ["base_graph", "weighted_graph"]
        mock_graph_class.return_value = mock_graph_builder

        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        predictor = Predictor()

        assert predictor.arima_predictor == mock_arima_predictor
        assert predictor.graph_builder == mock_graph_builder
        assert predictor.base_graph == "base_graph"
        assert predictor.weighted_graph == "weighted_graph"

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_initialization_missing_base_graph_build_success(self, mock_arima_class, mock_graph_class):
        """Test Predictor initialization when base graph is missing but can be built."""
        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = [
            FileNotFoundError("Base graph not found"),
            "base_graph",
            "weighted_graph",
        ]
        mock_graph_class.return_value = mock_graph_builder

        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        predictor = Predictor(build_graph_if_missing=True)

        assert predictor.base_graph == "base_graph"
        assert predictor.weighted_graph == "weighted_graph"

        mock_graph_builder.save_graph.assert_called_once_with(graph_type="base")

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_initialization_missing_base_graph_no_build(self, mock_arima_class, mock_graph_class):
        """Test Predictor initialization when base graph is missing and cannot be built."""
        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = FileNotFoundError("Base graph not found")
        mock_graph_class.return_value = mock_graph_builder

        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        with pytest.raises(ValueError, match="Base transport network graph not available"):
            Predictor(build_graph_if_missing=False)

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_initialization_missing_weighted_graph(self, mock_arima_class, mock_graph_class):
        """Test Predictor initialization when weighted graph is missing."""
        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = [
            "base_graph",
            FileNotFoundError("Weighted graph not found"),
        ]
        mock_graph_class.return_value = mock_graph_builder

        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        predictor = Predictor()

        assert predictor.base_graph == "base_graph"
        assert predictor.weighted_graph is None


class TestPredictorPredictionAndUpdate:
    """Tests for prediction and graph update functionality."""

    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    def test_predict_and_update_graph_success(self, mock_graph_class, mock_arima_class):
        """Test successful prediction and graph update."""
        mock_arima_predictor = Mock()
        mock_predictions = pd.DataFrame(
            {"station_id": [70671, 59403], "predictions": [[120, 130], [90, 100]], "total": [250, 190]}
        )
        mock_arima_predictor.predict_for_all_stations.return_value = mock_predictions
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.update_weighted_graph.return_value = "updated_weighted_graph"
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.arima_predictor = mock_arima_predictor
        predictor.graph_builder = mock_graph_builder

        result = predictor.predict_and_update_graph()

        assert result is True

        mock_arima_predictor.predict_for_all_stations.assert_called_once_with(optimize_params=False)
        mock_graph_builder.update_weighted_graph.assert_called_once_with(mock_predictions)

        assert predictor.weighted_graph == "updated_weighted_graph"

    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    def test_predict_and_update_graph_with_optimization(self, mock_graph_class, mock_arima_class):
        """Test prediction and graph update with parameter optimization."""
        mock_arima_predictor = Mock()
        mock_predictions = pd.DataFrame({"station_id": [70671], "predictions": [[120, 130]], "total": [250]})
        mock_arima_predictor.predict_for_all_stations.return_value = mock_predictions
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.update_weighted_graph.return_value = "updated_weighted_graph"
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.arima_predictor = mock_arima_predictor
        predictor.graph_builder = mock_graph_builder

        result = predictor.predict_and_update_graph(optimize_arima_params=True)

        assert result is True

        mock_arima_predictor.predict_for_all_stations.assert_called_once_with(optimize_params=True)

    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    def test_predict_and_update_graph_empty_predictions(self, mock_graph_class, mock_arima_class):
        """Test prediction and graph update with empty predictions."""
        mock_arima_predictor = Mock()
        mock_arima_predictor.predict_for_all_stations.return_value = pd.DataFrame()
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.arima_predictor = mock_arima_predictor
        predictor.graph_builder = mock_graph_builder

        result = predictor.predict_and_update_graph()

        assert result is False

        mock_graph_builder.update_weighted_graph.assert_not_called()

    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    def test_predict_and_update_graph_exception(self, mock_graph_class, mock_arima_class):
        """Test prediction and graph update when an exception occurs."""
        mock_arima_predictor = Mock()
        mock_arima_predictor.predict_for_all_stations.side_effect = Exception("Prediction failed")
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.arima_predictor = mock_arima_predictor
        predictor.graph_builder = mock_graph_builder

        result = predictor.predict_and_update_graph()

        assert result is False


class TestPredictorRouteFinding:
    """Tests for route finding functionality."""

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_find_optimal_route_base_graph(self, mock_arima_class, mock_graph_class):
        """Test finding optimal route using base graph."""
        mock_graph_builder = Mock()
        mock_route_info = {
            "walking_distance": 500.0,
            "walking_duration": 6.0,
            "network_time": 15.0,
            "total_time": 21.0,
            "optimal_path": [1, 2, 3],
            "route_info": {"segments": []},
            "graph_type": "base",
        }
        mock_graph_builder.find_optimal_route.return_value = mock_route_info
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder
        predictor.weighted_graph = None

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        result = predictor.find_optimal_route(start_coords, end_coords, use_weighted=False)

        assert result == mock_route_info

        mock_graph_builder.find_optimal_route.assert_called_once_with(start_coords, end_coords, use_weighted=False)

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_find_optimal_route_weighted_graph(self, mock_arima_class, mock_graph_class):
        """Test finding optimal route using weighted graph."""
        mock_graph_builder = Mock()
        mock_route_info = {
            "walking_distance": 500.0,
            "walking_duration": 6.0,
            "network_time": 15.0,
            "total_time": 21.0,
            "optimal_path": [1, 2, 3],
            "route_info": {"segments": []},
            "graph_type": "weighted",
        }
        mock_graph_builder.find_optimal_route.return_value = mock_route_info
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder
        predictor.weighted_graph = "weighted_graph"

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        result = predictor.find_optimal_route(start_coords, end_coords, use_weighted=True)

        assert result == mock_route_info

        mock_graph_builder.find_optimal_route.assert_called_once_with(start_coords, end_coords, use_weighted=True)

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_find_optimal_route_weighted_requested_but_unavailable(self, mock_arima_class, mock_graph_class):
        """Test finding optimal route when weighted graph is requested but unavailable."""
        mock_graph_builder = Mock()
        mock_route_info = {
            "walking_distance": 500.0,
            "walking_duration": 6.0,
            "network_time": 15.0,
            "total_time": 21.0,
            "optimal_path": [1, 2, 3],
            "route_info": {"segments": []},
            "graph_type": "base",
        }
        mock_graph_builder.find_optimal_route.return_value = mock_route_info
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder
        predictor.weighted_graph = None

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        result = predictor.find_optimal_route(start_coords, end_coords, use_weighted=True)

        assert result == mock_route_info

        mock_graph_builder.find_optimal_route.assert_called_once_with(start_coords, end_coords, use_weighted=False)

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_find_optimal_route_exception(self, mock_arima_class, mock_graph_class):
        """Test finding optimal route when an exception occurs."""
        mock_graph_builder = Mock()
        mock_graph_builder.find_optimal_route.side_effect = Exception("Route finding failed")
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        result = predictor.find_optimal_route(start_coords, end_coords)

        assert result is None


class TestPredictorGraphManagement:
    """Tests for graph management functionality."""

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_rebuild_base_graph_success(self, mock_arima_class, mock_graph_class):
        """Test successful base graph rebuilding."""
        mock_graph_builder = Mock()
        mock_graph_builder.save_graph.return_value = None
        mock_graph_builder.load_graph.return_value = "new_base_graph"
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder

        result = predictor.rebuild_base_graph()

        assert result is True

        mock_graph_builder.save_graph.assert_called_once_with(graph_type="base")
        mock_graph_builder.load_graph.assert_called_once_with("base")

        assert predictor.base_graph == "new_base_graph"

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_rebuild_base_graph_exception(self, mock_arima_class, mock_graph_class):
        """Test base graph rebuilding when an exception occurs."""
        mock_graph_builder = Mock()
        mock_graph_builder.save_graph.side_effect = Exception("Save failed")
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.graph_builder = mock_graph_builder

        result = predictor.rebuild_base_graph()

        assert result is False

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_get_graph_info(self, mock_arima_class, mock_graph_class):
        """Test getting graph information."""
        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.base_graph = Mock()
        predictor.weighted_graph = Mock()

        predictor.base_graph.number_of_nodes.return_value = 100
        predictor.base_graph.number_of_edges.return_value = 200
        predictor.weighted_graph.number_of_nodes.return_value = 100
        predictor.weighted_graph.number_of_edges.return_value = 200

        result = predictor.get_graph_info()

        assert "base_graph_available" in result
        assert "weighted_graph_available" in result
        assert "base_graph_nodes" in result
        assert "base_graph_edges" in result
        assert "weighted_graph_nodes" in result
        assert "weighted_graph_edges" in result

        assert result["base_graph_available"] is True
        assert result["weighted_graph_available"] is True
        assert result["base_graph_nodes"] == 100
        assert result["base_graph_edges"] == 200
        assert result["weighted_graph_nodes"] == 100
        assert result["weighted_graph_edges"] == 200

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_get_graph_info_missing_graphs(self, mock_arima_class, mock_graph_class):
        """Test getting graph information when graphs are missing."""
        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.base_graph = None
        predictor.weighted_graph = None

        result = predictor.get_graph_info()

        assert "base_graph_available" in result
        assert "weighted_graph_available" in result

        assert result["base_graph_available"] is False
        assert result["weighted_graph_available"] is False

        assert "base_graph_nodes" not in result
        assert "base_graph_edges" not in result
        assert "weighted_graph_nodes" not in result
        assert "weighted_graph_edges" not in result


class TestPredictorScheduling:
    """Tests for scheduling functionality."""

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_schedule_hourly_updates(self, mock_arima_class, mock_graph_class):
        """Test scheduling hourly updates."""
        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.predict_and_update_graph = Mock()

        result = predictor.schedule_hourly_updates()

        assert result is True

        assert len(schedule.jobs) > 0
        assert hasattr(schedule.jobs[0], "job_func")

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_run_scheduled_tasks_one_time(self, mock_arima_class, mock_graph_class):
        """Test running scheduled tasks once."""
        mock_graph_builder = Mock()
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor.__new__(Predictor)
        predictor.predict_and_update_graph = Mock()

        predictor.run_scheduled_tasks(run_forever=False)

        predictor.predict_and_update_graph.assert_called_once()

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_optimize_all_arima_models(self, mock_arima_class, mock_graph_class):
        """Test optimizing all ARIMA models."""
        mock_arima_predictor = Mock()
        mock_predictions = pd.DataFrame(
            {"station_id": [70671, 59403], "predictions": [[120, 130], [90, 100]], "total": [250, 190]}
        )
        mock_arima_predictor.predict_for_all_stations.return_value = mock_predictions
        mock_arima_class.return_value = mock_arima_predictor

        predictor = Predictor.__new__(Predictor)
        predictor.arima_predictor = mock_arima_predictor

        result = predictor.optimize_all_arima_models()

        assert result.equals(mock_predictions)

        mock_arima_predictor.predict_for_all_stations.assert_called_once_with(optimize_params=True)
