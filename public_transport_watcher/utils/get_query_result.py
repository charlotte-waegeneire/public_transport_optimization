"""Utility module to execute SQL queries and return results as pandas DataFrames."""

from typing import Dict, List, Optional, Union

import pandas as pd

from public_transport_watcher.extractor.sql import get_sql_query

from .get_engine import get_engine


def get_query_result(
    query_name: str,
    params: Optional[Union[Dict, List, tuple]] = None,
    index_col: Optional[Union[str, List[str]]] = None,
) -> pd.DataFrame:
    """
    Execute a named SQL query and return results as a pandas DataFrame.

    The function loads the SQL query from a file in the sql directory,
    executes it with optional parameters, and returns the results.

    Parameters
    ----------
    query_name : str
        Name of the SQL query file (without .sql extension)
    params : Optional[Union[Dict, List, tuple]], default=None
        Parameters to bind to the query
    index_col : Optional[Union[str, List[str]]], default=None
        Column(s) to set as index in the returned DataFrame

    Returns
    -------
        DataFrame containing the query results
    """
    query = get_sql_query(query_name)
    engine = get_engine()

    df = pd.read_sql_query(
        sql=query,
        con=engine,
        params=params,
        index_col=index_col,
    )

    engine.dispose()

    return df
