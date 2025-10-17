import os
import wrds
from typing import List, Optional
import pandas as pd
from src.assistant.utils.logging import logger


def fetch_crsp_data(
    permnos: List[int], start_date: Optional[str] = None, end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch CRSP monthly stock returns for the given permnos and date range.

    Args:
        permnos (List[int]): List of permnos to fetch data for.
        start_date (Optional[str]): Start date in YYYY-MM-DD format.
        end_date (Optional[str]): End date in YYYY-MM-DD format.

    Returns:
        pd.DataFrame: DataFrame containing the CRSP data.
    """
    conn = None
    try:
        conn = wrds.Connection(wrds_username=os.getenv("WRDS_USERNAME"))
        sql_query = """
        SELECT permno, date, ret
        FROM crsp.msf
        WHERE permno IN %s
        """
        params = (tuple(permnos),)
        if start_date:
            sql_query += " AND date >= %s"
            params += (start_date,)
        if end_date:
            sql_query += " AND date <= %s"
            params += (end_date,)

        df = conn.raw_sql(sql_query, params=params)
        return df

    except Exception as e:
        logger.error(f"Failed to fetch CRSP data: {e}")
        return pd.DataFrame()

    finally:
        if conn:
            conn.close()
