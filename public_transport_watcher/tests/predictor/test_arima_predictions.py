import json
from unittest.mock import patch

import pandas as pd

from public_transport_watcher.predictor.arima_predictions import ArimaPredictor


class TestArimaPredictorInitialization:
    """Tests for ArimaPredictor initialization."""

    def test_initialization_with_valid_params_file(self, mock_station_params_file):
        """Test ArimaPredictor initialization with valid parameters file."""
        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": mock_station_params_file,
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()

            assert hasattr(predictor, "station_params")
            assert len(predictor.station_params) == 4
            assert predictor.station_params[70671] == (1, 1, 2)
            assert predictor.station_params[59403] == (2, 0, 2)

    def test_initialization_with_missing_params_file(self):
        """Test ArimaPredictor initialization with missing parameters file."""
        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": "/nonexistent/file.json",
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()

            assert hasattr(predictor, "station_params")
            assert len(predictor.station_params) == 0

    def test_initialization_with_invalid_json_file(self, tmp_path):
        """Test ArimaPredictor initialization with invalid JSON file."""
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("invalid json content")

        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": str(invalid_file),
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()

            assert hasattr(predictor, "station_params")
            assert len(predictor.station_params) == 0


class TestArimaPredictorStationPrediction:
    """Tests for single station prediction functionality."""

    @patch("public_transport_watcher.predictor.arima_predictions.get_data_from_db")
    @patch("public_transport_watcher.predictor.arima_predictions.find_optimal_params")
    @patch("public_transport_watcher.predictor.arima_predictions.predict_navigo_validations")
    def test_predict_for_station_with_existing_params(
        self, mock_predict, mock_find_params, mock_get_data, arima_predictor, mock_traffic_data
    ):
        """Test prediction for station with existing parameters."""
        station_id = 70671

        mock_get_data.return_value = mock_traffic_data

        mock_predictions = [120, 130, 140, 150]
        mock_total = 540
        mock_predict.return_value = (mock_predictions, mock_total)

        mock_find_params.return_value = (1, 1, 2)

        predictions, total = arima_predictor.predict_for_station(station_id, optimize_params=False)

        assert predictions == mock_predictions
        assert total == mock_total

        mock_find_params.assert_not_called()
        mock_predict.assert_called_once()

    @patch("public_transport_watcher.predictor.arima_predictions.get_data_from_db")
    @patch("public_transport_watcher.predictor.arima_predictions.find_optimal_params")
    @patch("public_transport_watcher.predictor.arima_predictions.predict_navigo_validations")
    def test_predict_for_station_with_optimization(
        self, mock_predict, mock_find_params, mock_get_data, arima_predictor, mock_traffic_data
    ):
        """Test prediction for station with parameter optimization."""
        station_id = 99999  # Station not in params

        mock_get_data.return_value = mock_traffic_data

        mock_find_params.return_value = (2, 1, 1)

        mock_predictions = [90, 100, 110, 120]
        mock_total = 420
        mock_predict.return_value = (mock_predictions, mock_total)

        predictions, total = arima_predictor.predict_for_station(station_id, optimize_params=True)

        assert predictions == mock_predictions
        assert total == mock_total

        mock_find_params.assert_called_once()
        mock_predict.assert_called_once()

    @patch("public_transport_watcher.predictor.arima_predictions.get_data_from_db")
    def test_predict_for_station_with_no_data(self, mock_get_data, arima_predictor):
        """Test prediction for station with no available data."""
        station_id = 70671

        mock_get_data.return_value = pd.DataFrame()

        predictions, total = arima_predictor.predict_for_station(station_id)

        assert predictions is None
        assert total == 0

    @patch("public_transport_watcher.predictor.arima_predictions.get_data_from_db")
    def test_predict_for_station_with_exception(self, mock_get_data, arima_predictor):
        """Test prediction for station when an exception occurs."""
        station_id = 70671

        mock_get_data.side_effect = Exception("Database error")

        predictions, total = arima_predictor.predict_for_station(station_id)

        assert predictions is None
        assert total == 0


class TestArimaPredictorAllStationsPrediction:
    """Tests for all stations prediction functionality."""

    @patch("public_transport_watcher.predictor.arima_predictions.ArimaPredictor.predict_for_station")
    def test_predict_for_all_stations_success(self, mock_predict_station, arima_predictor):
        """Test prediction for all stations with successful results."""
        mock_predict_station.return_value = ([120, 130, 140, 150], 540)

        result = arima_predictor.predict_for_all_stations()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 4
        assert list(result.columns) == ["station_id", "predictions", "total"]

        assert mock_predict_station.call_count == 4

    @patch("public_transport_watcher.predictor.arima_predictions.ArimaPredictor.predict_for_station")
    def test_predict_for_all_stations_with_failures(self, mock_predict_station, arima_predictor):
        """Test prediction for all stations with some failures."""

        def mock_predict_side_effect(station_id, optimize_params=False):
            if station_id == 59403:
                return (None, 0)
            else:
                return ([120, 130, 140, 150], 540)

        mock_predict_station.side_effect = mock_predict_side_effect

        result = arima_predictor.predict_for_all_stations()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

        assert mock_predict_station.call_count == 4

    def test_predict_for_all_stations_with_no_params(self, mock_station_params_file):
        """Test prediction for all stations when no parameters are available."""
        with open(mock_station_params_file, "w") as f:
            json.dump({}, f)

        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": mock_station_params_file,
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()
            result = predictor.predict_for_all_stations()

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 0

    @patch("public_transport_watcher.predictor.arima_predictions.ArimaPredictor.predict_for_station")
    def test_predict_for_all_stations_with_exception(self, mock_predict_station, arima_predictor):
        """Test prediction for all stations when an exception occurs."""
        mock_predict_station.side_effect = Exception("Unexpected error")

        result = arima_predictor.predict_for_all_stations()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


class TestArimaPredictorParameterHandling:
    """Tests for ARIMA parameter handling."""

    def test_string_station_id_conversion(self, mock_station_params_file):
        """Test that string station IDs are properly converted to integers."""
        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": mock_station_params_file,
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()

            assert 70671 in predictor.station_params
            assert isinstance(list(predictor.station_params.keys())[0], int)

    def test_parameter_tuple_conversion(self, mock_station_params_file):
        """Test that parameters are stored as tuples."""
        with patch(
            "public_transport_watcher.predictor.arima_predictions.ARIMA_CONFIG",
            {
                "params_station_file": mock_station_params_file,
                "p_range": [0, 1, 2],
                "d_range": [0, 1],
                "q_range": [0, 1, 2],
            },
        ):
            predictor = ArimaPredictor()

            assert isinstance(predictor.station_params[70671], tuple)
            assert predictor.station_params[70671] == (1, 1, 2)
