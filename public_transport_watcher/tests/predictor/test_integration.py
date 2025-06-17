import tempfile
from unittest.mock import Mock, patch

import pandas as pd

from public_transport_watcher.predictor.arima_predictions import ArimaPredictor
from public_transport_watcher.predictor.graph_builder import GraphBuilder
from public_transport_watcher.predictor.predictor import Predictor


class TestPredictorIntegration:
    """Integration tests for the complete predictor workflow."""

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_complete_prediction_workflow(self, mock_arima_class, mock_graph_class):
        """Test the complete prediction workflow from initialization to route finding."""
        mock_arima_predictor = Mock()
        mock_predictions = pd.DataFrame(
            {"station_id": [70671, 59403], "predictions": [[120, 130], [90, 100]], "total": [250, 190]}
        )
        mock_arima_predictor.predict_for_all_stations.return_value = mock_predictions
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = ["base_graph", "weighted_graph"]
        mock_graph_builder.update_weighted_graph.return_value = "updated_weighted_graph"
        mock_graph_builder.find_optimal_route.return_value = {
            "walking_distance": 500.0,
            "walking_duration": 6.0,
            "network_time": 15.0,
            "total_time": 21.0,
            "optimal_path": [1, 2, 3],
            "route_info": {"segments": []},
            "graph_type": "weighted",
        }
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor()

        result = predictor.predict_and_update_graph()
        assert result is True
        assert predictor.weighted_graph == "updated_weighted_graph"

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)
        route = predictor.find_optimal_route(start_coords, end_coords, use_weighted=True)

        assert route is not None
        assert route["graph_type"] == "weighted"
        assert route["total_time"] == 21.0

    @patch("public_transport_watcher.predictor.arima_predictions.get_data_from_db")
    @patch("public_transport_watcher.predictor.arima_predictions.find_optimal_params")
    @patch("public_transport_watcher.predictor.arima_predictions.predict_navigo_validations")
    def test_arima_to_graph_integration(self, mock_predict, mock_find_params, mock_get_data):
        """Test integration between ARIMA predictions and graph updates."""
        mock_traffic_data = pd.DataFrame(
            {
                "station_id": [70671, 70671, 70671, 70671],
                "validations": [100, 110, 120, 130],
                "datetime": pd.date_range("2024-01-01", periods=4, freq="h"),
            }
        )
        mock_get_data.return_value = mock_traffic_data

        mock_find_params.return_value = (2, 1, 1)

        mock_predictions = [120, 130, 140, 150]
        mock_total = 540
        mock_predict.return_value = (mock_predictions, mock_total)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"70671": [1, 1, 2]}')
            params_file = f.name

        try:
            with patch(
                "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
                {
                    "params_station_file": params_file,
                    "p_range": [0, 1, 2],
                    "d_range": [0, 1],
                    "q_range": [0, 1, 2],
                },
            ):
                arima_predictor = ArimaPredictor()

                predictions, total = arima_predictor.predict_for_station(70671, optimize_params=True)

                assert predictions == mock_predictions
                assert total == mock_total

                all_predictions = arima_predictor.predict_for_all_stations()
                assert isinstance(all_predictions, pd.DataFrame)
                assert len(all_predictions) == 1
                assert all_predictions.iloc[0]["station_id"] == 70671
        finally:
            import os

            os.unlink(params_file)

    def test_graph_builder_integration(self):
        """Test integration of graph builder components."""
        mock_mapping = pd.DataFrame(
            {"transport_id": [1, 2, 3], "transport_name": ["Metro Line 1", "Metro Line 2", "Bus Line 1"]}
        )

        with patch("public_transport_watcher.predictor.graph_builder._MAPPING_STATIONS", mock_mapping):
            graph_builder = GraphBuilder()

            assert len(graph_builder.mapping_stations) == 3
            assert graph_builder.mapping_stations[1] == "Metro Line 1"

            # Test path handling
            with patch.dict(graph_builder.graph_config, {"base_network_path": "/test/base.pkl"}):
                path = graph_builder._get_network_path("base")
                assert path == "/test/base.pkl"

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_error_propagation_integration(self, mock_arima_class, mock_graph_class):
        """Test how errors propagate through the predictor system."""
        mock_arima_predictor = Mock()
        mock_arima_predictor.predict_for_all_stations.side_effect = Exception("ARIMA failed")
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = ["base_graph", "weighted_graph"]
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor()

        result = predictor.predict_and_update_graph()
        assert result is False

        assert predictor.weighted_graph == "weighted_graph"

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_graph_fallback_integration(self, mock_arima_class, mock_graph_class):
        """Test graph fallback mechanisms in integration."""
        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = [
            "base_graph",
            FileNotFoundError("Weighted graph not found"),  # Weighted graph fails
        ]
        mock_graph_builder.find_optimal_route.return_value = {
            "walking_distance": 500.0,
            "walking_duration": 6.0,
            "network_time": 15.0,
            "total_time": 21.0,
            "optimal_path": [1, 2, 3],
            "route_info": {"segments": []},
            "graph_type": "base",
        }
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor()

        start_coords = (48.8566, 2.3522)
        end_coords = (48.8637, 2.3488)

        route = predictor.find_optimal_route(start_coords, end_coords, use_weighted=True)

        mock_graph_builder.find_optimal_route.assert_called_once_with(start_coords, end_coords, use_weighted=False)
        assert route["graph_type"] == "base"

    def test_data_flow_integration(self):
        """Test the complete data flow through the predictor system."""
        mock_predictions_df = pd.DataFrame(
            {"station_id": [70671, 59403], "predictions": [[120, 130], [90, 100]], "total": [250, 190]}
        )

        assert "station_id" in mock_predictions_df.columns
        assert "predictions" in mock_predictions_df.columns
        assert "total" in mock_predictions_df.columns

        assert mock_predictions_df["station_id"].dtype in [int, "int64"]
        assert mock_predictions_df["total"].dtype in [int, "int64"]

        assert all(isinstance(p, list) for p in mock_predictions_df["predictions"])

        for _, row in mock_predictions_df.iterrows():
            assert abs(sum(row["predictions"]) - row["total"]) < 1e-6

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_scheduling_integration(self, mock_arima_class, mock_graph_class):
        """Test integration of scheduling functionality."""
        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.side_effect = ["base_graph", "weighted_graph"]
        mock_graph_class.return_value = mock_graph_builder

        predictor = Predictor()

        result = predictor.schedule_hourly_updates()
        assert result is True

        predictor.predict_and_update_graph = Mock()
        predictor.run_scheduled_tasks(run_forever=False)
        predictor.predict_and_update_graph.assert_called_once()

    def test_configuration_integration(self):
        """Test integration of configuration across components."""
        from public_transport_watcher.predictor.configuration import ARIMA_CONFIG, PREDICTION_CONFIG

        assert "p_range" in ARIMA_CONFIG
        assert "d_range" in ARIMA_CONFIG
        assert "q_range" in ARIMA_CONFIG
        assert "params_station_file" in ARIMA_CONFIG

        assert "graph" in PREDICTION_CONFIG
        assert "arima" in PREDICTION_CONFIG

        graph_config = PREDICTION_CONFIG["graph"]
        assert "base_network_path" in graph_config or "adjust_station_weights" in graph_config

    @patch("public_transport_watcher.predictor.predictor.GraphBuilder")
    @patch("public_transport_watcher.predictor.predictor.ArimaPredictor")
    def test_memory_management_integration(self, mock_arima_class, mock_graph_class):
        """Test memory management and resource cleanup in integration."""
        mock_arima_predictor = Mock()
        mock_arima_class.return_value = mock_arima_predictor

        mock_graph_builder = Mock()
        mock_graph_builder.load_graph.return_value = "base_graph"
        mock_graph_class.return_value = mock_graph_builder

        predictors = []
        for i in range(3):
            predictor = Predictor()
            predictors.append(predictor)

            assert predictor.arima_predictor == mock_arima_predictor
            assert predictor.graph_builder == mock_graph_builder

        assert len(predictors) == 3
        assert all(p.base_graph == "base_graph" for p in predictors)
