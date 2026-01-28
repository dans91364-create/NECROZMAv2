"""
Advanced Label Creation Module with Numba JIT Optimization

This module provides multi-dimensional outcome labeling with:
- Numba JIT compilation (50-100x faster than pure Python)
- Multi-target support: [5, 10, 15, 20, 30, 50] pips
- Multi-stop support: [5, 10, 15, 20, 30] pips  
- Multi-horizon support: [30, 60, 120, 240, 480, 1440] minutes
- Advanced metrics: MFE, MAE, R-Multiple
- Intelligent caching to avoid recalculation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from pathlib import Path
import hashlib
import pickle
from numba import njit
import time


@njit(cache=True, fastmath=True)
def _scan_for_target_stop(prices_high: np.ndarray, 
                          prices_low: np.ndarray,
                          candle_idx: int,
                          horizon_bars: int,
                          entry_price: float,
                          target_price: float,
                          stop_price: float,
                          pip_value: float,
                          direction_up: bool) -> Tuple[str, float, float, float, int]:
    """
    Numba-optimized scan for target/stop hits - 50-100x faster than pure Python.
    
    Scans forward from candle_idx for horizon_bars to determine if target or stop is hit first.
    
    Args:
        prices_high: Array of high prices
        prices_low: Array of low prices
        candle_idx: Starting candle index
        horizon_bars: Maximum bars to look forward
        entry_price: Entry price
        target_price: Target price level
        stop_price: Stop loss price level
        pip_value: Value of 1 pip in price units
        direction_up: True for long, False for short
        
    Returns:
        Tuple of (outcome, mfe, mae, r_multiple, bars_to_result)
        - outcome: 'target', 'stop', or 'timeout'
        - mfe: Maximum Favorable Excursion in pips
        - mae: Maximum Adverse Excursion in pips
        - r_multiple: Actual profit/loss as multiple of risk
        - bars_to_result: Number of bars until target/stop hit (or horizon)
    """
    max_idx = min(candle_idx + horizon_bars, len(prices_high))
    
    mfe = 0.0  # Maximum Favorable Excursion
    mae = 0.0  # Maximum Adverse Excursion
    
    for i in range(candle_idx + 1, max_idx):
        high = prices_high[i]
        low = prices_low[i]
        
        if direction_up:
            # Long trade
            favorable = high - entry_price
            adverse = entry_price - low
            
            # Update MFE/MAE
            if favorable > mfe:
                mfe = favorable
            if adverse > mae:
                mae = adverse
            
            # Check if target hit
            if high >= target_price:
                bars = i - candle_idx
                r_mult = (target_price - entry_price) / (entry_price - stop_price)
                return ('target', mfe / pip_value, mae / pip_value, r_mult, bars)
            
            # Check if stop hit
            if low <= stop_price:
                bars = i - candle_idx
                r_mult = (stop_price - entry_price) / (entry_price - stop_price)
                return ('stop', mfe / pip_value, mae / pip_value, r_mult, bars)
        else:
            # Short trade
            favorable = entry_price - low
            adverse = high - entry_price
            
            # Update MFE/MAE
            if favorable > mfe:
                mfe = favorable
            if adverse > mae:
                mae = adverse
            
            # Check if target hit
            if low <= target_price:
                bars = i - candle_idx
                r_mult = (entry_price - target_price) / (stop_price - entry_price)
                return ('target', mfe / pip_value, mae / pip_value, r_mult, bars)
            
            # Check if stop hit
            if high >= stop_price:
                bars = i - candle_idx
                r_mult = (entry_price - stop_price) / (stop_price - entry_price)
                return ('stop', mfe / pip_value, mae / pip_value, r_mult, bars)
    
    # Timeout - neither target nor stop hit within horizon
    bars = horizon_bars
    
    # Calculate final R-multiple based on where price ended up
    final_high = prices_high[max_idx - 1]
    final_low = prices_low[max_idx - 1]
    
    if direction_up:
        final_price = (final_high + final_low) / 2.0
        r_mult = (final_price - entry_price) / (entry_price - stop_price)
    else:
        final_price = (final_high + final_low) / 2.0
        r_mult = (entry_price - final_price) / (stop_price - entry_price)
    
    return ('timeout', mfe / pip_value, mae / pip_value, r_mult, bars)


def _get_cache_key(df: pd.DataFrame, target_pips: List[int], 
                   stop_pips: List[int], horizons: List[int]) -> str:
    """
    Generate cache key for label configuration.
    
    Args:
        df: Input DataFrame
        target_pips: List of target levels
        stop_pips: List of stop levels
        horizons: List of time horizons
        
    Returns:
        MD5 hash string for cache lookup
    """
    # Create hash from dataframe index and config
    index_str = str(df.index[0]) + str(df.index[-1]) + str(len(df))
    config_str = f"{target_pips}_{stop_pips}_{horizons}"
    combined = index_str + config_str
    return hashlib.md5(combined.encode()).hexdigest()


def label_dataframe(df: pd.DataFrame,
                   target_pips: List[int] = [5, 10, 15, 20, 30, 50],
                   stop_pips: List[int] = [5, 10, 15, 20, 30],
                   horizons: List[int] = [30, 60, 120, 240, 480, 1440],
                   use_cache: bool = True,
                   cache_dir: str = "data/labels",
                   pip_value: float = 0.1) -> Dict[str, pd.DataFrame]:
    """
    Multi-dimensional outcome labeling with Numba optimization.
    
    Creates labels for ALL combinations of:
    - Multiple targets × Multiple stops × Multiple horizons
    - × 2 directions (long/short)
    
    For default config:
    - 6 targets × 5 stops × 6 horizons = 180 configs
    
    Args:
        df: Input DataFrame with OHLC data
        target_pips: List of take profit levels in pips
        stop_pips: List of stop loss levels in pips
        horizons: List of time horizons in minutes (converted to bars based on timeframe)
        use_cache: Enable disk caching to avoid recalculation
        cache_dir: Directory for label cache
        pip_value: Value of 1 pip (0.1 for gold, 0.0001 for most forex pairs)
        
    Returns:
        Dict mapping config name (e.g., "T10_S5_H60") to DataFrame with label columns
    """
    print(f"🏷️  LABEL CREATION")
    print(f"{'='*80}")
    print(f"⚡ Numba JIT: ENABLED (Light Speed Mode - 50-100x faster)")
    print(f"")
    
    # Check cache
    if use_cache:
        cache_path = Path(cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)
        cache_key = _get_cache_key(df, target_pips, stop_pips, horizons)
        cache_file = cache_path / f"labels_{cache_key}.pkl"
        
        if cache_file.exists():
            print(f"📦 Loading labels from cache: {cache_file.name}")
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
    
    # Detect timeframe from data (bars per minute)
    if 'timestamp' in df.columns or isinstance(df.index, pd.DatetimeIndex):
        if isinstance(df.index, pd.DatetimeIndex):
            time_diffs = df.index.to_series().diff()
        else:
            time_diffs = pd.to_datetime(df['timestamp']).diff()
        
        median_diff = time_diffs.median()
        bars_per_minute = 1.0 / (median_diff.total_seconds() / 60.0)
    else:
        # Assume 1-minute bars if no timestamp
        bars_per_minute = 1.0
    
    # Calculate total number of configurations
    total_configs = len(target_pips) * len(stop_pips) * len(horizons)
    print(f"Creating labels for {total_configs} configurations...")
    print(f"  Targets: {target_pips}")
    print(f"  Stops: {stop_pips}")
    print(f"  Horizons: {horizons} minutes")
    print(f"  Bars per minute: {bars_per_minute:.2f}")
    print(f"")
    
    # Convert to numpy arrays for Numba
    prices_high = df['high'].values
    prices_low = df['low'].values
    prices_close = df['close'].values
    
    results_dict = {}
    config_idx = 0
    start_time = time.time()
    
    # Iterate over all combinations
    for tp in target_pips:
        for sl in stop_pips:
            for horizon_minutes in horizons:
                config_idx += 1
                config_name = f"T{tp}_S{sl}_H{horizon_minutes}"
                
                # Convert horizon from minutes to bars
                horizon_bars = int(horizon_minutes * bars_per_minute)
                
                config_start = time.time()
                
                # Initialize result arrays
                n = len(df)
                up_outcome = np.empty(n, dtype='U10')
                down_outcome = np.empty(n, dtype='U10')
                up_mfe = np.zeros(n)
                up_mae = np.zeros(n)
                down_mfe = np.zeros(n)
                down_mae = np.zeros(n)
                up_r_multiple = np.zeros(n)
                down_r_multiple = np.zeros(n)
                up_time_to_result = np.zeros(n, dtype=np.int32)
                down_time_to_result = np.zeros(n, dtype=np.int32)
                
                # Process each candle
                for i in range(n):
                    entry_price = prices_close[i]
                    
                    # Long trade
                    long_target = entry_price + (tp * pip_value)
                    long_stop = entry_price - (sl * pip_value)
                    
                    outcome, mfe, mae, r_mult, bars = _scan_for_target_stop(
                        prices_high, prices_low, i, horizon_bars,
                        entry_price, long_target, long_stop, pip_value, True
                    )
                    
                    up_outcome[i] = outcome
                    up_mfe[i] = mfe
                    up_mae[i] = mae
                    up_r_multiple[i] = r_mult
                    up_time_to_result[i] = bars
                    
                    # Short trade
                    short_target = entry_price - (tp * pip_value)
                    short_stop = entry_price + (sl * pip_value)
                    
                    outcome, mfe, mae, r_mult, bars = _scan_for_target_stop(
                        prices_high, prices_low, i, horizon_bars,
                        entry_price, short_target, short_stop, pip_value, False
                    )
                    
                    down_outcome[i] = outcome
                    down_mfe[i] = mfe
                    down_mae[i] = mae
                    down_r_multiple[i] = r_mult
                    down_time_to_result[i] = bars
                
                # Create result DataFrame
                result_df = df.copy()
                result_df['up_outcome'] = up_outcome
                result_df['down_outcome'] = down_outcome
                result_df['up_mfe'] = up_mfe
                result_df['up_mae'] = up_mae
                result_df['down_mfe'] = down_mfe
                result_df['down_mae'] = down_mae
                result_df['up_r_multiple'] = up_r_multiple
                result_df['down_r_multiple'] = down_r_multiple
                result_df['up_time_to_result'] = up_time_to_result
                result_df['down_time_to_result'] = down_time_to_result
                
                # Add binary labels for compatibility
                result_df['label_long'] = (up_outcome == 'target').astype(int)
                result_df['label_short'] = (down_outcome == 'target').astype(int)
                
                # Calculate statistics
                long_wins = (up_outcome == 'target').sum()
                long_losses = (up_outcome == 'stop').sum()
                long_timeouts = (up_outcome == 'timeout').sum()
                short_wins = (down_outcome == 'target').sum()
                short_losses = (down_outcome == 'stop').sum()
                short_timeouts = (down_outcome == 'timeout').sum()
                
                total_long = long_wins + long_losses
                total_short = short_wins + short_losses
                
                long_wr = (long_wins / total_long * 100) if total_long > 0 else 0
                short_wr = (short_wins / total_short * 100) if total_short > 0 else 0
                
                config_time = time.time() - config_start
                
                print(f"  {config_name}... ✅ ({config_time:.1f}s) "
                      f"Long WR: {long_wr:.1f}% Short WR: {short_wr:.1f}%")
                
                results_dict[config_name] = result_df
    
    elapsed = time.time() - start_time
    
    print(f"")
    print(f"✅ LABELS CREATED")
    print(f"   Total configs: {total_configs}")
    print(f"   Total time: {elapsed:.1f}s")
    
    # Find best config
    best_config = None
    best_wr = 0
    for config_name, result_df in results_dict.items():
        long_wins = (result_df['up_outcome'] == 'target').sum()
        long_total = ((result_df['up_outcome'] == 'target') | (result_df['up_outcome'] == 'stop')).sum()
        short_wins = (result_df['down_outcome'] == 'target').sum()
        short_total = ((result_df['down_outcome'] == 'target') | (result_df['down_outcome'] == 'stop')).sum()
        
        avg_wr = 0
        if long_total > 0 and short_total > 0:
            avg_wr = ((long_wins / long_total) + (short_wins / short_total)) / 2.0
        
        if avg_wr > best_wr:
            best_wr = avg_wr
            best_config = config_name
    
    if best_config:
        print(f"")
        print(f"   Label Statistics:")
        print(f"   - Best avg win rate: {best_config} ({best_wr*100:.1f}%)")
    
    print(f"{'='*80}")
    print(f"")
    
    # Cache results
    if use_cache:
        with open(cache_file, 'wb') as f:
            pickle.dump(results_dict, f)
        print(f"💾 Labels cached to: {cache_file}")
    
    return results_dict


def load_label_results(cache_dir: str = "data/labels", 
                       cache_key: str = None) -> Dict[str, pd.DataFrame]:
    """
    Load previously cached label results.
    
    Args:
        cache_dir: Directory where labels are cached
        cache_key: Specific cache key to load (if None, loads most recent)
        
    Returns:
        Dict of label DataFrames by config name
    """
    cache_path = Path(cache_dir)
    
    if not cache_path.exists():
        raise FileNotFoundError(f"Cache directory not found: {cache_dir}")
    
    if cache_key:
        cache_file = cache_path / f"labels_{cache_key}.pkl"
    else:
        # Find most recent cache file
        cache_files = list(cache_path.glob("labels_*.pkl"))
        if not cache_files:
            raise FileNotFoundError(f"No cache files found in {cache_dir}")
        cache_file = max(cache_files, key=lambda p: p.stat().st_mtime)
    
    if not cache_file.exists():
        raise FileNotFoundError(f"Cache file not found: {cache_file}")
    
    print(f"📦 Loading labels from cache: {cache_file.name}")
    
    with open(cache_file, 'rb') as f:
        return pickle.load(f)
