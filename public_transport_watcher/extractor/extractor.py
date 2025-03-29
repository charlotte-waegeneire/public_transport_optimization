from public_transport_watcher.extractor.extract import extract_navigo_validations

from public_transport_watcher.extractor.configuration import EXTRACTION_CONFIG


class Extractor:
    def __init__(self):
        self.extract_config = EXTRACTION_CONFIG
        self.batch_size = self.extract_config.get("batch_size")

    def extract_navigo_validations(self):
        config = self.extract_config.get("navigo")
        extract_navigo_validations(config, self.batch_size)


if __name__ == "__main__":
    extractor = Extractor()
    extractor.extract_navigo_validations()
