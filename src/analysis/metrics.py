import numpy as np
import pandas as pd
from .drawdown import drawdown

def metrics(result, periods_per_year):
    b=result.bars; r=b["return"]; t=result.trades
    total=b.equity.iloc[-1]/result.initial_capital-1
    years=len(b)/periods_per_year
    vol=r.std(ddof=1)*np.sqrt(periods_per_year)
    ann=np.expm1(np.log1p(total)/years) if years >= 1 else np.nan
    dd=drawdown(b.equity,result.initial_capital).min()
    wins=t.loc[t.pnl>0,"pnl"].sum(); losses=-t.loc[t.pnl<0,"pnl"].sum()
    return pd.Series({"total_return":total,"annualized_return":ann,"annualized_volatility":vol,
        "sharpe":r.mean()/r.std(ddof=1)*np.sqrt(periods_per_year) if r.std(ddof=1)>1e-14 else np.nan,
        "max_drawdown":dd,"calmar":ann/abs(dd) if dd<0 and np.isfinite(ann) else np.nan,
        "win_rate":(t["return"]>0).mean() if len(t) else np.nan,"trades":len(t),
        "average_trade":t["return"].mean(),"best_trade":t["return"].max(),"worst_trade":t["return"].min(),
        "exposure":b.exposure.mean(),"profit_factor":wins/losses if losses>0 else np.nan,
        "fees_paid":b.fees.sum(),"turnover":b.turnover.sum()})
