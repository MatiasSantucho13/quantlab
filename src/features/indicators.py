import numpy as np
import pandas as pd

def features(data, periods_per_year, window=42):
    d=data.copy()
    d["simple_return"]=d.close.pct_change(fill_method=None)
    d["log_return"]=np.log(d.close).diff()
    d["rolling_mean"]=d.close.rolling(window).mean()
    d["rolling_std"]=d.close.rolling(window).std(ddof=1)
    d["rolling_volatility"]=d.simple_return.rolling(window).std(ddof=1)*np.sqrt(periods_per_year)
    return d

def distribution(series):
    r=series.dropna()
    return pd.Series({"mean":r.mean(),"median":r.median(),"std":r.std(ddof=1),
        "skewness":r.skew(),"excess_kurtosis":r.kurt(),
        **{f"q{q:g}":r.quantile(q) for q in [.01,.05,.25,.75,.95,.99]}})
