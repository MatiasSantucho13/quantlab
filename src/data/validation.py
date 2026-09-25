import numpy as np
import pandas as pd

COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]

def validate(data, frequency="4h"):
    """Sort safely; reject ambiguous duplicates, missing bars and invalid values."""
    if not set(COLUMNS).issubset(data.columns):
        raise ValueError(f"Required columns: {COLUMNS}")
    d = data[COLUMNS].copy()
    d["timestamp"] = pd.to_datetime(d.timestamp, utc=True, errors="raise")
    if len(d) < 2 or d.timestamp.isna().any():
        raise ValueError("Need at least two valid timestamps")
    was_sorted = d.timestamp.is_monotonic_increasing
    duplicates = int(d.timestamp.duplicated().sum())
    if duplicates:
        raise ValueError(f"Duplicate timestamps: {duplicates}")
    d = d.sort_values("timestamp").reset_index(drop=True)
    for c in COLUMNS[1:]:
        d[c] = pd.to_numeric(d[c], errors="raise")
    if not np.isfinite(d[COLUMNS[1:]].to_numpy()).all():
        raise ValueError("Missing/non-finite OHLCV: no forward filling permitted")
    if (d[["open", "high", "low", "close"]] <= 0).any().any() or (d.volume < 0).any():
        raise ValueError("Nonpositive price or negative volume")
    if ((d.high < d[["open", "close", "low"]].max(axis=1)) |
        (d.low > d[["open", "close", "high"]].min(axis=1))).any():
        raise ValueError("Inconsistent OHLC bounds")
    delta = pd.Timedelta(frequency)
    if not d.timestamp.diff().iloc[1:].eq(delta).all():
        raise ValueError("Missing timestamps or irregular sampling; repair source explicitly")
    return d.set_index("timestamp"), {"rows":len(d), "duplicates":0,
        "missing_bars":0, "missing_values":0, "input_sorted":bool(was_sorted),
        "frequency":frequency, "policy":"sort; fail on duplicates, gaps or missing values"}
