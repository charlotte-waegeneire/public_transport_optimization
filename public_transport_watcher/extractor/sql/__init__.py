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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, f"{file_name}.sql")

    with open(file_path, "r", encoding="utf-8") as f:
        query = f.read()

    return query


sql_files = [
    "get_existing_stations",
]

for sql_file in sql_files:
    globals()[sql_file] = get_sql_query(sql_file)
