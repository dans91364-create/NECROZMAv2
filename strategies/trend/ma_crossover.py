"""
Ma Crossover Strategy

Placeholder for trend strategy.
"""

import pandas as pd
import numpy as np
from strategies.base import BaseStrategy


class MaCrossover(BaseStrategy):
    """
    Ma Crossover strategy implementation.
    """

    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """Create patterns from universe."""
        return universe.copy()

    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """Generate trading signals."""
        # Placeholder: Always return no signal
        return pd.Series(0, index=patterns.index)
