import numpy as np
import pandas as pd

def classify(data):
    """At bar open use only previous closes, including expanding vol threshold."""
    mean=data.close.rolling(180).mean()
    vol=data.close.pct_change(fill_method=None).rolling(42).std()
    threshold=vol.expanding(min_periods=180).median()
    trend=pd.Series(np.where(data.close >= mean,"up","down"),index=data.index)
    level=pd.Series(np.where(vol>threshold,"high_vol","low_vol"),index=data.index)
    labels=trend+" / "+level
    labels[mean.isna() | threshold.isna()]="warmup"
    return labels.shift(1,fill_value="warmup")

def by_regime(result, labels):
    d=result.bars.join(labels.rename("regime"))
    return d.groupby("regime").agg(bars=("return","size"),mean_bar_return=("return","mean"),
        bar_volatility=("return","std"),exposure=("exposure","mean"),
        worst_bar=("return","min"))
