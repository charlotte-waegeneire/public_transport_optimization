import os
from pathlib import Path

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


def get_env_variable(var_name: str) -> str:
    """
    Get the value of an environment variable.

    Parameters
    ----------
    var_name : str
        The name of the environment variable.

    Returns
    -------
    str
        The value of the environment variable.

    Raises
    ------
    ValueError
        If the environment variable is not set.
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value
