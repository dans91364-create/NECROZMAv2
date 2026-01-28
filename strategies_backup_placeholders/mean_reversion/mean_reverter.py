"""
🐉 NECROZMA - Original Mean Reverter Strategy

This is the original proven strategy that serves as the reference.
The strategy uses RSI-based mean reversion with dynamic position sizing.
"""

import pandas as pd
import numpy as np
from strategies.base import BaseStrategy


class MeanReverter(BaseStrategy):
    """
    The original NECROZMA mean reversion strategy.
    
    Strategy Logic:
    - Buy when RSI < 30 (oversold)
    - Sell when RSI > 70 (overbought)
    - Use lookback period for RSI calculation
    """
    
    def __init__(self, lookback: int = 14):
        super().__init__(lookback)
        self.oversold_threshold = 30
        self.overbought_threshold = 70
    
    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """
        Create mean reversion patterns.
        
        Args:
            universe: DataFrame with OHLCV and indicators
            
        Returns:
            DataFrame with pattern features
        """
        patterns = universe.copy()
        
        # Calculate RSI with custom lookback
        from ta.momentum import RSIIndicator
        rsi = RSIIndicator(close=patterns['close'], window=self.lookback)
        patterns['rsi'] = rsi.rsi()
        
        # Calculate price deviation from moving average
        patterns['sma'] = patterns['close'].rolling(window=self.lookback).mean()
        patterns['price_deviation'] = (patterns['close'] - patterns['sma']) / patterns['sma'] * 100
        
        # Calculate volatility
        patterns['volatility'] = patterns['close'].pct_change().rolling(window=self.lookback).std()
        
        return patterns
    
    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals based on RSI mean reversion.
        
        Args:
            patterns: DataFrame with pattern features
            
        Returns:
            Series with trading signals (1=long, -1=short, 0=no trade)
        """
        signals = pd.Series(0, index=patterns.index)
        
        # Ensure RSI column exists
        if 'rsi' not in patterns.columns:
            patterns = self.create_patterns(patterns)
        
        # Long signal: RSI oversold
        long_condition = patterns['rsi'] < self.oversold_threshold
        
        # Short signal: RSI overbought
        short_condition = patterns['rsi'] > self.overbought_threshold
        
        # Generate signals
        signals[long_condition] = 1
        signals[short_condition] = -1
        
        return signals
    
    def __repr__(self):
        return f"🐉 MeanReverter(lookback={self.lookback}, RSI<{self.oversold_threshold}/{self.overbought_threshold})"
