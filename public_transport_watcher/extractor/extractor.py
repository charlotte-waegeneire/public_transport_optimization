from public_transport_watcher.extractor.configuration import EXTRACTION_CONFIG
from public_transport_watcher.extractor.extract import (
    extract_addresses_informations,
    extract_airquality_data,
    extract_navigo_validations,
    extract_stations_informations,
    process_traffic_data,
)
from public_transport_watcher.extractor.extract.real_time import (
    get_latest_air_quality_csv,
)
from public_transport_watcher.utils import get_query_result

from public_transport_watcher.logging_config import get_logger

logger = get_logger()


class Extractor:
    def __init__(self):
        self.extract_config = EXTRACTION_CONFIG

    def extract_stations_data(self):
        config = self.extract_config.get("stations")
        batch_size = config.get("batch_size", 100)
        extract_stations_informations(batch_size)

    def extract_navigo_validations(self):
        config = self.extract_config.get("navigo")
        existing_entries = get_query_result("get_existing_stations")
        if existing_entries.empty:
            logger.error("No existing stations found. Import stations data first.")
            return
        extract_navigo_validations(config)

    def extract_addresses_informations(self):
        config = self.extract_config.get("addresses", {})
        batch_size = config.get("batch_size", 1000)
        extract_addresses_informations(batch_size)

    def extract_traffic_data(self):
        return process_traffic_data()

    def extract_airquality_data(self):
        get_latest_air_quality_csv()
        config = self.extract_config.get("pollution", {})
        pollutants = config.get("pollutants", [])
        limits = config.get("limits", {})
        return extract_airquality_data(pollutants, limits)


if __name__ == "__main__":
    extractor = Extractor()
    extractor.extract_stations_data()
    extractor.extract_navigo_validations()
    extractor.extract_addresses_informations()
    traffic_data = extractor.extract_traffic_data()
    air_quality_data = extractor.extract_airquality_data() # needs to be scheduled
