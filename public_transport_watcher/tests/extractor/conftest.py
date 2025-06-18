"""Common fixtures for extractor tests."""

from datetime import datetime

import pandas as pd
import pytest

from public_transport_watcher.extractor.extractor import Extractor


@pytest.fixture
def extractor():
    """Create an Extractor instance for testing."""
    return Extractor()


@pytest.fixture
def mock_empty_df():
    """Create an empty DataFrame for testing."""
    return pd.DataFrame()


@pytest.fixture
def mock_stations_df():
    """Create a mock stations DataFrame for testing."""
    return pd.DataFrame(
        {
            "id": [1, 2],
            "name": ["Station 1", "Station 2"],
            "latitude": [48.8566, 48.8566],
            "longitude": [2.3522, 2.3522],
        }
    )


@pytest.fixture
def mock_navigo_df():
    """Create a mock Navigo validations DataFrame for testing."""
    return pd.DataFrame(
        {
            "ida": [1, 2],
            "libelle_arret": ["Station 1", "Station 2"],
            "jour": [datetime(2024, 3, 20), datetime(2024, 3, 20)],
            "tranche_horaire": ["10-11", "11-12"],
            "cat_day": ["JOHV", "JOHV"],
            "validations_horaires": [100, 150],
        }
    )


@pytest.fixture
def mock_addresses_df():
    """Create a mock addresses DataFrame for testing."""
    return pd.DataFrame({"street_name": ["Rue de la Paix", "Avenue des Champs-Élysées"], "C_AR": ["75001", "75008"]})


@pytest.fixture
def mock_transport_categories_df():
    """Create a mock transport categories DataFrame for testing."""
    return pd.DataFrame({"ID_Line": ["1", "2"], "TransportMode": ["metro", "rail"]})


@pytest.fixture
def mock_transport_lines_df():
    """Create a mock transport lines DataFrame for testing."""
    return pd.DataFrame(
        {"line_id": [1, 2], "name": ["Line 1", "Line 2"], "category_id": [1, 1], "color": ["#FFFF00", "#0000FF"]}
    )


@pytest.fixture
def mock_schedule_df():
    """Create a mock schedule DataFrame for testing."""
    return pd.DataFrame(
        {
            "arrival_timestamp": [datetime(2024, 3, 20, 10, 0), datetime(2024, 3, 20, 10, 5)],
            "stop_id": [1, 2],
            "next_station_id": [2, 3],
            "line_numeric_id": [1, 1],
            "journey_id": ["TRIP1", "TRIP1"],
        }
    )
