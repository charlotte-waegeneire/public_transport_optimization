"""Tests for the extraction functionality."""

from unittest.mock import patch


def test_extractor_initialization(extractor):
    """Test that the Extractor class initializes correctly."""
    assert hasattr(extractor, "extract_config")
    assert extractor.extract_config is not None


class TestStationsExtraction:
    """Tests for stations data extraction."""

    @patch("public_transport_watcher.extractor.extractor.extract_stations_informations")
    def test_extract_stations_with_data(self, mock_extract, extractor, mock_stations_df):
        """Test stations extraction when data is available."""
        mock_extract.return_value = mock_stations_df
        extractor.extract_stations_data()
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.extract_stations_informations")
    def test_extract_stations_without_data(self, mock_extract, extractor, mock_empty_df):
        """Test stations extraction when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_stations_data()
        mock_extract.assert_called_once()


class TestNavigoExtraction:
    """Tests for Navigo validations extraction."""

    @patch("public_transport_watcher.extractor.extractor.get_query_result")
    @patch("public_transport_watcher.extractor.extractor.extract_navigo_validations_informations")
    def test_extract_navigo_with_existing_stations(
        self, mock_extract, mock_get_query, extractor, mock_stations_df, mock_navigo_df
    ):
        """Test Navigo extraction when stations exist."""
        mock_get_query.return_value = mock_stations_df
        mock_extract.return_value = mock_navigo_df
        extractor.extract_navigo_validations()
        mock_get_query.assert_called_once_with("get_existing_stations")
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.get_query_result")
    @patch("public_transport_watcher.extractor.extractor.extract_navigo_validations_informations")
    def test_extract_navigo_without_stations(self, mock_extract, mock_get_query, extractor, mock_empty_df):
        """Test Navigo extraction when no stations exist."""
        mock_get_query.return_value = mock_empty_df
        extractor.extract_navigo_validations()
        mock_get_query.assert_called_once_with("get_existing_stations")
        mock_extract.assert_not_called()


class TestAddressesExtraction:
    """Tests for addresses extraction."""

    @patch("public_transport_watcher.extractor.extractor.extract_addresses_informations")
    def test_extract_addresses_with_data(self, mock_extract, extractor, mock_addresses_df):
        """Test addresses extraction when data is available."""
        mock_extract.return_value = mock_addresses_df
        extractor.extract_addresses_informations()
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.extract_addresses_informations")
    def test_extract_addresses_without_data(self, mock_extract, extractor, mock_empty_df):
        """Test addresses extraction when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_addresses_informations()
        mock_extract.assert_called_once()


class TestTransportCategoriesExtraction:
    """Tests for transport categories extraction."""

    @patch("public_transport_watcher.extractor.extractor.extract_transport_categories_informations")
    def test_extract_categories_with_data(self, mock_extract, extractor, mock_transport_categories_df):
        """Test transport categories extraction when data is available."""
        mock_extract.return_value = mock_transport_categories_df
        extractor.extract_categ_data()
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.extract_transport_categories_informations")
    def test_extract_categories_without_data(self, mock_extract, extractor, mock_empty_df):
        """Test transport categories extraction when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_categ_data()
        mock_extract.assert_called_once()


class TestTransportLinesExtraction:
    """Tests for transport lines extraction."""

    @patch("public_transport_watcher.extractor.extractor.extract_transport_lines_informations")
    def test_extract_lines_with_data(self, mock_extract, extractor, mock_transport_lines_df):
        """Test transport lines extraction when data is available."""
        mock_extract.return_value = mock_transport_lines_df
        extractor.extract_transport_data()
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.extract_transport_lines_informations")
    def test_extract_lines_without_data(self, mock_extract, extractor, mock_empty_df):
        """Test transport lines extraction when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_transport_data()
        mock_extract.assert_called_once()


class TestScheduleExtraction:
    """Tests for schedule extraction."""

    @patch("public_transport_watcher.extractor.extractor.extract_schedule_informations")
    def test_extract_schedule_with_data(self, mock_extract, extractor, mock_schedule_df):
        """Test schedule extraction when data is available."""
        mock_extract.return_value = mock_schedule_df
        extractor.extract_schedule_data()
        mock_extract.assert_called_once()

    @patch("public_transport_watcher.extractor.extractor.extract_schedule_informations")
    def test_extract_schedule_without_data(self, mock_extract, extractor, mock_empty_df):
        """Test schedule extraction when no data is available."""
        mock_extract.return_value = mock_empty_df
        extractor.extract_schedule_data()
        mock_extract.assert_called_once()
