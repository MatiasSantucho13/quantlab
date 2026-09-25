import pandas as pd
from ..features.indicators import distribution

def risk(result):
    r=result.bars["return"]
    cutoff=r.quantile(.05)
    tail=r[r<=cutoff]
    return {"bar_var95_loss":-cutoff,"bar_expected_shortfall95_loss":-tail.mean(),
        "worst_bar":r.min(),"worst_6bar_compounded":((1+r).rolling(6).apply(lambda x:x.prod(),raw=True)-1).min(),
        "negative_bar_fraction":float((r<0).mean()),"downside_rms":(r.clip(upper=0).pow(2).mean())**.5}
