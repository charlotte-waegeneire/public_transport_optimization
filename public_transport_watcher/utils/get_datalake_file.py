import os
from pathlib import Path


from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_datalake_file(data_category: str, year: int, subfolder: str) -> list[str]:
    """
    Get the files path for a given data category and subfolder in the datalake.

    Parameters
    ----------
    data_category : str
        The category of data (e.g., "weather", "pollution").
    year : int
        The year of the data.
    subfolder : str
        The subfolder within the data category.
    """
    datalake_root = os.getenv("DATALAKE_ROOT")
    if not datalake_root:
        raise ValueError("DATALAKE_ROOT environment variable is not set.")

    data_path = os.path.join(datalake_root, data_category, str(year), subfolder)
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"The path {data_path} does not exist.")

    found_files = [
        os.path.join(data_path, f)
        for f in os.listdir(data_path)
        if os.path.isfile(os.path.join(data_path, f))
    ]
    if not found_files:
        raise FileNotFoundError(f"No files found in the path {data_path}.")

    return found_files
