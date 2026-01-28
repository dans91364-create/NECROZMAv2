"""
Base Strategy Class

All strategies must inherit from this base class and implement:
- create_patterns(): Create trading patterns from universe
- generate_signals(): Generate trading signals from patterns
"""

import pandas as pd
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    """
    
    def __init__(self, lookback: int = 14):
        """
        Initialize strategy.
        
        Args:
            lookback: Lookback period for calculations
        """
        self.lookback = lookback
        self.name = self.__class__.__name__
    
    @abstractmethod
    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """
        Create trading patterns from universe.
        
        Args:
            universe: DataFrame with OHLCV and indicators
            
        Returns:
            DataFrame with pattern features
        """
        raise NotImplementedError("Subclasses must implement create_patterns()")
    
    @abstractmethod
    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from patterns.
        
        Args:
            patterns: DataFrame with pattern features
            
        Returns:
            Series with trading signals (1=long, -1=short, 0=no trade)
        """
        raise NotImplementedError("Subclasses must implement generate_signals()")
    
    def __repr__(self):
        return f"{self.name}(lookback={self.lookback})"
