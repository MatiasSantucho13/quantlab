from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    frequency: str = "4h"
    initial_capital: float = 10_000.0
    fee: float = 0.001
    slippage: float = 0.0

    @property
    def periods_per_year(self):
        import pandas as pd
        return pd.Timedelta(days=365.25) / pd.Timedelta(self.frequency)
