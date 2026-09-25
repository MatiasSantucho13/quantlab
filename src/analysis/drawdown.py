import numpy as np

def drawdown(equity, initial_capital):
    peak=equity.cummax().clip(lower=initial_capital)
    return equity/peak-1
