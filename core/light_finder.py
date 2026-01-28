#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - LIGHT FINDER

Multi-Objective Strategy Ranking System
"Finding the 13 Legendaries among thousands"

Metrics:
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside risk only)
- Calmar Ratio (return / max drawdown)
- Win Rate (% profitable trades)
- Profit Factor (gross profit / gross loss)
- Max Drawdown (worst peak-to-trough)
- Expectancy (average $ per trade)
- Total Return (absolute performance)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple

class LightFinder:
    """
    Multi-objective strategy ranking system.
    
    Usage:
        finder = LightFinder()
        ranking = finder.rank_strategies(backtest_results)
        top_13 = finder.get_legendaries(ranking)
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Initialize with metric weights for composite score.
        
        Default weights:
            sharpe_ratio: 0.25
            sortino_ratio: 0.20
            calmar_ratio: 0.15
            win_rate: 0.15
            profit_factor: 0.15
            max_drawdown: 0.10 (inverted - lower is better)
        """
        self.weights = weights or {
            'sharpe_ratio': 0.25,
            'sortino_ratio': 0.20,
            'calmar_ratio': 0.15,
            'win_rate': 0.15,
            'profit_factor': 0.15,
            'max_drawdown': 0.10
        }
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sharpe Ratio."""
        excess_returns = returns - risk_free_rate
        if excess_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / excess_returns.std()
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.0) -> float:
        """Calculate Sortino Ratio (downside deviation only)."""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0
        return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
    
    def calculate_calmar_ratio(self, total_return: float, max_drawdown: float) -> float:
        """Calculate Calmar Ratio (return / max drawdown)."""
        if max_drawdown == 0:
            return 0.0
        return total_return / abs(max_drawdown)
    
    def calculate_profit_factor(self, trades: List[Dict]) -> float:
        """Calculate Profit Factor (gross profit / gross loss)."""
        gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in trades if t['profit'] < 0))
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        return gross_profit / gross_loss
    
    def calculate_expectancy(self, trades: List[Dict]) -> float:
        """Calculate Expectancy (average profit per trade)."""
        if len(trades) == 0:
            return 0.0
        return sum(t['profit'] for t in trades) / len(trades)
    
    def calculate_all_metrics(self, result: Dict) -> Dict[str, float]:
        """Calculate all metrics for a single strategy result."""
        equity_curve = pd.Series(result.get('equity_curve', []))
        returns = equity_curve.pct_change().dropna()
        trades = result.get('trades', [])
        
        metrics = {
            'total_return': result.get('total_return', 0.0),
            'num_trades': result.get('num_trades', 0),
            'win_rate': result.get('win_rate', 0.0),
            'max_drawdown': abs(result.get('max_drawdown', 0.0)),
            'sharpe_ratio': self.calculate_sharpe_ratio(returns),
            'sortino_ratio': self.calculate_sortino_ratio(returns),
            'calmar_ratio': self.calculate_calmar_ratio(
                result.get('total_return', 0.0),
                result.get('max_drawdown', 0.0)
            ),
            'profit_factor': self.calculate_profit_factor(trades),
            'expectancy': self.calculate_expectancy(trades)
        }
        
        return metrics
    
    def calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """
        Calculate composite score from weighted metrics.
        
        Normalizes each metric to 0-1 scale before weighting.
        """
        score = 0.0
        
        # Sharpe (typical range -2 to 4, normalize to 0-1)
        sharpe_norm = min(max((metrics['sharpe_ratio'] + 2) / 6, 0), 1)
        score += self.weights['sharpe_ratio'] * sharpe_norm
        
        # Sortino (typical range -2 to 6, normalize to 0-1)
        sortino_norm = min(max((metrics['sortino_ratio'] + 2) / 8, 0), 1)
        score += self.weights['sortino_ratio'] * sortino_norm
        
        # Calmar (typical range 0 to 10, normalize to 0-1)
        calmar_norm = min(max(metrics['calmar_ratio'] / 10, 0), 1)
        score += self.weights['calmar_ratio'] * calmar_norm
        
        # Win rate (already 0-100, normalize to 0-1)
        win_rate_norm = metrics['win_rate'] / 100
        score += self.weights['win_rate'] * win_rate_norm
        
        # Profit factor (typical range 0 to 5, normalize to 0-1)
        pf_norm = min(max(metrics['profit_factor'] / 5, 0), 1)
        score += self.weights['profit_factor'] * pf_norm
        
        # Max drawdown (inverted - lower is better, typical 0-100%)
        dd_norm = 1 - min(metrics['max_drawdown'] / 100, 1)
        score += self.weights['max_drawdown'] * dd_norm
        
        return score
    
    def rank_strategies(self, backtest_results: Dict[str, Dict]) -> pd.DataFrame:
        """
        Rank all strategies by composite score.
        
        Args:
            backtest_results: Dict mapping strategy_key to result dict
            
        Returns:
            DataFrame with ranked strategies
        """
        rows = []
        
        for key, result in backtest_results.items():
            # Parse key (format: strategy_risk_level)
            parts = key.rsplit('_risk_', 1)
            strategy_name = parts[0]
            risk_level = float(parts[1]) if len(parts) > 1 else 0.0
            
            # Calculate all metrics
            metrics = self.calculate_all_metrics(result)
            metrics['strategy'] = strategy_name
            metrics['risk_level'] = risk_level
            
            # Calculate composite score
            metrics['composite_score'] = self.calculate_composite_score(metrics)
            
            rows.append(metrics)
        
        # Create DataFrame and sort by composite score
        df = pd.DataFrame(rows)
        df = df.sort_values('composite_score', ascending=False).reset_index(drop=True)
        df.insert(0, 'rank', range(1, len(df) + 1))
        
        return df
    
    def get_legendaries(self, ranking: pd.DataFrame, n: int = 13) -> pd.DataFrame:
        """Get top N strategies (the Legendaries)."""
        return ranking.head(n).copy()
    
    def get_best_per_strategy(self, ranking: pd.DataFrame) -> pd.DataFrame:
        """Get best risk level for each unique strategy."""
        return ranking.loc[ranking.groupby('strategy')['composite_score'].idxmax()]
