"""
Rsi Momentum Strategy

RSI momentum breakout strategy.
"""

import pandas as pd
import numpy as np
from strategies.base import BaseStrategy


class RsiMomentum(BaseStrategy):
    """
    RSI Momentum strategy.
    
    Long when RSI crosses above 50 (bullish momentum).
    Short when RSI crosses below 50 (bearish momentum).
    """

    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """Create patterns from universe."""
        patterns = universe.copy()
        
        from ta.momentum import RSIIndicator
        rsi = RSIIndicator(close=patterns['close'], window=self.lookback)
        patterns['rsi'] = rsi.rsi()
        
        return patterns

    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(0, index=patterns.index)
        
        if 'rsi' not in patterns.columns:
            patterns = self.create_patterns(patterns)
        
        # Long when RSI > 50 (momentum up)
        long_condition = patterns['rsi'] > 50
        
        # Short when RSI < 50 (momentum down)
        short_condition = patterns['rsi'] < 50
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
