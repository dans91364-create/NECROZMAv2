"""
Backtester Module - BACKTEST

This module handles:
- Running backtests for all strategies
- Calculating performance metrics
- Generating reports
- Ranking strategies
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
from pathlib import Path
import os


def run_backtest(patterns: pd.DataFrame, labels: pd.DataFrame, 
                 risk_levels: List[float], initial_balance: float = 200) -> Dict[str, Any]:
    """
    Run backtest simulation for all strategies.
    
    Args:
        patterns: DataFrame with pattern signals
        labels: DataFrame with labels
        risk_levels: List of risk levels to test (% of balance per trade)
        initial_balance: Initial account balance
        
    Returns:
        Dictionary with backtest results
    """
    print(f"🔬 Running backtest (balance=${initial_balance}, risk levels={len(risk_levels)})...")
    
    # Get signal columns
    signal_cols = [col for col in patterns.columns if col.startswith('signal_')]
    
    results = {}
    
    for signal_col in signal_cols:
        strategy_name = signal_col.replace('signal_', '')
        
        for risk_level in risk_levels:
            # Run simulation for this strategy and risk level
            result = simulate_strategy(
                patterns[signal_col],
                labels,
                risk_level,
                initial_balance
            )
            
            # Store results
            key = f"{strategy_name}_risk_{risk_level}"
            results[key] = result
    
    print(f"✅ Backtest completed: {len(results)} strategy/risk combinations tested")
    
    return results


def simulate_strategy(signals: pd.Series, labels: pd.DataFrame, 
                      risk_pct: float, initial_balance: float) -> Dict[str, Any]:
    """
    Simulate a single strategy.
    
    Args:
        signals: Series with trading signals (1=long, -1=short, 0=no trade)
        labels: DataFrame with labels
        risk_pct: Risk per trade as percentage
        initial_balance: Initial balance
        
    Returns:
        Dictionary with simulation results
    """
    balance = initial_balance
    equity_curve = [initial_balance]
    trades = []
    
    for i in range(len(signals)):
        signal = signals.iloc[i]
        
        if signal == 1:  # Long trade
            label = labels.iloc[i]['label_long'] if i < len(labels) else -1
            if label == 1:  # Win
                profit = balance * (risk_pct / 100)
                balance += profit
                trades.append({'type': 'long', 'result': 'win', 'profit': profit})
            elif label == 0:  # Loss
                loss = balance * (risk_pct / 100)
                balance -= loss
                trades.append({'type': 'long', 'result': 'loss', 'profit': -loss})
        
        elif signal == -1:  # Short trade
            label = labels.iloc[i]['label_short'] if i < len(labels) else -1
            if label == 1:  # Win
                profit = balance * (risk_pct / 100)
                balance += profit
                trades.append({'type': 'short', 'result': 'win', 'profit': profit})
            elif label == 0:  # Loss
                loss = balance * (risk_pct / 100)
                balance -= loss
                trades.append({'type': 'short', 'result': 'loss', 'profit': -loss})
        
        equity_curve.append(balance)
    
    # Calculate metrics
    total_return = (balance - initial_balance) / initial_balance * 100
    num_trades = len(trades)
    num_wins = sum(1 for t in trades if t['result'] == 'win')
    win_rate = num_wins / num_trades * 100 if num_trades > 0 else 0
    
    # Calculate max drawdown
    equity_array = np.array(equity_curve)
    running_max = np.maximum.accumulate(equity_array)
    drawdown = (equity_array - running_max) / running_max * 100
    max_drawdown = drawdown.min()
    
    return {
        'final_balance': balance,
        'total_return': total_return,
        'num_trades': num_trades,
        'num_wins': num_wins,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'equity_curve': equity_curve,
        'trades': trades
    }


def calculate_metrics(results: Dict[str, Any]) -> pd.DataFrame:
    """
    Calculate performance metrics from backtest results.
    
    Args:
        results: Dictionary with backtest results
        
    Returns:
        DataFrame with metrics for all strategies
    """
    print(f"📊 Calculating performance metrics...")
    
    metrics_list = []
    
    for key, result in results.items():
        # Parse key
        parts = key.rsplit('_risk_', 1)
        strategy_name = parts[0]
        risk_level = float(parts[1])
        
        metrics_list.append({
            'strategy': strategy_name,
            'risk_level': risk_level,
            'final_balance': result['final_balance'],
            'total_return': result['total_return'],
            'num_trades': result['num_trades'],
            'num_wins': result['num_wins'],
            'win_rate': result['win_rate'],
            'max_drawdown': result['max_drawdown']
        })
    
    metrics_df = pd.DataFrame(metrics_list)
    
    print(f"✅ Metrics calculated for {len(metrics_df)} combinations")
    
    return metrics_df


def generate_report(metrics: pd.DataFrame, output_dir: str = "results") -> str:
    """
    Generate HTML and CSV report from metrics.
    
    Args:
        metrics: DataFrame with metrics
        output_dir: Directory to save reports
        
    Returns:
        Path to HTML report
    """
    print(f"📄 Generating report...")
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, "metrics.csv")
    metrics.to_csv(csv_path, index=False)
    print(f"   CSV saved: {csv_path}")
    
    # Generate HTML
    html_path = os.path.join(output_dir, "report.html")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>NECROZMAv2 - Backtest Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #ffd700; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #444; padding: 12px; text-align: left; }}
            th {{ background-color: #333; color: #ffd700; }}
            tr:nth-child(even) {{ background-color: #222; }}
            .positive {{ color: #00ff00; }}
            .negative {{ color: #ff4444; }}
        </style>
    </head>
    <body>
        <h1>🐉 NECROZMAv2 - Grande Teste Report</h1>
        <p>Total Strategies Tested: {len(metrics['strategy'].unique())}</p>
        <p>Total Risk Levels: {len(metrics['risk_level'].unique())}</p>
        <p>Total Combinations: {len(metrics)}</p>
        
        <h2>Top 10 Performers</h2>
        {metrics.nlargest(10, 'total_return').to_html(index=False, classes='table')}
        
        <h2>All Results</h2>
        {metrics.to_html(index=False, classes='table')}
    </body>
    </html>
    """
    
    with open(html_path, 'w') as f:
        f.write(html_content)
    
    print(f"   HTML saved: {html_path}")
    
    return html_path


def rank_strategies(metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Rank all strategies by performance.
    
    Args:
        metrics: DataFrame with metrics
        
    Returns:
        DataFrame with ranked strategies
    """
    print(f"🏆 Ranking strategies...")
    
    # For each strategy, find the best performing risk level
    best_per_strategy = metrics.loc[metrics.groupby('strategy')['total_return'].idxmax()]
    
    # Sort by total return
    ranking = best_per_strategy.sort_values('total_return', ascending=False).reset_index(drop=True)
    
    # Add rank
    ranking.insert(0, 'rank', range(1, len(ranking) + 1))
    
    print(f"✅ Strategies ranked:")
    print(f"   Best: {ranking.iloc[0]['strategy']} ({ranking.iloc[0]['total_return']:.2f}%)")
    if len(ranking) > 1:
        print(f"   Worst: {ranking.iloc[-1]['strategy']} ({ranking.iloc[-1]['total_return']:.2f}%)")
    
    return ranking


def run_backtest_workflow(patterns: pd.DataFrame, labels: pd.DataFrame, 
                          risk_levels: List[float], initial_balance: float = 200,
                          output_dir: str = "results") -> pd.DataFrame:
    """
    Run complete backtest workflow.
    
    Args:
        patterns: DataFrame with patterns
        labels: DataFrame with labels
        risk_levels: List of risk levels to test
        initial_balance: Initial balance
        output_dir: Directory to save results
        
    Returns:
        DataFrame with ranked strategies
    """
    print(f"\n{'='*60}")
    print(f"🔬 BACKTEST")
    print(f"{'='*60}\n")
    
    # Step 1: Run backtest
    results = run_backtest(patterns, labels, risk_levels, initial_balance)
    
    # Step 2: Calculate metrics
    metrics = calculate_metrics(results)
    
    # Step 3: Generate report
    report_path = generate_report(metrics, output_dir)
    
    # Step 4: Rank strategies
    ranking = rank_strategies(metrics)
    
    # Save ranking
    ranking_path = os.path.join(output_dir, "ranking.csv")
    ranking.to_csv(ranking_path, index=False)
    print(f"📊 Ranking saved: {ranking_path}")
    
    print(f"\n{'='*60}")
    print(f"✅ BACKTEST COMPLETE - Report: {report_path}")
    print(f"{'='*60}\n")
    
    return ranking
