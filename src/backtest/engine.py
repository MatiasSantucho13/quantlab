from dataclasses import dataclass
import numpy as np
import pandas as pd
from .costs import check_costs, buy_units, sell_value

@dataclass
class BacktestResult:
    bars: pd.DataFrame
    trades: pd.DataFrame
    orders: pd.DataFrame
    initial_capital: float

def run(data, signals, initial_capital=10000., fee=.001, slippage=0., benchmark=False):
    """Close t signal executes at open t+1. Last close liquidates by prior convention.

    Cash/units ledger, all-in long or cash; no rebalancing while holding.
    Open gaps accrue to the prior holding, never to a new entry.
    Benchmark buys first open. All results end flat for comparable net trade metrics.
    """
    check_costs(fee,slippage)
    if not np.isfinite(initial_capital) or initial_capital <= 0 or len(data)<2:
        raise ValueError("Positive capital and >=2 bars required")
    if not signals.index.equals(data.index) or not signals.isin([0,1]).all():
        raise ValueError("Signals must align exactly and contain only 0/1")
    targets=signals.shift(1,fill_value=0).astype(int)
    if benchmark: targets[:]=1
    cash=float(initial_capital); units=0.; entry=None; records=[]; trades=[]; orders=[]
    previous=initial_capital
    for i,(timestamp,row) in enumerate(data.iterrows()):
        target=int(targets.iloc[i]); fees=0.; turnover=0.
        if target and units == 0:
            invested=cash
            units,charge,price=buy_units(cash,row.open,fee,slippage)
            cash=0.; fees+=charge; turnover+=units*price
            entry=(timestamp, invested, price)
            orders.append((timestamp,"buy",price,units,charge,"open"))
        elif not target and units > 0:
            cash,charge,price=sell_value(units,row.open,fee,slippage)
            fees+=charge; turnover+=units*price
            orders.append((timestamp,"sell",price,units,charge,"open"))
            trades.append((entry[0],timestamp,entry[1],cash,cash/entry[1]-1,cash-entry[1],False))
            units=0.; entry=None
        exposed=float(units>0)
        if i == len(data)-1 and units > 0:
            cash,charge,price=sell_value(units,row.close,fee,slippage)
            fees+=charge; turnover+=units*price
            orders.append((timestamp,"sell",price,units,charge,"terminal_close"))
            trades.append((entry[0],timestamp,entry[1],cash,cash/entry[1]-1,cash-entry[1],True))
            units=0.
        equity=cash+units*row.close
        records.append((timestamp,target,exposed,units,cash,equity,equity/previous-1,fees,turnover))
        previous=equity
    bars=pd.DataFrame(records,columns=["timestamp","target","exposure","units","cash","equity","return","fees","turnover"]).set_index("timestamp")
    return BacktestResult(bars,pd.DataFrame(trades,columns=["entry_time","exit_time","invested","proceeds","return","pnl","terminal_exit"]),
        pd.DataFrame(orders,columns=["timestamp","side","price","units","fee","execution"]),initial_capital)
