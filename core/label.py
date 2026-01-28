"""
Label Creation Module - CREATE LABEL

This module handles:
- Calculating forward returns
- Creating win/loss labels based on TP/SL
- Defining target levels
- Multi-dimensional labeling with Numba optimization
"""

import pandas as pd
import numpy as np
from typing import List, Tuple, Dict
from core.labeler import label_dataframe, load_label_results


def calculate_forward_returns(df: pd.DataFrame, periods: List[int] = [1, 5, 10, 20, 50, 100]) -> pd.DataFrame:
    """
    Calculate forward returns for multiple periods.
    
    Args:
        df: DataFrame with price data
        periods: List of periods to calculate forward returns
        
    Returns:
        DataFrame with forward return columns
    """
    print(f"📈 Calculating forward returns for periods: {periods}...")
    
    df = df.copy()
    
    for period in periods:
        # Forward return (future price / current price - 1)
        df[f'fwd_return_{period}'] = df['close'].shift(-period) / df['close'] - 1
        
        # Forward high (maximum high in next N periods)
        df[f'fwd_high_{period}'] = df['high'].shift(-period).rolling(window=period).max()
        
        # Forward low (minimum low in next N periods)
        df[f'fwd_low_{period}'] = df['low'].shift(-period).rolling(window=period).min()
    
    print(f"✅ Forward returns calculated for {len(periods)} periods")
    
    return df


def create_labels(df: pd.DataFrame, tp_pips: float = 10.0, sl_pips: float = 10.0) -> pd.DataFrame:
    """
    Create win/loss labels based on TP/SL levels.
    
    For XAUUSD, 1 pip = 0.1 (since gold is quoted to 2 decimals)
    
    Args:
        df: DataFrame with price data
        tp_pips: Take profit in pips
        sl_pips: Stop loss in pips
        
    Returns:
        DataFrame with label columns
    """
    print(f"🏷️  Creating labels (TP: {tp_pips} pips, SL: {sl_pips} pips)...")
    
    df = df.copy()
    
    # Convert pips to price for XAUUSD (1 pip = 0.1 for gold)
    pip_value = 0.1
    tp_price = tp_pips * pip_value
    sl_price = sl_pips * pip_value
    
    # Calculate future price movements
    for i in range(len(df)):
        current_price = df.iloc[i]['close']
        
        # Look ahead to find TP or SL hit
        # Long trade
        long_tp = current_price + tp_price
        long_sl = current_price - sl_price
        
        # Short trade
        short_tp = current_price - tp_price
        short_sl = current_price + sl_price
        
        # Check next 100 bars (or end of data)
        lookforward = min(100, len(df) - i - 1)
        
        if lookforward > 0:
            future_highs = df.iloc[i+1:i+1+lookforward]['high'].values
            future_lows = df.iloc[i+1:i+1+lookforward]['low'].values
            
            # Long trade outcome
            long_tp_hit = np.any(future_highs >= long_tp)
            long_sl_hit = np.any(future_lows <= long_sl)
            
            # Short trade outcome
            short_tp_hit = np.any(future_lows <= short_tp)
            short_sl_hit = np.any(future_highs >= short_sl)
            
            # Determine which was hit first for long
            if long_tp_hit and long_sl_hit:
                tp_idx = np.argmax(future_highs >= long_tp)
                sl_idx = np.argmax(future_lows <= long_sl)
                df.loc[df.index[i], 'label_long'] = 1 if tp_idx < sl_idx else 0
            elif long_tp_hit:
                df.loc[df.index[i], 'label_long'] = 1
            elif long_sl_hit:
                df.loc[df.index[i], 'label_long'] = 0
            else:
                df.loc[df.index[i], 'label_long'] = -1  # Neither hit
            
            # Determine which was hit first for short
            if short_tp_hit and short_sl_hit:
                tp_idx = np.argmax(future_lows <= short_tp)
                sl_idx = np.argmax(future_highs >= short_sl)
                df.loc[df.index[i], 'label_short'] = 1 if tp_idx < sl_idx else 0
            elif short_tp_hit:
                df.loc[df.index[i], 'label_short'] = 1
            elif short_sl_hit:
                df.loc[df.index[i], 'label_short'] = 0
            else:
                df.loc[df.index[i], 'label_short'] = -1  # Neither hit
        else:
            df.loc[df.index[i], 'label_long'] = -1
            df.loc[df.index[i], 'label_short'] = -1
    
    # Convert to int
    df['label_long'] = df['label_long'].fillna(-1).astype(int)
    df['label_short'] = df['label_short'].fillna(-1).astype(int)
    
    # Calculate label statistics
    long_wins = (df['label_long'] == 1).sum()
    long_losses = (df['label_long'] == 0).sum()
    short_wins = (df['label_short'] == 1).sum()
    short_losses = (df['label_short'] == 0).sum()
    
    print(f"✅ Labels created:")
    print(f"   Long: {long_wins} wins, {long_losses} losses ({long_wins/(long_wins+long_losses)*100:.1f}% win rate)")
    print(f"   Short: {short_wins} wins, {short_losses} losses ({short_wins/(short_wins+short_losses)*100:.1f}% win rate)")
    
    return df


def define_targets(df: pd.DataFrame, tp_pips: float = 10.0, sl_pips: float = 10.0) -> pd.DataFrame:
    """
    Define TP/SL target levels for each bar.
    
    Args:
        df: DataFrame with price data
        tp_pips: Take profit in pips
        sl_pips: Stop loss in pips
        
    Returns:
        DataFrame with target columns
    """
    print(f"🎯 Defining target levels...")
    
    df = df.copy()
    
    # Convert pips to price for XAUUSD
    pip_value = 0.1
    tp_price = tp_pips * pip_value
    sl_price = sl_pips * pip_value
    
    # Long targets
    df['long_tp'] = df['close'] + tp_price
    df['long_sl'] = df['close'] - sl_price
    
    # Short targets
    df['short_tp'] = df['close'] - tp_price
    df['short_sl'] = df['close'] + sl_price
    
    # Risk/Reward ratio
    df['rr_ratio'] = tp_pips / sl_pips
    
    print(f"✅ Targets defined (RR: {tp_pips/sl_pips:.2f})")
    
    return df


def run_label_workflow(universe: pd.DataFrame, config: dict = None, 
                      tp_pips: float = None, sl_pips: float = None) -> Dict[str, pd.DataFrame]:
    """
    Run complete label creation workflow with multi-config support.
    
    If config is provided, uses multi-dimensional labeling from core.labeler.
    Otherwise falls back to simple labeling for backward compatibility.
    
    Args:
        universe: Universe DataFrame
        config: Configuration dictionary (optional)
        tp_pips: Take profit in pips (for simple mode)
        sl_pips: Stop loss in pips (for simple mode)
        
    Returns:
        Dict mapping config name to DataFrame with labels, or single DataFrame for simple mode
    """
    # Check if multi-config mode is enabled
    if config and 'labeling' in config:
        labeling_config = config['labeling']
        target_pips = labeling_config.get('target_pips', [10])
        stop_pips = labeling_config.get('stop_pips', [10])
        horizons = labeling_config.get('horizons', [60])
        use_cache = labeling_config.get('use_cache', True)
        cache_dir = labeling_config.get('cache_dir', 'data/labels')
        
        # Use new multi-dimensional labeler
        labels_dict = label_dataframe(
            universe,
            target_pips=target_pips,
            stop_pips=stop_pips,
            horizons=horizons,
            use_cache=use_cache,
            cache_dir=cache_dir
        )
        
        return labels_dict
    else:
        # Backward compatibility - simple mode
        print(f"\n{'='*60}")
        print(f"🏷️  LABEL CREATION (Simple Mode)")
        print(f"{'='*60}\n")
        
        # Use default values if not provided
        if tp_pips is None:
            tp_pips = 10.0
        if sl_pips is None:
            sl_pips = 10.0
        
        # Step 1: Calculate forward returns
        df = calculate_forward_returns(universe)
        
        # Step 2: Create labels
        df = create_labels(df, tp_pips, sl_pips)
        
        # Step 3: Define targets
        df = define_targets(df, tp_pips, sl_pips)
        
        print(f"\n{'='*60}")
        print(f"✅ LABELS CREATED - {len(df)} bars labeled")
        print(f"{'='*60}\n")
        
        # Return as dict for consistency
        return {'default': df}
