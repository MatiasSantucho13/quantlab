from dataclasses import dataclass
from .base import BaseStrategy

@dataclass
class Momentum(BaseStrategy):
    fast: int = 20
    slow: int = 100

    def __post_init__(self):
        if not (1 <= self.fast < self.slow): raise ValueError("Require 1 <= fast < slow")

    def generate_signals(self, data):
        fast=data.close.rolling(self.fast).mean()
        slow=data.close.rolling(self.slow).mean()
        return (fast > slow).astype(int)
