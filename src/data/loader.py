from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from .validation import validate

def load(path, frequency="4h"):
    path = Path(path)
    data, quality = validate(pd.read_csv(path), frequency)
    quality["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    sidecar = path.with_suffix(".json")
    metadata = json.loads(sidecar.read_text()) if sidecar.exists() else {
        "kind":"user-supplied, provenance unverified", "source":str(path)}
    return data, quality, metadata

def synthetic(path, n=6576, seed=42):
    """Engineering fixture only, never historical BTC evidence."""
    rng = np.random.default_rng(seed)
    r = rng.normal(0.00005, 0.012, n)
    opening = 30000 * np.exp(np.r_[0, np.cumsum(r[:-1])])
    close = opening * np.exp(r)
    spread = np.abs(rng.normal(0, .004, n))
    d = pd.DataFrame({"timestamp":pd.date_range("2022-01-01", periods=n, freq="4h", tz="UTC"),
        "open":opening,"high":np.maximum(opening, close)*(1+spread),
        "low":np.minimum(opening, close)/(1+spread),"close":close,
        "volume":rng.lognormal(8, .5, n)})
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(path,index=False)
    path.with_suffix(".json").write_text(json.dumps({"kind":"SYNTHETIC — NOT HISTORICAL BTC",
        "source":"seeded lognormal fixture", "seed":seed},indent=2))
    return path
