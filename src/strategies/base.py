from abc import ABC, abstractmethod
from dataclasses import asdict

class BaseStrategy(ABC):
    @abstractmethod
    def generate_signals(self, data):
        """Target position (0 or 1) using information through this close only."""
    def get_parameters(self):
        return asdict(self)
