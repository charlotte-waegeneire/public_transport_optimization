from public_transport_watcher.utils import get_sql_query

get_top_10_stations = get_sql_query("get_top_10_stations")
get_validations_per_month_year = get_sql_query("get_validations_per_month_year")

__all__ = [
    "get_top_10_stations",
    "get_validations_per_month_year",
]
