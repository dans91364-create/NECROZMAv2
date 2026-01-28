"""
Universe Creation Module - CREATE UNIVERSE

This module handles:
- Downloading tick data from Exness for multiple pairs
- Converting ZIP → CSV → Parquet format
- Creating standardized DataFrame
- Calculating base indicators
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
import requests
from tqdm import tqdm
import zipfile
import tempfile


def download_with_progress(url: str, output_path: Path) -> None:
    """
    Download file with progress bar.
    
    Args:
        url: URL to download from
        output_path: Path to save downloaded file
    """
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(output_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc=f"Downloading") as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


def extract_csv_from_zip(zip_path: Path) -> Path:
    """
    Extract CSV file from ZIP archive.
    
    Args:
        zip_path: Path to ZIP file
        
    Returns:
        Path to extracted CSV file
    """
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        # Get the first CSV file in the archive
        csv_files = [f for f in zip_ref.namelist() if f.endswith('.csv')]
        if not csv_files:
            raise ValueError(f"No CSV file found in {zip_path}")
        
        csv_filename = csv_files[0]
        extract_dir = zip_path.parent
        zip_ref.extract(csv_filename, extract_dir)
        
        return extract_dir / csv_filename


def download_pair(pair: str, year: int, month: int, base_url: str, output_dir: Path) -> Optional[Path]:
    """
    Download tick data for a single pair/month from Exness.
    
    Args:
        pair: Currency pair (e.g., 'EURUSD')
        year: Year (e.g., 2026)
        month: Month (1-12)
        base_url: URL template for downloads
        output_dir: Directory to save parquet files
        
    Returns:
        Path to parquet file, or None if download failed
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_parquet = output_dir / f"{pair}_{year}_{month:02d}.parquet"
    
    # Skip if already exists
    if output_parquet.exists():
        print(f"⏭️  {pair} já existe, pulando...")
        return output_parquet
    
    try:
        # Build URL
        url = base_url.format(pair=pair, year=year, month=month)
        
        # Create temp directory for download
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_file = temp_path / f"{pair}_{year}_{month:02d}.zip"
            
            # Download ZIP
            print(f"📥 Downloading {pair}...")
            download_with_progress(url, zip_file)
            
            # Extract CSV
            csv_file = extract_csv_from_zip(zip_file)
            
            # Read and validate
            df = pd.read_csv(
                csv_file,
                skiprows=1,
                names=['broker', 'symbol', 'timestamp', 'bid', 'ask'],
                parse_dates=['timestamp']
            )
            
            # Convert to standardized format
            # Create OHLC from bid/ask tick data
            df['mid'] = (df['bid'] + df['ask']) / 2
            df.set_index('timestamp', inplace=True)
            
            # Resample to M1 bars for compatibility with existing system
            ohlc = df['mid'].resample('1min').ohlc()
            ohlc.columns = ['open', 'high', 'low', 'close']
            ohlc['volume'] = df['mid'].resample('1min').count()
            
            # Remove rows with no data
            ohlc = ohlc.dropna()
            
            # Reset index to have datetime as column
            ohlc.reset_index(inplace=True)
            ohlc.rename(columns={'timestamp': 'DateTime'}, inplace=True)
            
            # Convert to Parquet
            ohlc.to_parquet(output_parquet, engine='pyarrow', compression='snappy')
            
            file_size = output_parquet.stat().st_size / 1024 / 1024  # MB
            num_ticks = len(df)
            print(f"✅ {pair}: {file_size:.1f}MB, {num_ticks/1000000:.1f}M ticks")
            
            return output_parquet
            
    except Exception as e:
        print(f"❌ Error downloading {pair}: {e}")
        return None


def download_all_pairs(pairs: List[str], year: int, month: int, base_url: str, output_dir: Path) -> Dict[str, Path]:
    """
    Download tick data for all pairs.
    
    Args:
        pairs: List of currency pairs
        year: Year
        month: Month
        base_url: URL template for downloads
        output_dir: Directory to save parquet files
        
    Returns:
        Dictionary mapping pair to parquet file path
    """
    print(f"\n{'='*80}")
    print(f"📥 STEP 1: DOWNLOADING {len(pairs)} PAIRS")
    print(f"{'='*80}\n")
    
    results = {}
    
    for i, pair in enumerate(pairs, 1):
        print(f"[{i}/{len(pairs)}] {pair}...")
        parquet_path = download_pair(pair, year, month, base_url, output_dir)
        if parquet_path:
            results[pair] = parquet_path
    
    print(f"\n✅ Downloaded {len(results)}/{len(pairs)} pairs successfully\n")
    
    return results


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


def resample_to_timeframe(df: pd.DataFrame, interval_minutes: int) -> pd.DataFrame:
    """
    Resample M1 data to higher timeframe.
    
    Args:
        df: DataFrame with M1 data (must have datetime index and OHLCV columns)
        interval_minutes: Interval in minutes (1, 5, 15, 30, 60)
        
    Returns:
        Resampled DataFrame with OHLCV columns only (indicators are dropped)
        
    Note:
        Only OHLCV columns are preserved during resampling.
        Indicator columns (if present) are dropped and should be recalculated.
    """
    # Validate interval
    valid_intervals = [1, 5, 15, 30, 60]
    if interval_minutes not in valid_intervals:
        raise ValueError(f"Invalid interval_minutes: {interval_minutes}. Must be one of {valid_intervals}")
    
    if interval_minutes == 1:
        # Return only OHLCV columns even for M1
        return df[['open', 'high', 'low', 'close', 'volume']].copy()
    
    # Resample OHLCV
    resampled = df[['open', 'high', 'low', 'close', 'volume']].resample(f'{interval_minutes}min').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    return resampled


def create_all_universes(pair_data: pd.DataFrame, intervals: List[int], lookbacks: List[int]) -> Dict[str, pd.DataFrame]:
    """
    Create universes for all interval × lookback combinations.
    
    Args:
        pair_data: DataFrame M1 for a pair (with datetime index and OHLCV columns)
        intervals: List of intervals [1, 5, 15, 30, 60]
        lookbacks: List of lookbacks [5, 10, 15, 20, 30]
        
    Returns:
        Dict mapping "universe_{interval}m_{lookback}lb" -> DataFrame
        
    Note:
        The lookback parameter is included in the naming for compatibility with 
        downstream processing, but all universes for a given interval share the 
        same data (indicators are calculated once per interval).
    """
    universes = {}
    
    for interval in intervals:
        # Resample to the timeframe (returns only OHLCV)
        resampled = resample_to_timeframe(pair_data, interval)
        
        # Calculate indicators once per interval
        with_indicators = calculate_base_indicators(resampled)
        
        # Create references for each lookback combination
        # Note: All lookbacks for the same interval share the same data
        for lookback in lookbacks:
            universe_name = f"universe_{interval}m_{lookback}lb"
            # Store reference to the same DataFrame (memory efficient)
            universes[universe_name] = with_indicators
    
    return universes


def run_universe_workflow(year: int, month: int, pairs: Optional[List[str]] = None, 
                          base_url: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """
    Run complete universe creation workflow for multiple pairs.
    
    Args:
        year: Year
        month: Month
        pairs: List of currency pairs (if None, uses single pair mode)
        base_url: URL template for downloads (required for multi-pair mode)
        
    Returns:
        Dictionary mapping pair to universe DataFrame, or single DataFrame for single pair mode
    """
    # Single pair mode (backward compatibility)
    if pairs is None or len(pairs) == 0:
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
    
    # Multi-pair mode
    print(f"\n{'='*80}")
    print(f"🌌 MULTI-PAIR UNIVERSE CREATION - {year}-{month:02d}")
    print(f"{'='*80}\n")
    
    if base_url is None:
        raise ValueError("base_url is required for multi-pair mode")
    
    # Step 1: Download all pairs
    parquet_dir = Path("data/parquet")
    pair_files = download_all_pairs(pairs, year, month, base_url, parquet_dir)
    
    # Step 2: Create universes for each pair
    print(f"\n{'='*80}")
    print(f"📊 STEP 2: CREATING UNIVERSES")
    print(f"{'='*80}\n")
    
    universes = {}
    
    for i, (pair, parquet_path) in enumerate(pair_files.items(), 1):
        try:
            print(f"Processing {pair}... ", end='', flush=True)
            
            # Create universe
            universe = create_universe(str(parquet_path))
            
            # Calculate indicators
            universe = calculate_base_indicators(universe)
            
            universes[pair] = universe
            print(f"✅ {len(universe)} bars created")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    print(f"\n{'='*80}")
    print(f"✅ CREATED {len(universes)}/{len(pairs)} UNIVERSES")
    print(f"{'='*80}\n")
    
    return universes
