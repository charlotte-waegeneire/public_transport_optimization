from public_transport_watcher.extractor.configuration import EXTRACTION_CONFIG
from public_transport_watcher.extractor.extract import (
    extract_addresses_informations,
    extract_air_quality_informations,
    extract_navigo_validations_informations,
    extract_schedule_informations,
    extract_stations_informations,
    extract_traffic_informations,
    extract_transport_categories_informations,
    extract_transport_lines_informations,
)
from public_transport_watcher.extractor.extract.real_time import (
    extract_weather_informations,
    get_latest_air_quality_csv,
)
from public_transport_watcher.extractor.insert import (
    insert_addresses_informations,
    insert_navigo_validations,
    insert_schedule_informations,
    insert_stations,
    insert_transport_categories,
    insert_transport_lines,
)
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_query_result

logger = get_logger()


class Extractor:
    def __init__(self):
        self.extract_config = EXTRACTION_CONFIG

    def extract_stations_data(self):
        config = self.extract_config.get("stations")
        batch_size = config.get("batch_size", 1000)
        stations_df = extract_stations_informations()
        if not stations_df.empty:
            insert_stations(stations_df, batch_size)

    def extract_navigo_validations(self):
        config = self.extract_config.get("navigo")
        existing_entries = get_query_result("get_existing_stations")
        if existing_entries.empty:
            logger.error("No existing stations found. Import stations data first.")
            return

        navigo_df = extract_navigo_validations_informations(config)
        if not navigo_df.empty:
            insert_navigo_validations(navigo_df)

    def extract_addresses_informations(self):
        config = self.extract_config.get("addresses", {})
        batch_size = config.get("batch_size", 1000)
        addresses_df = extract_addresses_informations()
        if not addresses_df.empty:
            insert_addresses_informations(addresses_df, batch_size)

    def extract_traffic_data(self):
        return extract_traffic_informations()

    def extract_air_quality_data(self):
        get_latest_air_quality_csv()
        config = self.extract_config.get("pollution", {})
        pollutants = config.get("pollutants", [])
        limits = config.get("limits", {})
        return extract_air_quality_informations(pollutants, limits)

    def extract_weather_data(self):
        config = self.extract_config.get("weather", {})
        return extract_weather_informations(config)

    def extract_categ_data(self):
        categ_df = extract_transport_categories_informations()
        if not categ_df.empty:
            insert_transport_categories(categ_df)

    def extract_transport_data(self):
        transport_df = extract_transport_lines_informations()
        if not transport_df.empty:
            insert_transport_lines(transport_df)

    def extract_schedule_data(self):
        config = self.extract_config.get("schedule", {})
        schedule_df = extract_schedule_informations()
        if not schedule_df.empty:
            insert_schedule_informations(schedule_df, config)


if __name__ == "__main__":
    extractor = Extractor()
    extractor.extract_stations_data()
    extractor.extract_navigo_validations()
    extractor.extract_addresses_informations()
    extractor.extract_categ_data()
    extractor.extract_transport_data()
    extractor.extract_schedule_data()
    # traffic_data = extractor.extract_traffic_data()  # needs to be scheduled
    # air_quality_data = extractor.extract_air_quality_data()  # needs to be scheduled
    # weather_data = extractor.extract_weather_data()  # needs to be scheduled
