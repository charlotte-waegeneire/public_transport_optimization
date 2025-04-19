import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_datalake_file(data_category: str, folder: str, subfolder: str = None) -> list[str]:
    """
    Get the files path for a given data category and subfolder in the datalake.

    Parameters
    ----------
    data_category : str
        The category of data (e.g., "weather", "pollution").
    folder : str
        The folder within the data category.
    subfolder : str
        The subfolder within the data category.

    Returns
    -------
    list[str]
        A list of file paths within the specified folder and subfolder.
    """
    datalake_root = os.getenv("DATALAKE_ROOT")
    if not datalake_root:
        raise ValueError("DATALAKE_ROOT environment variable is not set.")

    if not data_category or not folder:
        raise ValueError("Both data_category and folder must be provided.")

    data_path = os.path.join(datalake_root, data_category, str(folder))
    if subfolder:
        data_path = os.path.join(data_path, str(subfolder))

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"The path {data_path} does not exist.")

    found_files = [
        os.path.join(data_path, f) for f in os.listdir(data_path) if os.path.isfile(os.path.join(data_path, f))
    ]
    if not found_files:
        raise FileNotFoundError(f"No files found in the path {data_path}.")

    return found_files
