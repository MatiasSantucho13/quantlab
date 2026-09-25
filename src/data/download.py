"""Public static archive downloader; no exchange trading/API credentials."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
from io import BytesIO
import json
from pathlib import Path
import urllib.request
from zipfile import ZipFile
import pandas as pd
from .validation import validate

BASE = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/4h"

def parse_archive(blob):
    with ZipFile(BytesIO(blob)) as z:
        names = [x for x in z.namelist() if x.endswith(".csv")]
        if len(names) != 1: raise ValueError("Expected one CSV")
        d = pd.read_csv(z.open(names[0]),header=None)
    stamp = pd.to_numeric(d[0])
    # Official spot archives switched from milliseconds to microseconds in 2025.
    ns = stamp.where(stamp >= 10**14, stamp * 1000) * 1000
    return pd.DataFrame({"timestamp":pd.to_datetime(ns,unit="ns",utc=True),
        **{c:d[i] for i,c in enumerate(["open","high","low","close","volume"],1)}})

def download(output, start="2022-01", end="2024-12"):
    months = list(pd.period_range(start,end,freq="M").astype(str))
    if not months: raise ValueError("Empty date range")
    def fetch(month):
        url = f"{BASE}/BTCUSDT-4h-{month}.zip"
        with urllib.request.urlopen(url,timeout=40) as response: blob=response.read()
        with urllib.request.urlopen(url+".CHECKSUM",timeout=40) as response:
            expected=response.read().decode().split()[0]
        digest=hashlib.sha256(blob).hexdigest()
        if digest != expected: raise ValueError(f"Checksum mismatch: {month}")
        return parse_archive(blob), {"url":url,"sha256":digest}
    with ThreadPoolExecutor(max_workers=6) as pool: items=list(pool.map(fetch,months))
    d, _ = validate(pd.concat([x[0] for x in items],ignore_index=True))
    output=Path(output); output.parent.mkdir(parents=True,exist_ok=True)
    d.to_csv(output)
    output.with_suffix(".json").write_text(json.dumps({"kind":"historical", "symbol":"BTCUSDT",
        "source":"Binance public spot archives", "documentation":"https://github.com/binance/binance-public-data",
        "frequency":"4h", "archives":[x[1] for x in items]},indent=2))
    return output

if __name__ == "__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",default="data/raw/btcusdt_4h.csv")
    p.add_argument("--start",default="2022-01"); p.add_argument("--end",default="2024-12")
    a=p.parse_args(); print(download(a.output,a.start,a.end))
