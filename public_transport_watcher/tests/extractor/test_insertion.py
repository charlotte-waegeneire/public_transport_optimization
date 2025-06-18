"""Tests for the insertion functionality."""

from unittest.mock import patch


class TestStationsInsertion:
    """Tests for stations data insertion."""

    @patch("public_transport_watcher.extractor.extractor.insert_stations")
    @patch("public_transport_watcher.extractor.extractor.extract_stations_informations")
    def test_insert_stations_with_data(self, mock_extract, mock_insert, extractor, mock_stations_df):
        """Test stations insertion when data is available."""
        mock_extract.return_value = mock_stations_df
        extractor.extract_stations_data()
        mock_insert.assert_called_once_with(mock_stations_df, 100)

    @patch("public_transport_watcher.extractor.extractor.insert_stations")
    @patch("public_transport_watcher.extractor.extractor.extract_stations_informations")
    def test_insert_stations_without_data(self, mock_extract, mock_insert, extractor, mock_empty_df):
        """Test stations insertion when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_stations_data()
        mock_insert.assert_not_called()


class TestNavigoInsertion:
    """Tests for Navigo validations insertion."""

    @patch("public_transport_watcher.extractor.extractor.get_query_result")
    @patch("public_transport_watcher.extractor.extractor.extract_navigo_validations_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_navigo_validations")
    def test_insert_navigo_with_data(
        self, mock_insert, mock_extract, mock_get_query, extractor, mock_stations_df, mock_navigo_df
    ):
        """Test Navigo insertion when data is available."""
        mock_get_query.return_value = mock_stations_df
        mock_extract.return_value = mock_navigo_df
        extractor.extract_navigo_validations()
        mock_insert.assert_called_once_with(mock_navigo_df)

    @patch("public_transport_watcher.extractor.extractor.get_query_result")
    @patch("public_transport_watcher.extractor.extractor.extract_navigo_validations_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_navigo_validations")
    def test_insert_navigo_without_data(
        self, mock_insert, mock_extract, mock_get_query, extractor, mock_stations_df, mock_empty_df
    ):
        """Test Navigo insertion when no data is available."""
        mock_get_query.return_value = mock_stations_df
        mock_extract.return_value = mock_empty_df
        extractor.extract_navigo_validations()
        mock_insert.assert_not_called()


class TestAddressesInsertion:
    """Tests for addresses insertion."""

    @patch("public_transport_watcher.extractor.extractor.extract_addresses_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_addresses_informations")
    def test_insert_addresses_with_data(self, mock_insert, mock_extract, extractor, mock_addresses_df):
        """Test addresses insertion when data is available."""
        mock_extract.return_value = mock_addresses_df
        extractor.extract_addresses_informations()
        mock_insert.assert_called_once_with(mock_addresses_df, 1000)

    @patch("public_transport_watcher.extractor.extractor.extract_addresses_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_addresses_informations")
    def test_insert_addresses_without_data(self, mock_insert, mock_extract, extractor, mock_empty_df):
        """Test addresses insertion when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_addresses_informations()
        mock_insert.assert_not_called()


class TestTransportCategoriesInsertion:
    """Tests for transport categories insertion."""

    @patch("public_transport_watcher.extractor.extractor.extract_transport_categories_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_transport_categories")
    def test_insert_categories_with_data(self, mock_insert, mock_extract, extractor, mock_transport_categories_df):
        """Test transport categories insertion when data is available."""
        mock_extract.return_value = mock_transport_categories_df
        extractor.extract_categ_data()
        mock_insert.assert_called_once_with(mock_transport_categories_df)

    @patch("public_transport_watcher.extractor.extractor.extract_transport_categories_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_transport_categories")
    def test_insert_categories_without_data(self, mock_insert, mock_extract, extractor, mock_empty_df):
        """Test transport categories insertion when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_categ_data()
        mock_insert.assert_not_called()


class TestTransportLinesInsertion:
    """Tests for transport lines insertion."""

    @patch("public_transport_watcher.extractor.extractor.extract_transport_lines_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_transport_lines")
    def test_insert_lines_with_data(self, mock_insert, mock_extract, extractor, mock_transport_lines_df):
        """Test transport lines insertion when data is available."""
        mock_extract.return_value = mock_transport_lines_df
        extractor.extract_transport_data()
        mock_insert.assert_called_once_with(mock_transport_lines_df)

    @patch("public_transport_watcher.extractor.extractor.extract_transport_lines_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_transport_lines")
    def test_insert_lines_without_data(self, mock_insert, mock_extract, extractor, mock_empty_df):
        """Test transport lines insertion when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_transport_data()
        mock_insert.assert_not_called()


class TestScheduleInsertion:
    """Tests for schedule insertion."""

    @patch("public_transport_watcher.extractor.extractor.extract_schedule_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_schedule_informations")
    def test_insert_schedule_with_data(self, mock_insert, mock_extract, extractor, mock_schedule_df):
        """Test schedule insertion when data is available."""
        mock_extract.return_value = mock_schedule_df
        extractor.extract_schedule_data()
        mock_insert.assert_called_once_with(mock_schedule_df, extractor.extract_config.get("schedule", {}))

    @patch("public_transport_watcher.extractor.extractor.extract_schedule_informations")
    @patch("public_transport_watcher.extractor.extractor.insert_schedule_informations")
    def test_insert_schedule_without_data(self, mock_insert, mock_extract, extractor, mock_empty_df):
        """Test schedule insertion when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_schedule_data()
        mock_insert.assert_not_called()
