import os
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_env_variable

logger = get_logger()

_CURRENT_YEAR = datetime.now().year
_URL = f"https://files.data.gouv.fr/lcsqa/concentrations-de-polluants-atmospheriques-reglementes/temps-reel/{_CURRENT_YEAR}/"

_DATALAKE_ROOT = get_env_variable("DATALAKE_ROOT")
_DESTINATION_PATH = os.path.join(_DATALAKE_ROOT, "lcsqa", "latest")


def get_latest_air_quality_csv() -> str | None:
    """
    Retrieves the most recent CSV file from a server index page.
    """
    try:
        response = requests.get(_URL)
        if response.status_code != 200:
            logger.error(f"Failed to retrieve page: status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        csv_links = [
            link for link in soup.find_all("a") if link.get("href", "").endswith(".csv")
        ]

        if not csv_links:
            logger.error("No CSV files found on the page.")
            return None

        files_info = []
        for link in csv_links:
            parent_line = link.parent
            line_text = parent_line.get_text()
            match = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2})", line_text)

            if match:
                date_str = match.group(1)
                date_obj = datetime.strptime(date_str, "%d-%b-%Y %H:%M")

                size_match = re.search(r"(\d+)$", line_text.strip())
                size = int(size_match.group(1)) if size_match else 0

                files_info.append(
                    {"name": link.get("href"), "date": date_obj, "size": size}
                )

        if not files_info:
            logger.error("Failed to extract file date information.")
            return None

        most_recent_file = max(files_info, key=lambda x: x["date"])
        logger.info(
            f"Most recent CSV file: {most_recent_file['name']} "
            f"(from {most_recent_file['date'].strftime('%Y-%m-%d %H:%M')})"
        )

        file_url = _URL.rstrip("/") + "/" + most_recent_file["name"]
        file_response = requests.get(file_url)
        file_response.raise_for_status()

        os.makedirs(_DESTINATION_PATH, exist_ok=True)

        file_path = os.path.join(_DESTINATION_PATH, "raw_data.csv")
        with open(file_path, "wb") as f:
            f.write(file_response.content)

        logger.info(f"File successfully downloaded to: {file_path}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error while downloading file: {e}")

    except (OSError, IOError) as e:
        logger.error(f"File system error: {e}")

    except Exception as e:
        logger.error(f"Unexpected error while downloading file: {e}")
