"""
Universe Creation Module - CREATE UNIVERSE

This module handles:
- Downloading XAUUSD M1 data from broker
- Converting CSV to Parquet format
- Creating standardized DataFrame
- Calculating base indicators
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import requests
from tqdm import tqdm


def download_data(year: int, month: int, output_dir: str = "data/raw") -> str:
    """
    Download XAUUSD M1 data from Exness/broker for specified month.
    
    Args:
        year: Year (e.g., 2026)
        month: Month (1-12)
        output_dir: Directory to save CSV file
        
    Returns:
        Path to downloaded CSV file
        
    Note:
        For now, this is a placeholder that expects manual data placement.
        In production, this would connect to Exness API or broker API.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    filename = f"XAUUSD_M1_{year}_{month:02d}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # TODO: Implement actual download from Exness/broker API
    # For now, we expect the user to manually place the CSV file
    print(f"⚠️  Looking for data file: {filepath}")
    print(f"   Please ensure XAUUSD M1 data for {year}-{month:02d} is placed at this location.")
    print(f"   Expected format: DateTime,Open,High,Low,Close,Volume")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found. Creating sample data for testing...")
        # Create sample data for testing
        create_sample_data(filepath, year, month)
    
    return filepath


def create_sample_data(filepath: str, year: int, month: int):
    """
    Create sample XAUUSD M1 data for testing purposes.
    
    Args:
        filepath: Path to save sample CSV
        year: Year
        month: Month
    """
    print(f"📊 Generating sample M1 data for {year}-{month:02d}...")
    
    # Generate one day of M1 data (1440 bars)
    num_bars = 1440
    start_date = pd.Timestamp(f"{year}-{month:02d}-01 00:00:00")
    
    # Create datetime index
    dates = pd.date_range(start=start_date, periods=num_bars, freq='1min')
    
    # Generate realistic price data (starting around 2000 for gold)
    base_price = 2000.0
    np.random.seed(42)
    returns = np.random.normal(0, 0.0001, num_bars)
    prices = base_price * (1 + returns).cumprod()
    
    # Create OHLCV data
    df = pd.DataFrame({
        'DateTime': dates,
        'Open': prices,
        'High': prices * (1 + abs(np.random.normal(0, 0.0002, num_bars))),
        'Low': prices * (1 - abs(np.random.normal(0, 0.0002, num_bars))),
        'Close': prices * (1 + np.random.normal(0, 0.0001, num_bars)),
        'Volume': np.random.randint(100, 1000, num_bars)
    })
    
    df.to_csv(filepath, index=False)
    print(f"✅ Sample data created: {num_bars} bars")


def convert_to_parquet(csv_path: str, delete_csv: bool = True) -> str:
    """
    Convert CSV to Parquet format and optionally delete CSV.
    
    Args:
        csv_path: Path to CSV file
        delete_csv: Whether to delete CSV after conversion
        
    Returns:
        Path to Parquet file
    """
    print(f"📦 Converting {csv_path} to Parquet...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Create parquet directory
    parquet_dir = "data/parquet"
    Path(parquet_dir).mkdir(parents=True, exist_ok=True)
    
    # Create parquet filename
    csv_filename = os.path.basename(csv_path)
    parquet_filename = csv_filename.replace('.csv', '.parquet')
    parquet_path = os.path.join(parquet_dir, parquet_filename)
    
    # Save as parquet
    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    
    file_size_csv = os.path.getsize(csv_path) / 1024 / 1024  # MB
    file_size_parquet = os.path.getsize(parquet_path) / 1024 / 1024  # MB
    compression_ratio = (1 - file_size_parquet / file_size_csv) * 100
    
    print(f"✅ Parquet created: {parquet_path}")
    print(f"   CSV: {file_size_csv:.2f} MB → Parquet: {file_size_parquet:.2f} MB")
    print(f"   Compression: {compression_ratio:.1f}%")
    
    # Delete CSV if requested
    if delete_csv:
        os.remove(csv_path)
        print(f"🗑️  Deleted CSV: {csv_path}")
    
    return parquet_path


def create_universe(parquet_path: str) -> pd.DataFrame:
    """
    Create standardized DataFrame from Parquet file.
    
    Args:
        parquet_path: Path to Parquet file
        
    Returns:
        Standardized DataFrame with datetime index
    """
    print(f"🌌 Creating universe from {parquet_path}...")
    
    # Read parquet
    df = pd.read_parquet(parquet_path)
    
    # Ensure DateTime column exists and is parsed
    if 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        df.set_index('DateTime', inplace=True)
    
    # Standardize column names
    df.columns = [col.lower() for col in df.columns]
    
    # Sort by datetime
    df.sort_index(inplace=True)
    
    # Remove duplicates
    df = df[~df.index.duplicated(keep='first')]
    
    print(f"✅ Universe created: {len(df)} bars")
    print(f"   Period: {df.index[0]} to {df.index[-1]}")
    print(f"   Columns: {list(df.columns)}")
    
    return df


def calculate_base_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with additional indicator columns
    """
    print(f"📊 Calculating base indicators...")
    
    try:
        import ta
    except ImportError:
        print("⚠️  'ta' library not installed. Installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'ta'])
        import ta
    
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Simple Moving Averages
    for period in [7, 14, 21, 50, 100, 200]:
        df[f'sma_{period}'] = ta.trend.sma_indicator(df['close'], window=period)
    
    # Exponential Moving Averages
    for period in [7, 14, 21, 50, 100, 200]:
        df[f'ema_{period}'] = ta.trend.ema_indicator(df['close'], window=period)
    
    # RSI
    df['rsi_14'] = ta.momentum.rsi(df['close'], window=14)
    
    # ATR
    df['atr_14'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bollinger.bollinger_hband()
    df['bb_middle'] = bollinger.bollinger_mavg()
    df['bb_lower'] = bollinger.bollinger_lband()
    df['bb_width'] = bollinger.bollinger_wband()
    
    # MACD
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_diff'] = macd.macd_diff()
    
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    # ADX
    adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
    df['adx'] = adx.adx()
    
    # Volume indicators
    df['volume_sma'] = df['volume'].rolling(window=20).mean()
    
    print(f"✅ Indicators calculated: {len([c for c in df.columns if c not in ['open', 'high', 'low', 'close', 'volume']])} new columns")
    
    return df


def run_universe_workflow(year: int, month: int) -> pd.DataFrame:
    """
    Run complete universe creation workflow.
    
    Args:
        year: Year
        month: Month
        
    Returns:
        Universe DataFrame with indicators
    """
    print(f"\n{'='*60}")
    print(f"🌌 UNIVERSE CREATION - {year}-{month:02d}")
    print(f"{'='*60}\n")
    
    # Step 1: Download data
    csv_path = download_data(year, month)
    
    # Step 2: Convert to Parquet
    parquet_path = convert_to_parquet(csv_path, delete_csv=True)
    
    # Step 3: Create universe
    universe = create_universe(parquet_path)
    
    # Step 4: Calculate indicators
    universe = calculate_base_indicators(universe)
    
    print(f"\n{'='*60}")
    print(f"✅ UNIVERSE CREATED - {len(universe)} bars with {len(universe.columns)} features")
    print(f"{'='*60}\n")
    
    return universe
