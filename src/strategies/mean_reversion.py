from dataclasses import dataclass
import pandas as pd
from .base import BaseStrategy

@dataclass
class MeanReversion(BaseStrategy):
    window: int = 42
    entry: float = 2.0
    exit: float = 0.0

    def __post_init__(self):
        if self.window < 2 or self.entry <= 0 or self.exit <= -self.entry:
            raise ValueError("Invalid z-score parameters")

    def generate_signals(self, data):
        mean=data.close.rolling(self.window).mean()
        std=data.close.rolling(self.window).std(ddof=1).replace(0,float("nan"))
        z=(data.close-mean)/std
        position=0; signals=[]
        for value in z:
            if pd.isna(value): position=0
            elif position == 0 and value < -self.entry: position=1
            elif position == 1 and value >= self.exit: position=0
            signals.append(position)
        return pd.Series(signals,index=data.index,dtype=int)
