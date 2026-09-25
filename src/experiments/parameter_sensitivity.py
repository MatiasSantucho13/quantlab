import numpy as np
import pandas as pd
from ..strategies.momentum import Momentum
from ..backtest.engine import run
from ..analysis.metrics import metrics

def split(data):
    n=len(data); a=int(n*.6); b=int(n*.8)
    if a < 180 or b <= a or b >= n: raise ValueError("Need >=300 observations")
    return {"train":data.iloc[:a],"validation":data.iloc[a:b],"test":data.iloc[b:]}

def experiment(train, validation, config):
    """Function has no test input. Select by validation net Sharpe; deterministic ties."""
    history=pd.concat([train,validation]); rows=[]
    for fast in (10,20,30):
        for slow in (50,100,150):
            strategy=Momentum(fast,slow)
            for name,part in [("train",train),("validation",validation)]:
                signals=strategy.generate_signals(history).loc[part.index]
                result=run(part,signals,config.initial_capital,config.fee,config.slippage)
                rows.append({"fast":fast,"slow":slow,"split":name,**metrics(result,config.periods_per_year).to_dict()})
    table=pd.DataFrame(rows)
    candidates=table[table.split=="validation"].copy()
    candidates["score"]=candidates.sharpe.fillna(-np.inf)
    selected=candidates.sort_values(["score","fast","slow"],ascending=[False,True,True]).iloc[0]
    return table, Momentum(int(selected.fast),int(selected.slow))
