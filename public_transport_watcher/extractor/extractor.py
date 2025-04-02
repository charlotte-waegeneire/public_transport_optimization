from public_transport_watcher.extractor.configuration import EXTRACTION_CONFIG
from public_transport_watcher.extractor.extract import (
    extract_navigo_validations,
    extract_stations_informations,
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


if __name__ == "__main__":
    extractor = Extractor()
    extractor.extract_stations_data()
    # extractor.extract_navigo_validations()
