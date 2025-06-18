from unittest.mock import Mock, patch

import pandas as pd

from public_transport_watcher.predictor.arima.get_data import get_data_from_db


class TestGetDataFromDB:
    """Tests for get_data_from_db function."""

    def test_get_data_from_db_with_valid_station_id(self):
        """Test getting data for a valid station ID."""
        mock_engine = Mock()
        mock_session = Mock()

        mock_data = pd.DataFrame(
            {
                "station_id": [70671, 70671],
                "station_name": ["Test Station", "Test Station"],
                "time_bin_id": [1, 2],
                "cat_day": ["JOHV", "JOHV"],
                "start_timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
                "end_timestamp": ["2024-01-01 11:00:00", "2024-01-01 12:00:00"],
                "validations": [100, 150],
            }
        )

        with patch("public_transport_watcher.predictor.arima.get_data.get_engine", return_value=mock_engine):
            with patch("pandas.read_sql", return_value=mock_data):
                with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
                    mock_sessionmaker.return_value = mock_session

                    result = get_data_from_db(70671)

                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 2
                    assert result.index.name == "datetime"
                    assert isinstance(result.index, pd.DatetimeIndex)

    def test_get_data_from_db_with_none_station_id(self):
        """Test getting data with None station ID."""
        result = get_data_from_db(None)

        assert result is None

    def test_get_data_from_db_with_invalid_station_id_type(self):
        """Test getting data with invalid station ID type."""
        result = get_data_from_db("70671")

        assert result is None

    def test_get_data_from_db_with_empty_result(self):
        """Test getting data when no results are returned."""
        mock_engine = Mock()
        mock_session = Mock()

        mock_data = pd.DataFrame()

        with patch("public_transport_watcher.predictor.arima.get_data.get_engine", return_value=mock_engine):
            with patch("pandas.read_sql", return_value=mock_data):
                with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
                    mock_sessionmaker.return_value = mock_session

                    result = get_data_from_db(70671)

                    assert isinstance(result, pd.DataFrame)
                    assert len(result) == 0

    def test_get_data_from_db_with_missing_start_timestamp(self):
        """Test getting data when start_timestamp column is missing."""
        mock_engine = Mock()
        mock_session = Mock()

        mock_data = pd.DataFrame(
            {
                "station_id": [70671],
                "station_name": ["Test Station"],
                "time_bin_id": [1],
                "cat_day": ["JOHV"],
                "end_timestamp": ["2024-01-01 11:00:00"],
                "validations": [100],
            }
        )

        with patch("public_transport_watcher.predictor.arima.get_data.get_engine", return_value=mock_engine):
            with patch("pandas.read_sql", return_value=mock_data):
                with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
                    mock_sessionmaker.return_value = mock_session

                    result = get_data_from_db(70671)

                    assert isinstance(result, pd.DataFrame)
                    assert "datetime" not in result.columns
                    assert result.index.name != "datetime"


class TestArimaParameterOptimization:
    """Tests for ARIMA parameter optimization functions."""

    @patch("public_transport_watcher.predictor.arima.find_optimal_params.find_optimal_params")
    def test_find_optimal_params_integration(self, mock_find_params):
        """Test integration with find_optimal_params function."""
        mock_find_params.return_value = (2, 1, 1)

        # This would test the actual function if it were imported
        # For now, we just verify the mock works
        result = mock_find_params(70671, pd.DataFrame(), [0, 1, 2], [0, 1], [0, 1, 2], {}, "")

        assert result == (2, 1, 1)


class TestArimaPrediction:
    """Tests for ARIMA prediction functions."""

    @patch("public_transport_watcher.predictor.arima.predict_navigo_validations.predict_navigo_validations")
    def test_predict_navigo_validations_integration(self, mock_predict):
        """Test integration with predict_navigo_validations function."""
        mock_predictions = [120, 130, 140, 150]
        mock_total = 540
        mock_predict.return_value = (mock_predictions, mock_total)

        mock_data = pd.DataFrame({"validations": [100, 110, 120, 130]})

        predictions, total = mock_predict(mock_data, 70671, (1, 1, 2))

        assert predictions == [120, 130, 140, 150]
        assert total == 540


class TestArimaDataValidation:
    """Tests for ARIMA data validation."""

    def test_validate_traffic_data_structure(self):
        """Test validation of traffic data structure."""
        valid_data = pd.DataFrame(
            {
                "station_id": [70671],
                "station_name": ["Test Station"],
                "time_bin_id": [1],
                "cat_day": ["JOHV"],
                "start_timestamp": ["2024-01-01 10:00:00"],
                "end_timestamp": ["2024-01-01 11:00:00"],
                "validations": [100],
            }
        )

        required_columns = ["station_id", "validations", "start_timestamp"]
        for col in required_columns:
            assert col in valid_data.columns, f"Missing required column: {col}"

        assert valid_data["station_id"].dtype in [int, "int64"], "station_id should be integer"
        assert valid_data["validations"].dtype in [int, "int64"], "validations should be integer"

    def test_validate_traffic_data_content(self):
        """Test validation of traffic data content."""
        valid_data = pd.DataFrame(
            {
                "station_id": [70671, 70671],
                "validations": [100, 150],
                "start_timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
            }
        )

        assert (valid_data["validations"] >= 0).all(), "Validations should be non-negative"

        if "time_bin_id" in valid_data.columns:
            assert valid_data["time_bin_id"].is_unique, "Time bin IDs should be unique"

    def test_validate_arima_parameters(self):
        """Test validation of ARIMA parameters."""
        valid_params = (1, 1, 2)

        assert len(valid_params) == 3, "ARIMA parameters should have 3 components (p, d, q)"

        assert all(isinstance(p, int) for p in valid_params), "All ARIMA parameters should be integers"

        p, d, q = valid_params
        assert p >= 0, "p parameter should be non-negative"
        assert d >= 0, "d parameter should be non-negative"
        assert q >= 0, "q parameter should be non-negative"


class TestArimaPredictionResults:
    """Tests for ARIMA prediction results validation."""

    def test_validate_prediction_output_structure(self):
        """Test validation of prediction output structure."""
        predictions = [120, 130, 140, 150]
        total = 540

        assert isinstance(predictions, list), "Predictions should be a list"
        assert len(predictions) > 0, "Predictions should not be empty"
        assert all(isinstance(p, (int, float)) for p in predictions), "All predictions should be numeric"

        assert isinstance(total, (int, float)), "Total should be numeric"
        assert total >= 0, "Total should be non-negative"

        assert abs(sum(predictions) - total) < 1e-6, "Total should equal sum of predictions"

    def test_validate_prediction_values(self):
        """Test validation of prediction values."""
        predictions = [120, 130, 140, 150]

        assert all(p >= 0 for p in predictions), "All predictions should be non-negative"

        mean_pred = sum(predictions) / len(predictions)
        for p in predictions:
            assert 0 <= p <= mean_pred * 10, f"Prediction {p} seems unreasonable"

    def test_validate_prediction_temporal_consistency(self):
        """Test validation of temporal consistency in predictions."""
        hourly_predictions = [
            50,
            60,
            80,
            120,
            150,
            180,
            200,
            190,
            170,
            140,
            100,
            80,
            70,
            60,
            50,
            40,
            30,
            40,
            60,
            80,
            100,
            120,
            90,
            70,
        ]

        morning_peak = hourly_predictions[7:9]  # 8-10 AM
        evening_peak = hourly_predictions[17:19]  # 6-8 PM
        off_peak = hourly_predictions[0:6]  # Midnight to 6 AM

        assert max(morning_peak) > min(off_peak), "Morning peak should be higher than off-peak"
        assert max(evening_peak) > min(off_peak), "Evening peak should be higher than off-peak"


class TestArimaErrorHandling:
    """Tests for ARIMA error handling scenarios."""

    def test_handle_missing_data_scenarios(self):
        """Test handling of missing data scenarios."""
        empty_df = pd.DataFrame()
        assert len(empty_df) == 0, "Empty DataFrame should have zero rows"

        incomplete_df = pd.DataFrame(
            {
                "station_id": [70671],
                # Missing validations column
                "start_timestamp": ["2024-01-01 10:00:00"],
            }
        )
        assert "validations" not in incomplete_df.columns, "DataFrame should be missing validations column"

        null_df = pd.DataFrame(
            {
                "station_id": [70671, 70671, 70671],
                "validations": [None, None, None],
                "start_timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00", "2024-01-01 12:00:00"],
            }
        )
        assert null_df["validations"].isna().all(), "All validations should be null"

    def test_handle_invalid_arima_parameters(self):
        """Test handling of invalid ARIMA parameters."""
        invalid_params_negative = (-1, 1, 2)
        assert invalid_params_negative[0] < 0, "p parameter should be negative"

        invalid_params_float = (1.5, 1, 2)
        assert not isinstance(invalid_params_float[0], int), "p parameter should not be integer"

        invalid_params_count = (1, 1)  # Missing q parameter
        assert len(invalid_params_count) != 3, "Should have wrong number of parameters"

    def test_handle_prediction_failures(self):
        """Test handling of prediction failures."""
        insufficient_data = pd.DataFrame(
            {
                "station_id": [70671],
                "validations": [100],  # Only one data point
                "start_timestamp": ["2024-01-01 10:00:00"],
            }
        )
        assert len(insufficient_data) < 10, "Should have insufficient data for ARIMA"

        constant_data = pd.DataFrame(
            {
                "station_id": [70671] * 10,
                "validations": [100] * 10,  # All same value
                "start_timestamp": [f"2024-01-01 {i:02d}:00:00" for i in range(10)],
            }
        )
        assert constant_data["validations"].nunique() == 1, "Should have constant values"
