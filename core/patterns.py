"""
Pattern Creation Module - CREATE PATTERNS

This module handles:
- Generating patterns from all strategies
- Applying variable lookback
- Creating feature matrix for backtest
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from pathlib import Path
import importlib
import inspect


def discover_strategies(categories: List[str]) -> Dict[str, List[Any]]:
    """
    Discover all strategy classes from strategy modules.
    
    Args:
        categories: List of strategy category names
        
    Returns:
        Dictionary mapping category to list of strategy classes
    """
    print(f"🔍 Discovering strategies in {len(categories)} categories...")
    
    strategies_by_category = {}
    total_count = 0
    
    for category in categories:
        try:
            # Import category module
            module_path = f"strategies.{category}"
            category_module = importlib.import_module(module_path)
            
            # Get all strategy classes in this module
            strategies = []
            
            # Check if there's a __all__ list
            if hasattr(category_module, '__all__'):
                for name in category_module.__all__:
                    strategy_class = getattr(category_module, name)
                    if inspect.isclass(strategy_class):
                        strategies.append(strategy_class)
            
            strategies_by_category[category] = strategies
            total_count += len(strategies)
            print(f"   {category}: {len(strategies)} strategies")
            
        except ImportError as e:
            print(f"   ⚠️  {category}: module not found ({e})")
            strategies_by_category[category] = []
    
    print(f"✅ Discovered {total_count} strategies across {len(categories)} categories")
    
    return strategies_by_category


def generate_all_patterns(universe: pd.DataFrame, strategies: Dict[str, List[Any]], lookback: int = 14) -> pd.DataFrame:
    """
    Run all strategies to generate patterns.
    
    Args:
        universe: Universe DataFrame with indicators
        strategies: Dictionary of strategy classes by category
        lookback: Lookback period for strategies
        
    Returns:
        DataFrame with pattern signals from all strategies
    """
    print(f"🎨 Generating patterns (lookback={lookback})...")
    
    patterns = universe.copy()
    strategy_count = 0
    signal_dict = {}  # Collect signals before adding to DataFrame
    
    for category, strategy_list in strategies.items():
        for strategy_class in strategy_list:
            try:
                # Try v1-style instantiation first (params: Dict)
                # v1 strategies use Dict params, v2 uses lookback: int
                try:
                    # v1 style: __init__(params: Dict)
                    params = {"lookback": lookback, "period": lookback}
                    strategy = strategy_class(params)
                    strategy_name = strategy.name
                except TypeError:
                    # v2 style: __init__(lookback: int)
                    strategy = strategy_class(lookback=lookback)
                    strategy_name = strategy.name
                
                # Generate signals
                signals = strategy.generate_signals(patterns)
                
                # Store in dict (more efficient than adding columns iteratively)
                column_name = f"signal_{strategy_name.lower()}"
                signal_dict[column_name] = signals
                
                strategy_count += 1
                
            except Exception as e:
                print(f"   ⚠️  Error in {strategy_class.__name__}: {e}")
    
    # Add all signals at once (much more efficient than iterative column addition)
    if signal_dict:
        signals_df = pd.DataFrame(signal_dict, index=patterns.index)
        patterns = pd.concat([patterns, signals_df], axis=1)
    
    print(f"✅ Generated patterns from {strategy_count} strategies")
    
    return patterns


def apply_lookback(patterns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """
    Apply variable lookback to patterns.
    
    Args:
        patterns: DataFrame with patterns
        lookback: Lookback period to apply
        
    Returns:
        DataFrame with lookback applied
    """
    # For now, this is a simple filter
    # In a more sophisticated implementation, this could recalculate patterns
    # with different lookback windows
    
    return patterns.iloc[lookback:]


def create_feature_matrix(patterns: pd.DataFrame) -> pd.DataFrame:
    """
    Create feature matrix for backtest.
    
    Args:
        patterns: DataFrame with all patterns
        
    Returns:
        Feature matrix ready for backtesting
    """
    print(f"🧮 Creating feature matrix...")
    
    # Select signal columns
    signal_cols = [col for col in patterns.columns if col.startswith('signal_')]
    
    # Create feature matrix
    features = patterns[signal_cols].copy()
    
    # Add timestamp info
    features['hour'] = patterns.index.hour
    features['day_of_week'] = patterns.index.dayofweek
    features['day_of_month'] = patterns.index.day
    
    # Fill NaN values
    features = features.fillna(0)
    
    print(f"✅ Feature matrix created: {len(features)} rows × {len(features.columns)} features")
    
    return features


def run_patterns_workflow(universe: pd.DataFrame, strategies: Dict[str, List[Any]], lookback: int = 14) -> pd.DataFrame:
    """
    Run complete pattern creation workflow.
    
    Args:
        universe: Universe DataFrame
        strategies: Dictionary of strategy classes
        lookback: Lookback period
        
    Returns:
        DataFrame with patterns and features
    """
    print(f"\n{'='*60}")
    print(f"🎨 PATTERN CREATION")
    print(f"{'='*60}\n")
    
    # Step 1: Generate all patterns
    patterns = generate_all_patterns(universe, strategies, lookback)
    
    # Step 2: Apply lookback
    patterns = apply_lookback(patterns, lookback)
    
    # Step 3: Create feature matrix
    features = create_feature_matrix(patterns)
    
    print(f"\n{'='*60}")
    print(f"✅ PATTERNS CREATED - {len(patterns)} bars with {len(features.columns)} features")
    print(f"{'='*60}\n")
    
    return patterns
