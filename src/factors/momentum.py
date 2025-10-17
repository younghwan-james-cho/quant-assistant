from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_12_1_momentum(
    crsp_df: pd.DataFrame,
    date_col: str = "date",
    permno_col: str = "permno",
    ret_col: str = "ret",
    lookback: int = 12,
    skip: int = 1,
) -> pd.DataFrame:
    """
    Calculate the Jegadeesh-Titman style (12-1) momentum signal for each stock.

    This function computes, for each date and PERMNO, the cumulative return over
    `lookback` months ending `skip` months before the target date. Formally,
    the momentum at time t is:

        momentum_t = prod_{j=skip+1}^{skip+lookback} (1 + ret_{t-j}) - 1

    Defaults implement the common 12-1 specification (lookback=12, skip=1).

    Args:
        crsp_df: long-format DataFrame containing at least columns for PERMNO,
            date, and monthly returns. Expected rows like those returned by the
            CRSP fetcher: {'permno', 'date', 'ret'}.
        date_col: name of the date column (will be coerced to datetime).
        permno_col: name of the integer identifier column for stocks.
        ret_col: name of the monthly return column (decimal, e.g. 0.05 for 5%).
        lookback: number of months in formation period (default 12).
        skip: number of most-recent months to skip (default 1).

    Returns:
        DataFrame with columns ['date', 'permno', 'momentum'] where 'momentum'
        contains the cumulative return over the formation window (float) and
        is NaN when there isn't sufficient history.

    Notes / assumptions:
      - Missing returns in the formation window produce NaN momentum.
      - The function treats the input `date_col` as the reference month for
        which the momentum is produced (momentum at date t uses prior months
        ending `skip` months before t).
    """

    # Basic validation
    required = {date_col, permno_col, ret_col}
    if not required.issubset(crsp_df.columns):
        missing = required - set(crsp_df.columns)
        raise ValueError(f"Input DataFrame is missing required columns: {missing}")

    if lookback <= 0 or skip < 0:
        raise ValueError("lookback must be > 0 and skip must be >= 0")

    # Prepare dataframe
    df = crsp_df[[permno_col, date_col, ret_col]].copy()
    df = df.dropna(subset=[permno_col, date_col])
    df[date_col] = pd.to_datetime(df[date_col])
    # Ensure returns are numeric; keep NaN if conversion fails
    df[ret_col] = pd.to_numeric(df[ret_col], errors="coerce")

    # Sort and compute per-permno rolling product on shifted returns
    df = df.sort_values([permno_col, date_col])

    def _group_momentum(group: pd.DataFrame) -> pd.DataFrame:
        # (1 + r)
        one_plus = 1.0 + group[ret_col]
        # Shift forward so that the formation window ends `skip` months before
        # the target date. To get months t-(skip+1) ... t-(skip+lookback), we
        # shift by (skip + 1) and then take a rolling window of size lookback.
        shifted = one_plus.shift(skip + 1)
        # rolling product; require full window
        rolled = shifted.rolling(window=lookback, min_periods=lookback)
        prod = rolled.apply(lambda x: np.prod(x), raw=True)
        momentum = prod - 1.0
        result = group[[date_col]].copy()
        result["momentum"] = momentum.values
        return result

    out = df.groupby(permno_col, group_keys=False).apply(_group_momentum)
    out = out.reset_index()
    # keep only relevant columns and ensure types
    out = out[[date_col, permno_col, "momentum"]]
    out[permno_col] = out[permno_col].astype(int)

    return out
