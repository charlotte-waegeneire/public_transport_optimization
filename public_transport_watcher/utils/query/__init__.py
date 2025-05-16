from public_transport_watcher.utils import get_sql_query

query_files = [
    "get_existing_stations",
    "get_top_10_stations",
    "get_validations_per_month_year",
]

for query_file in query_files:
    globals()[query_file] = get_sql_query(query_file)
