import os


def get_sql_query(file_name: str) -> str:
    """
    Read an SQL file and return its content

    Parameters
    ----------
    file_name : str
        Name of the SQL file to read (without the .sql extension)

    Returns
    -------
        SQL file content
    """
    # Get the utils directory and the query subdirectory
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    query_dir = os.path.join(utils_dir, "query")

    # Look for the SQL file in the query subdirectory
    file_path = os.path.join(query_dir, f"{file_name}.sql")

    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    # If file not found, raise an error
    raise FileNotFoundError(f"SQL file not found: {file_name}.sql in {query_dir}")
