from public_transport_watcher.utils import get_sql_query

sql_files = [
    "get_existing_stations",
]

for sql_file in sql_files:
    globals()[sql_file] = get_sql_query(sql_file)
