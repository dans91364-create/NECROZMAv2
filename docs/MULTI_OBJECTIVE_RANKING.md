# Multi-Objective Ranking System

## Overview

NECROZMAv2 now includes an advanced multi-objective ranking system that evaluates trading strategies based on multiple performance metrics, not just total return. This system helps identify the best strategies (the "13 Legendaries") using a composite score derived from:

- **Sharpe Ratio** (25%): Risk-adjusted return
- **Sortino Ratio** (20%): Downside risk only
- **Calmar Ratio** (15%): Return / max drawdown
- **Win Rate** (15%): Percentage of profitable trades
- **Profit Factor** (15%): Gross profit / gross loss
- **Max Drawdown** (10%): Worst peak-to-trough decline (inverted)

## New Files

### `core/light_finder.py`

Multi-objective strategy ranking system.

**Key Features:**
- Calculates advanced metrics (Sharpe, Sortino, Calmar ratios)
- Computes profit factor and expectancy from trade history
- Normalizes metrics to 0-1 scale for fair comparison
- Ranks strategies by weighted composite score
- Identifies top N "Legendary" strategies

**Usage:**
```python
from core.light_finder import LightFinder

# Initialize with custom weights (optional)
finder = LightFinder(weights={
    'sharpe_ratio': 0.25,
    'sortino_ratio': 0.20,
    'calmar_ratio': 0.15,
    'win_rate': 0.15,
    'profit_factor': 0.15,
    'max_drawdown': 0.10
})

# Rank strategies
ranking = finder.rank_strategies(backtest_results)

# Get top 13 legendaries
legendaries = finder.get_legendaries(ranking, n=13)

# Get best risk level per strategy
best_per_strategy = finder.get_best_per_strategy(ranking)
```

### `core/light_report.py`

Report generator for text, CSV, and JSON output (no HTML dashboard).

**Key Features:**
- Saves full ranking to CSV
- Saves top 13 legendaries to CSV
- Generates JSON summary statistics
- Creates formatted text report
- Outputs to console

**Usage:**
```python
from core.light_report import LightReport

# Initialize with output directory
report = LightReport(output_dir="results/2026-01")

# Generate all reports at once
report.generate_all(ranking, legendaries)

# Or generate individually
report.save_ranking_csv(ranking, "ranking_all.csv")
report.save_legendaries_csv(legendaries, "ranking_top13.csv")
report.save_summary_json(ranking, legendaries, "summary_stats.json")
report.generate_text_report(ranking, legendaries, "light_report.txt")
```

## Configuration

The ranking system can be configured in `config.yaml`:

```yaml
ranking:
  weights:
    sharpe_ratio: 0.25
    sortino_ratio: 0.20
    calmar_ratio: 0.15
    win_rate: 0.15
    profit_factor: 0.15
    max_drawdown: 0.10
  top_n: 13  # Number of legendaries
```

## Integration with Grande Teste

The multi-objective ranking is automatically applied when running the full workflow:

```bash
python necrozma.py --full 2026-01
```

**Output:**
```
🌟 Ranking strategies with multi-objective scoring...
📄 Generating reports...
📊 Ranking saved: results/2026-01/ranking_all.csv
🏆 Legendaries saved: results/2026-01/ranking_top13.csv
📋 Summary saved: results/2026-01/summary_stats.json
📄 Report saved: results/2026-01/light_report.txt

================================================================================
🐉 NECROZMAv2 - GRANDE TESTE REPORT
Generated: 2026-01-28 19:45:00
================================================================================

📊 SUMMARY STATISTICS
----------------------------------------
Total strategies tested: 6336
Profitable strategies: 2847 (44.9%)
Best return: 134.97%
Worst return: -89.32%
Average return: 3.21%
Average Sharpe: 0.342
Average Win Rate: 48.3%

🏆 TOP 13 LENDÁRIOS
--------------------------------------------------------------------------------
#   Strategy                  Return     Sharpe   Sortino  WinRate  MaxDD    Score   
--------------------------------------------------------------------------------
1   RSIClassic               134.97%     2.341    3.892    62.3%    12.4%   0.8234
2   BollingerBandwidth        98.32%     1.987    2.876    58.1%    15.2%   0.7651
3   MACDCrossover             87.21%     1.654    2.432    55.7%    18.3%   0.7123
...
```

## Report Files

After running a full workflow, you'll find these files in `results/YYYY-MM/`:

1. **`ranking_all.csv`**: Complete ranking of all strategy/risk combinations
2. **`ranking_top13.csv`**: Top 13 legendaries only
3. **`summary_stats.json`**: Summary statistics in JSON format
4. **`light_report.txt`**: Formatted text report
5. **`ranking_all_universes.csv`**: Combined ranking from old method (for comparison)

## Metrics Explained

### Sharpe Ratio
- Measures risk-adjusted return
- Higher is better
- Typical range: -2 to 4
- Normalized to 0-1 for scoring

### Sortino Ratio
- Like Sharpe but only considers downside risk
- Better for strategies with asymmetric returns
- Typical range: -2 to 6
- Normalized to 0-1 for scoring

### Calmar Ratio
- Return divided by maximum drawdown
- Measures return per unit of worst-case risk
- Typical range: 0 to 10
- Normalized to 0-1 for scoring

### Profit Factor
- Gross profit divided by gross loss
- Values > 1 indicate profitability
- Typical range: 0 to 5
- Normalized to 0-1 for scoring

### Win Rate
- Percentage of profitable trades
- Already in 0-100 range
- Directly normalized to 0-1

### Max Drawdown
- Worst peak-to-trough decline
- Lower is better (inverted in scoring)
- Typical range: 0-100%
- Inverted and normalized to 0-1

## Backward Compatibility

The system maintains full backward compatibility:

- Old `run_backtest_workflow()` calls still work
- Original ranking by total_return is still saved
- New multi-objective ranking is added on top
- No breaking changes to existing code

## Customization

You can customize the ranking weights in `config.yaml` to emphasize different metrics:

**Risk-averse profile:**
```yaml
ranking:
  weights:
    sharpe_ratio: 0.30
    sortino_ratio: 0.25
    max_drawdown: 0.20
    calmar_ratio: 0.15
    profit_factor: 0.05
    win_rate: 0.05
```

**Return-focused profile:**
```yaml
ranking:
  weights:
    sharpe_ratio: 0.35
    profit_factor: 0.25
    calmar_ratio: 0.20
    sortino_ratio: 0.10
    win_rate: 0.05
    max_drawdown: 0.05
```

## Notes

- The system requires `equity_curve` and `trades` data from backtests
- Metrics are calculated per strategy/risk combination
- Composite score is weighted average of normalized metrics
- Rankings are independent for each universe/label combination
- Final ranking combines all universes using multi-objective scores
