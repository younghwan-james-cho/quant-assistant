from __future__ import annotations
import os
from typing import List, Optional

try:
    import wrds
except ImportError:
    wrds = None  # type: ignore


def fetch_crsp_monthly_returns(
    permnos: List[int],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[dict]:
    """
    Download CRSP monthly returns (ret) for the provided PERMNOs via WRDS.

    Authentication:
    - Prefer ~/.pgpass for non-interactive secure auth.
    - Alternatively set WRDS_USERNAME (required) and optionally WRDS_PASSWORD.
    """
    if wrds is None:
        raise RuntimeError("wrds package not installed")

    username = os.getenv("WRDS_USERNAME")
    if not username:
        raise RuntimeError("WRDS_USERNAME environment variable must be set for WRDS access")

    if not permnos:
        return []

    perms = sorted({int(p) for p in permnos})
    perm_list = ",".join(str(p) for p in perms)

    where_clauses = [f"permno IN ({perm_list})"]
    if start_date:
        where_clauses.append(f"date >= '{start_date}'")
    if end_date:
        where_clauses.append(f"date <= '{end_date}'")
    where_sql = " AND ".join(where_clauses)

    sql = f"SELECT permno, date, ret FROM crsp.msf WHERE {where_sql} ORDER BY permno, date"

    conn = None
    try:
        password = os.getenv("WRDS_PASSWORD")
        if password:
            conn = wrds.Connection(wrds_username=username, wrds_password=password)
        else:
            conn = wrds.Connection(wrds_username=username)

        df = conn.raw_sql(sql, index_col=None)

        results: List[dict] = []
        for _, row in df.iterrows():
            results.append(
                {
                    "permno": int(row["permno"]),
                    "date": str(row["date"]),
                    "ret": None if row["ret"] is None else float(row["ret"]),
                }
            )
        return results
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
