#!/usr/bin/env python3
"""
🐉 NECROZMA v2 - Trading Strategy Laboratory

Main CLI entry point for the Grande Teste system.
Tests 285+ strategies across multiple lookback periods and risk levels.
"""

import argparse
import sys
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.universe import run_universe_workflow, create_all_universes
from core.label import run_label_workflow
from core.patterns import discover_strategies, run_patterns_workflow
from core.backtester import run_backtest_workflow
from core.regime_detector import RegimeDetector
from core.pattern_miner import PatternMiner


def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def parse_year_month(year_month: str) -> tuple:
    """
    Parse YYYY-MM format.
    
    Args:
        year_month: String in YYYY-MM format
        
    Returns:
        Tuple of (year, month)
    """
    try:
        parts = year_month.split('-')
        year = int(parts[0])
        month = int(parts[1])
        
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12")
        
        return year, month
    except (IndexError, ValueError) as e:
        raise ValueError(f"Invalid date format. Expected YYYY-MM, got '{year_month}': {e}")


def cmd_universe(args, config):
    """
    Execute universe creation only.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    year, month = parse_year_month(args.date)
    
    print(f"\n{'='*60}")
    print(f"🌌 CREATING UNIVERSE FOR {year}-{month:02d}")
    print(f"{'='*60}\n")
    
    universe = run_universe_workflow(year, month)
    
    # Save universe
    output_dir = Path("data/universe")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"universe_{year}_{month:02d}.parquet"
    universe.to_parquet(output_path)
    
    print(f"\n✅ Universe saved: {output_path}\n")


def cmd_patterns(args, config):
    """
    Execute pattern creation only.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    year, month = parse_year_month(args.date)
    
    print(f"\n{'='*60}")
    print(f"🎨 CREATING PATTERNS FOR {year}-{month:02d}")
    print(f"{'='*60}\n")
    
    # Load universe
    universe_path = Path(f"data/universe/universe_{year}_{month:02d}.parquet")
    
    if not universe_path.exists():
        print(f"❌ Universe not found: {universe_path}")
        print(f"   Please run: python necrozma.py --universe {args.date}")
        return
    
    import pandas as pd
    universe = pd.read_parquet(universe_path)
    
    # Discover strategies
    strategies = discover_strategies(config['strategies']['categories'])
    
    # Generate patterns
    lookback = config['backtest']['lookbacks'][0]  # Use first lookback
    patterns = run_patterns_workflow(universe, strategies, lookback)
    
    # Save patterns
    output_dir = Path("data/patterns")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"patterns_{year}_{month:02d}.parquet"
    patterns.to_parquet(output_path)
    
    print(f"\n✅ Patterns saved: {output_path}\n")


def cmd_backtest(args, config):
    """
    Execute backtest only.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    year, month = parse_year_month(args.date)
    
    print(f"\n{'='*60}")
    print(f"🔬 BACKTESTING FOR {year}-{month:02d}")
    print(f"{'='*60}\n")
    
    # Load patterns
    patterns_path = Path(f"data/patterns/patterns_{year}_{month:02d}.parquet")
    
    if not patterns_path.exists():
        print(f"❌ Patterns not found: {patterns_path}")
        print(f"   Please run: python necrozma.py --patterns {args.date}")
        return
    
    import pandas as pd
    patterns = pd.read_parquet(patterns_path)
    
    # Load universe for labels
    universe_path = Path(f"data/universe/universe_{year}_{month:02d}.parquet")
    universe = pd.read_parquet(universe_path)
    
    # Create labels (multi-config mode)
    labels_dict = run_label_workflow(universe, config)
    
    # Run backtest for each label config
    output_dir = Path(f"results/{year}-{month:02d}")
    
    # For simple backtest command, use first config or default
    first_config = list(labels_dict.keys())[0]
    labels = labels_dict[first_config]
    
    ranking = run_backtest_workflow(
        patterns,
        labels,
        config['backtest']['risk_levels'],
        config['backtest']['initial_balance'],
        str(output_dir)
    )
    
    # Add label config to ranking
    ranking['label_config'] = first_config
    
    print(f"\n✅ Backtest complete! Results in: {output_dir}\n")


def cmd_full(args, config):
    """
    Execute full Grande Teste workflow.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    year, month = parse_year_month(args.date)
    
    print(f"\n{'='*80}")
    print(f"🐉 GRANDE TESTE - {year}-{month:02d}")
    print(f"{'='*80}\n")
    
    # Check if multi-pair mode is enabled
    pairs = config.get('data', {}).get('pairs', [])
    base_url = config.get('data', {}).get('base_url', None)
    
    # Get intervals and lookbacks from analysis config
    intervals = config.get('analysis', {}).get('intervals', [1])
    lookbacks = config.get('analysis', {}).get('lookbacks', config['backtest']['lookbacks'])
    
    if pairs and base_url:
        num_universes = len(intervals) * len(lookbacks)
        print(f"Multi-pair mode: Testing {len(pairs)} pairs × {num_universes} universes")
        print(f"  Intervals: {intervals} (timeframes in minutes)")
        print(f"  Lookbacks: {lookbacks} (periods)")
        print(f"  Total combinations: {len(pairs)} pairs × {num_universes} universes = {len(pairs) * num_universes}")
        print(f"  1. Download/Create Universes for {len(pairs)} pairs")
        print(f"  2. Create {num_universes} universes per pair (interval × lookback)")
        print(f"  3. Generate Patterns (285+ strategies)")
        print(f"  4. Run Backtest ({len(config['backtest']['risk_levels'])} risk levels)")
    else:
        num_universes = len(intervals) * len(lookbacks)
        print(f"Single-pair mode: Testing {num_universes} universes")
        print(f"  Intervals: {intervals} (timeframes in minutes)")
        print(f"  Lookbacks: {lookbacks} (periods)")
        print(f"  1. Download/Create Universe")
        print(f"  2. Create {num_universes} universes (interval × lookback)")
        print(f"  3. Generate Patterns (285+ strategies)")
        print(f"  4. Run Backtest ({len(config['backtest']['risk_levels'])} risk levels)")
    
    print(f"\n{'='*80}\n")
    
    start_time = datetime.now()
    
    # Step 1: Create Universe(s)
    if pairs and base_url:
        # Multi-pair mode
        pair_m1_data = run_universe_workflow(year, month, pairs=pairs, base_url=base_url)
        
        # Process each pair
        all_pair_results = []
        
        for pair_idx, (pair, m1_universe) in enumerate(pair_m1_data.items(), 1):
            print(f"\n{'='*80}")
            print(f"🔬 PROCESSING PAIR {pair_idx}/{len(pair_m1_data)}: {pair}")
            print(f"{'='*80}\n")
            
            # Save M1 universe for this pair
            output_dir = Path(f"data/universe/{pair}")
            output_dir.mkdir(parents=True, exist_ok=True)
            universe_path = output_dir / f"universe_m1_{year}_{month:02d}.parquet"
            m1_universe.to_parquet(universe_path)
            
            # Step 2: Create all universes (interval × lookback combinations)
            print(f"\n🌌 Creating {len(intervals) * len(lookbacks)} universes for {pair}...")
            universes = create_all_universes(m1_universe, intervals, lookbacks)
            print(f"✅ Created {len(universes)} universes for {pair}")
            
            # Step 3: Discover Strategies
            strategies = discover_strategies(config['strategies']['categories'])
            
            # Step 4: Process each universe
            pair_results = []
            
            for universe_idx, (universe_name, universe_df) in enumerate(universes.items(), 1):
                # Parse interval and lookback from universe name
                # Format: "universe_{interval}m_{lookback}lb"
                try:
                    parts = universe_name.split('_')
                    if len(parts) != 3:
                        raise ValueError(f"Unexpected universe name format: {universe_name}")
                    interval = int(parts[1].replace('m', ''))
                    lookback = int(parts[2].replace('lb', ''))
                except (ValueError, IndexError) as e:
                    print(f"⚠️  Warning: Could not parse universe name '{universe_name}': {e}")
                    print(f"    Skipping this universe.")
                    continue
                
                print(f"\n{'─'*60}")
                print(f"📊 {pair} - Universe {universe_idx}/{len(universes)}: {interval}m, lookback={lookback}")
                print(f"{'─'*60}\n")
                
                # Step 2.5: Detect Market Regimes (if enabled)
                universe_with_regimes = universe_df.copy()
                if config.get('regime', {}).get('n_regimes', 0) > 0:
                    print(f"🔮 Detecting market regimes...")
                    try:
                        detector = RegimeDetector(
                            n_regimes=config['regime']['n_regimes'],
                            method=config['regime'].get('method', 'hdbscan'),
                            min_cluster_size=config['regime'].get('min_cluster_size', 100)
                        )
                        universe_with_regimes = detector.detect_regimes(universe_df)
                        regime_analysis = detector.analyze_regimes(universe_with_regimes)
                        
                        print(f"   Detected {regime_analysis['n_regimes']} regimes:")
                        for regime_id, regime_info in regime_analysis['regimes'].items():
                            print(f"   - {regime_info['name']}: {regime_info['pct']:.1f}% of data")
                    except Exception as e:
                        print(f"   ⚠️  Regime detection failed: {e}")
                        universe_with_regimes = universe_df.copy()
                
                # Create labels for this universe (multi-config mode)
                labels_dict = run_label_workflow(universe_with_regimes, config)
                
                # Step 2.6: Mine Patterns (if enabled)
                pattern_mining_enabled = config.get('pattern_mining', {}).get('enabled', False)
                if pattern_mining_enabled and labels_dict:
                    print(f"\n⛏️  Mining patterns with ML...")
                    try:
                        # Use first label config for pattern mining
                        first_label_config = list(labels_dict.keys())[0]
                        first_labels = labels_dict[first_label_config]
                        
                        miner = PatternMiner(
                            use_shap=config['pattern_mining'].get('use_shap', True),
                            top_features=config['pattern_mining'].get('top_features', 50)
                        )
                        mining_results = miner.discover_patterns(universe_with_regimes, first_labels)
                        
                        importance = miner.get_feature_importance()
                        if len(importance) > 0:
                            print(f"   Top 10 important features:")
                            for idx, row in importance.head(10).iterrows():
                                print(f"   {idx+1}. {row['feature']}: {row['importance']:.4f}")
                            
                            # Save patterns
                            patterns_output_dir = Path(f"results/{year}-{month:02d}/{pair}/{universe_name}")
                            patterns_output_dir.mkdir(parents=True, exist_ok=True)
                            patterns_path = patterns_output_dir / "ml_patterns.csv"
                            importance.to_csv(patterns_path, index=False)
                            print(f"   💾 ML patterns saved: {patterns_path}")
                    except Exception as e:
                        print(f"   ⚠️  Pattern mining failed: {e}")
                
                # Generate patterns
                patterns = run_patterns_workflow(universe_with_regimes, strategies, lookback)
                
                # Run backtest for each label config
                for label_config, labels in labels_dict.items():
                    output_dir_universe = Path(f"results/{year}-{month:02d}/{pair}/{universe_name}/{label_config}")
                    ranking = run_backtest_workflow(
                        patterns,
                        labels,
                        config['backtest']['risk_levels'],
                        config['backtest']['initial_balance'],
                        str(output_dir_universe)
                    )
                    
                    # Add pair, interval, lookback, and label_config info to ranking
                    ranking['pair'] = pair
                    ranking['interval'] = interval
                    ranking['lookback'] = lookback
                    ranking['label_config'] = label_config
                    
                    pair_results.append(ranking)
            
            # Combine results for this pair
            if pair_results:
                pair_combined = pd.concat(pair_results, ignore_index=True)
                all_pair_results.append(pair_combined)
        
        # Combine all results from all pairs and universes
        print(f"\n{'='*80}")
        print(f"📊 COMBINING RESULTS FROM ALL PAIRS AND UNIVERSES")
        print(f"{'='*80}\n")
        
        import pandas as pd
        combined = pd.concat(all_pair_results, ignore_index=True)
        combined = combined.sort_values('total_return', ascending=False).reset_index(drop=True)
        combined.insert(0, 'overall_rank', range(1, len(combined) + 1))
        
        # Save combined ranking
        final_output_dir = Path(f"results/{year}-{month:02d}")
        final_ranking_path = final_output_dir / "ranking_all_pairs_universes.csv"
        combined.to_csv(final_ranking_path, index=False)
        
        # Show top 13 (the Legendaries)
        print(f"🏆 TOP 13 LENDÁRIOS:\n")
        print(combined.head(13).to_string(index=False))
        
    else:
        # Single pair mode - now also with multiple universes
        m1_universe = run_universe_workflow(year, month)
        
        # Save M1 universe
        output_dir = Path("data/universe")
        output_dir.mkdir(parents=True, exist_ok=True)
        universe_path = output_dir / f"universe_m1_{year}_{month:02d}.parquet"
        m1_universe.to_parquet(universe_path)
        
        # Step 2: Create all universes (interval × lookback combinations)
        print(f"\n🌌 Creating {len(intervals) * len(lookbacks)} universes...")
        universes = create_all_universes(m1_universe, intervals, lookbacks)
        print(f"✅ Created {len(universes)} universes")
        
        # Step 3: Discover Strategies
        strategies = discover_strategies(config['strategies']['categories'])
        
        # Step 4: Process each universe
        all_results = []
        
        for universe_idx, (universe_name, universe_df) in enumerate(universes.items(), 1):
            # Parse interval and lookback from universe name
            # Format: "universe_{interval}m_{lookback}lb"
            try:
                parts = universe_name.split('_')
                if len(parts) != 3:
                    raise ValueError(f"Unexpected universe name format: {universe_name}")
                interval = int(parts[1].replace('m', ''))
                lookback = int(parts[2].replace('lb', ''))
            except (ValueError, IndexError) as e:
                print(f"⚠️  Warning: Could not parse universe name '{universe_name}': {e}")
                print(f"    Skipping this universe.")
                continue
            
            print(f"\n{'─'*60}")
            print(f"📊 Universe {universe_idx}/{len(universes)}: {interval}m, lookback={lookback}")
            print(f"{'─'*60}\n")
            
            # Step 2.5: Detect Market Regimes (if enabled)
            universe_with_regimes = universe_df.copy()
            if config.get('regime', {}).get('n_regimes', 0) > 0:
                print(f"🔮 Detecting market regimes...")
                try:
                    detector = RegimeDetector(
                        n_regimes=config['regime']['n_regimes'],
                        method=config['regime'].get('method', 'hdbscan'),
                        min_cluster_size=config['regime'].get('min_cluster_size', 100)
                    )
                    universe_with_regimes = detector.detect_regimes(universe_df)
                    regime_analysis = detector.analyze_regimes(universe_with_regimes)
                    
                    print(f"   Detected {regime_analysis['n_regimes']} regimes:")
                    for regime_id, regime_info in regime_analysis['regimes'].items():
                        print(f"   - {regime_info['name']}: {regime_info['pct']:.1f}% of data")
                except Exception as e:
                    print(f"   ⚠️  Regime detection failed: {e}")
                    universe_with_regimes = universe_df.copy()
            
            # Create labels for this universe (multi-config mode)
            labels_dict = run_label_workflow(universe_with_regimes, config)
            
            # Step 2.6: Mine Patterns (if enabled)
            pattern_mining_enabled = config.get('pattern_mining', {}).get('enabled', False)
            if pattern_mining_enabled and labels_dict:
                print(f"\n⛏️  Mining patterns with ML...")
                try:
                    # Use first label config for pattern mining
                    first_label_config = list(labels_dict.keys())[0]
                    first_labels = labels_dict[first_label_config]
                    
                    miner = PatternMiner(
                        use_shap=config['pattern_mining'].get('use_shap', True),
                        top_features=config['pattern_mining'].get('top_features', 50)
                    )
                    mining_results = miner.discover_patterns(universe_with_regimes, first_labels)
                    
                    importance = miner.get_feature_importance()
                    if len(importance) > 0:
                        print(f"   Top 10 important features:")
                        for idx, row in importance.head(10).iterrows():
                            print(f"   {idx+1}. {row['feature']}: {row['importance']:.4f}")
                        
                        # Save patterns
                        patterns_output_dir = Path(f"results/{year}-{month:02d}/{universe_name}")
                        patterns_output_dir.mkdir(parents=True, exist_ok=True)
                        patterns_path = patterns_output_dir / "ml_patterns.csv"
                        importance.to_csv(patterns_path, index=False)
                        print(f"   💾 ML patterns saved: {patterns_path}")
                except Exception as e:
                    print(f"   ⚠️  Pattern mining failed: {e}")
            
            # Generate patterns
            patterns = run_patterns_workflow(universe_with_regimes, strategies, lookback)
            
            # Run backtest for each label config
            for label_config, labels in labels_dict.items():
                output_dir_universe = Path(f"results/{year}-{month:02d}/{universe_name}/{label_config}")
                ranking = run_backtest_workflow(
                    patterns,
                    labels,
                    config['backtest']['risk_levels'],
                    config['backtest']['initial_balance'],
                    str(output_dir_universe)
                )
                
                # Add interval, lookback, and label_config info to ranking
                ranking['interval'] = interval
                ranking['lookback'] = lookback
                ranking['label_config'] = label_config
                
                all_results.append(ranking)
        
        # Combine all results
        print(f"\n{'='*80}")
        print(f"📊 COMBINING RESULTS FROM ALL UNIVERSES")
        print(f"{'='*80}\n")
        
        import pandas as pd
        combined = pd.concat(all_results, ignore_index=True)
        combined = combined.sort_values('total_return', ascending=False).reset_index(drop=True)
        combined.insert(0, 'overall_rank', range(1, len(combined) + 1))
        
        # Save combined ranking
        final_output_dir = Path(f"results/{year}-{month:02d}")
        final_ranking_path = final_output_dir / "ranking_all_universes.csv"
        combined.to_csv(final_ranking_path, index=False)
        
        # Show top 13 (the Legendaries)
        print(f"🏆 TOP 13 LENDÁRIOS:\n")
        print(combined.head(13).to_string(index=False))
    
    # Calculate execution time
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{'='*80}")
    print(f"✅ GRANDE TESTE COMPLETE!")
    print(f"{'='*80}")
    
    strategies_count = len(discover_strategies(config['strategies']['categories']))
    num_universes = len(intervals) * len(lookbacks)
    
    if pairs and base_url:
        print(f"📊 Results directory: {Path(f'results/{year}-{month:02d}')}")
        print(f"🏆 Final ranking: {Path(f'results/{year}-{month:02d}/ranking_all_pairs_universes.csv')}")
        print(f"⏱️  Duration: {duration}")
        total_combinations = strategies_count * len(pairs) * num_universes * len(config['backtest']['risk_levels'])
        print(f"🐉 Tested: {strategies_count} strategies × {len(pairs)} pairs × {num_universes} universes × {len(config['backtest']['risk_levels'])} risk levels")
        print(f"   Total combinations: {total_combinations:,}")
    else:
        print(f"📊 Results directory: {final_output_dir}")
        print(f"🏆 Final ranking: {final_ranking_path}")
        print(f"⏱️  Duration: {duration}")
        total_combinations = strategies_count * num_universes * len(config['backtest']['risk_levels'])
        print(f"🐉 Tested: {strategies_count} strategies × {num_universes} universes × {len(config['backtest']['risk_levels'])} risk levels")
        print(f"   Total combinations: {total_combinations:,}")
    
    print(f"{'='*80}\n")


def cmd_report(args, config):
    """
    Generate report from existing results.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    print(f"\n{'='*60}")
    print(f"📊 GENERATING REPORT")
    print(f"{'='*60}\n")
    
    results_dir = Path("results")
    
    if not results_dir.exists() or not any(results_dir.iterdir()):
        print(f"❌ No results found in {results_dir}")
        print(f"   Please run: python necrozma.py --full YYYY-MM")
        return
    
    # Find latest results
    latest = sorted(results_dir.iterdir(), reverse=True)[0]
    
    print(f"📂 Latest results: {latest}")
    
    # Check for ranking file
    ranking_file = latest / "ranking_all_lookbacks.csv"
    
    if not ranking_file.exists():
        ranking_file = latest / "ranking.csv"
    
    if ranking_file.exists():
        import pandas as pd
        ranking = pd.read_csv(ranking_file)
        
        print(f"\n🏆 TOP 13 LENDÁRIOS:\n")
        print(ranking.head(13).to_string(index=False))
        
        print(f"\n📊 Summary Statistics:")
        print(f"   Total strategies tested: {len(ranking)}")
        print(f"   Best return: {ranking['total_return'].max():.2f}%")
        print(f"   Worst return: {ranking['total_return'].min():.2f}%")
        print(f"   Average return: {ranking['total_return'].mean():.2f}%")
        print(f"   Positive strategies: {(ranking['total_return'] > 0).sum()} ({(ranking['total_return'] > 0).sum() / len(ranking) * 100:.1f}%)")
    else:
        print(f"❌ No ranking file found in {latest}")
    
    print()


def main():
    """
    Main entry point.
    """
    # ASCII Art
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🐉 NECROZMA v2 - Trading Strategy Laboratory 🐉           ║
    ║                                                               ║
    ║   "285 strategies enter. 13 Legendaries emerge."             ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)
    
    parser = argparse.ArgumentParser(
        description="🐉 NECROZMAv2 - Complete Trading Strategy Laboratory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete Grande Teste
  python necrozma.py --full 2026-01
  
  # Create universe only
  python necrozma.py --universe 2026-01
  
  # Create patterns only
  python necrozma.py --patterns 2026-01
  
  # Run backtest only
  python necrozma.py --backtest 2026-01
  
  # Generate report
  python necrozma.py --report
        """
    )
    
    # Commands
    parser.add_argument('--full', dest='date', metavar='YYYY-MM',
                        help='Run complete Grande Teste for specified month')
    parser.add_argument('--universe', dest='universe_date', metavar='YYYY-MM',
                        help='Create universe only')
    parser.add_argument('--patterns', dest='patterns_date', metavar='YYYY-MM',
                        help='Create patterns only')
    parser.add_argument('--backtest', dest='backtest_date', metavar='YYYY-MM',
                        help='Run backtest only')
    parser.add_argument('--report', action='store_true',
                        help='Generate report from existing results')
    
    # Config
    parser.add_argument('--config', default='config.yaml',
                        help='Path to config file (default: config.yaml)')
    
    args = parser.parse_args()
    
    # Load config
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print(f"❌ Config file not found: {args.config}")
        return 1
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return 1
    
    # Execute command
    try:
        if args.date:
            cmd_full(args, config)
        elif args.universe_date:
            args.date = args.universe_date
            cmd_universe(args, config)
        elif args.patterns_date:
            args.date = args.patterns_date
            cmd_patterns(args, config)
        elif args.backtest_date:
            args.date = args.backtest_date
            cmd_backtest(args, config)
        elif args.report:
            cmd_report(args, config)
        else:
            parser.print_help()
            return 1
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
