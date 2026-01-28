"""
Ma Crossover Strategy

Simple Moving Average crossover strategy.
"""

import pandas as pd
import numpy as np
from strategies.base import BaseStrategy


class MaCrossover(BaseStrategy):
    """
    Moving Average Crossover strategy.
    
    Long when fast MA crosses above slow MA.
    Short when fast MA crosses below slow MA.
    """

    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """Create patterns from universe."""
        patterns = universe.copy()
        
        # Fast and slow MAs
        fast_period = self.lookback
        slow_period = self.lookback * 2
        
        patterns['ma_fast'] = patterns['close'].rolling(window=fast_period).mean()
        patterns['ma_slow'] = patterns['close'].rolling(window=slow_period).mean()
        
        return patterns

    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(0, index=patterns.index)
        
        if 'ma_fast' not in patterns.columns:
            patterns = self.create_patterns(patterns)
        
        # Long when fast > slow
        long_condition = patterns['ma_fast'] > patterns['ma_slow']
        
        # Short when fast < slow
        short_condition = patterns['ma_fast'] < patterns['ma_slow']
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
