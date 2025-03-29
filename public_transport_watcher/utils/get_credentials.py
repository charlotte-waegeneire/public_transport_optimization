import os
from pathlib import Path


from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_credentials() -> tuple[str, str, str, str, str]:
    """
    Get the database credentials from environment variables.

    Returns
    -------
    tuple
        A tuple containing the database user, password, host, port, and name.
    """
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    return db_user, db_password, db_host, db_port, db_name
