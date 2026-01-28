"""
Atr Breakout Strategy

ATR-based breakout strategy.
"""

import pandas as pd
import numpy as np
from strategies.base import BaseStrategy


class AtrBreakout(BaseStrategy):
    """
    ATR Breakout strategy.
    
    Long when price breaks above MA + 2*ATR.
    Short when price breaks below MA - 2*ATR.
    """

    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """Create patterns from universe."""
        patterns = universe.copy()
        
        from ta.volatility import AverageTrueRange
        
        # Calculate ATR
        atr = AverageTrueRange(
            high=patterns['high'],
            low=patterns['low'],
            close=patterns['close'],
            window=self.lookback
        )
        patterns['atr'] = atr.average_true_range()
        
        # Calculate moving average
        patterns['ma'] = patterns['close'].rolling(window=self.lookback).mean()
        
        # Breakout levels
        patterns['upper_band'] = patterns['ma'] + 2 * patterns['atr']
        patterns['lower_band'] = patterns['ma'] - 2 * patterns['atr']
        
        return patterns

    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        signals = pd.Series(0, index=patterns.index)
        
        if 'upper_band' not in patterns.columns:
            patterns = self.create_patterns(patterns)
        
        # Long on breakout above
        long_condition = patterns['close'] > patterns['upper_band']
        
        # Short on breakout below
        short_condition = patterns['close'] < patterns['lower_band']
        
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
