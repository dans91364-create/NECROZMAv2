# NECROZMAv2 - Implementation Guide

## 🐉 Overview

NECROZMAv2 is a complete trading strategy laboratory that tests 265+ strategies to find the best performing ones (the "Legendaries"). This is the LABORATORY version - it's designed for testing and validation, not live trading.

## 📁 Project Structure

```
NECROZMAv2/
├── necrozma.py              # Main CLI entry point
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── README.md               # Project overview
├── IMPLEMENTATION.md       # This file
│
├── core/                   # Core modules
│   ├── universe.py         # Data download, conversion, universe creation
│   ├── label.py            # Forward returns, labels, targets
│   ├── patterns.py         # Pattern generation, feature matrix
│   └── backtester.py       # Backtest engine, metrics, ranking
│
├── strategies/             # Trading strategies (265+ files)
│   ├── base.py             # BaseStrategy abstract class
│   ├── mean_reversion/     # 24 mean reversion strategies
│   │   ├── mean_reverter.py  # 🐉 Original Necrozma strategy
│   │   └── ...
│   ├── trend/              # 24 trend following strategies
│   ├── momentum/           # 24 momentum strategies
│   ├── volatility/         # 24 volatility strategies
│   ├── volume/             # 24 volume strategies
│   ├── smc/                # 24 Smart Money Concepts strategies
│   ├── fibonacci/          # 24 Fibonacci strategies
│   ├── harmonic/           # 24 Harmonic pattern strategies
│   ├── wyckoff/            # 24 Wyckoff strategies
│   ├── candlestick/        # 24 Candlestick pattern strategies
│   ├── chart_patterns/     # 24 Chart pattern strategies
│   └── exotic/             # 24 Exotic strategies
│
├── data/                   # Data directory (ignored by git)
│   ├── raw/                # Raw CSV files
│   ├── parquet/            # Compressed parquet files
│   ├── universe/           # Universe DataFrames
│   └── patterns/           # Pattern DataFrames
│
└── results/                # Results directory (ignored by git)
    └── YYYY-MM/            # Results by month
        ├── ranking.csv     # Strategy ranking
        ├── metrics.csv     # Detailed metrics
        └── report.html     # Visual report
```

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/dans91364-create/NECROZMAv2.git
cd NECROZMAv2

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Run complete Grande Teste for January 2026
python necrozma.py --full 2026-01

# Create universe only
python necrozma.py --universe 2026-01

# Create patterns only
python necrozma.py --patterns 2026-01

# Run backtest only
python necrozma.py --backtest 2026-01

# Generate report from existing results
python necrozma.py --report
```

## 🔄 Workflow

The system follows a 4-step workflow:

### 1. UNIVERSE Creation
- Downloads XAUUSD M1 data for specified month
- Converts CSV to Parquet (50% compression)
- Creates standardized DataFrame
- Calculates base indicators (SMA, EMA, RSI, ATR, Bollinger Bands, MACD, etc.)

### 2. LABEL Creation
- Calculates forward returns
- Creates win/loss labels based on TP/SL levels
- Defines target levels for each bar

### 3. PATTERN Generation
- Discovers all strategy classes
- Runs each strategy to generate signals
- Applies variable lookback (6-20)
- Creates feature matrix

### 4. BACKTEST Execution
- Simulates trades for all strategies
- Tests multiple risk levels (2% - 12.5%)
- Calculates performance metrics
- Generates ranking and report

## 📊 Configuration

Edit `config.yaml` to customize:

```yaml
data:
  source: exness          # Data source
  symbol: XAUUSD          # Trading symbol
  timeframe: M1           # Timeframe (M1 = 1 minute)

backtest:
  lookbacks: [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
  risk_levels: [2.0, 2.5, 3.0, ..., 12.0, 12.5]
  initial_balance: 200    # Starting balance

strategies:
  categories:             # 12 strategy categories
    - mean_reversion
    - trend
    - momentum
    # ... etc
```

## 🎯 Creating New Strategies

All strategies must inherit from `BaseStrategy`:

```python
from strategies.base import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    """My custom strategy."""
    
    def create_patterns(self, universe: pd.DataFrame) -> pd.DataFrame:
        """
        Create trading patterns from universe.
        
        Args:
            universe: DataFrame with OHLCV and indicators
            
        Returns:
            DataFrame with pattern features
        """
        patterns = universe.copy()
        # Add your pattern logic here
        return patterns
    
    def generate_signals(self, patterns: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals from patterns.
        
        Args:
            patterns: DataFrame with pattern features
            
        Returns:
            Series with signals (1=long, -1=short, 0=no trade)
        """
        signals = pd.Series(0, index=patterns.index)
        
        # Your signal logic here
        # signals[buy_condition] = 1
        # signals[sell_condition] = -1
        
        return signals
```

### Strategy Guidelines

1. **Inherit from BaseStrategy**: All strategies must inherit from the base class
2. **Implement required methods**: `create_patterns()` and `generate_signals()`
3. **Return standardized format**: Signals must be 1 (long), -1 (short), or 0 (no trade)
4. **Use self.lookback**: Access the lookback parameter for calculations
5. **Handle missing data**: Use `.fillna()` or `.dropna()` appropriately

### Example Strategies

#### 1. Mean Reverter (Original Necrozma)
```python
# strategies/mean_reversion/mean_reverter.py
class MeanReverter(BaseStrategy):
    """RSI-based mean reversion."""
    
    def generate_signals(self, patterns):
        signals = pd.Series(0, index=patterns.index)
        signals[patterns['rsi'] < 30] = 1   # Oversold = Long
        signals[patterns['rsi'] > 70] = -1  # Overbought = Short
        return signals
```

#### 2. MA Crossover
```python
# strategies/trend/ma_crossover.py
class MaCrossover(BaseStrategy):
    """Moving average crossover."""
    
    def generate_signals(self, patterns):
        signals = pd.Series(0, index=patterns.index)
        fast = patterns['close'].rolling(self.lookback).mean()
        slow = patterns['close'].rolling(self.lookback * 2).mean()
        signals[fast > slow] = 1   # Fast above slow = Long
        signals[fast < slow] = -1  # Fast below slow = Short
        return signals
```

## 📈 Understanding Results

### Ranking CSV
Contains the best configuration for each strategy:

```csv
rank,strategy,risk_level,final_balance,total_return,num_trades,win_rate,max_drawdown
1,rsimomentum,5.0,13283.41,6541.71%,86,100.0%,0.0%
2,macrossover,5.0,7044.48,3422.24%,73,100.0%,0.0%
3,meanreverter,2.0,250.00,25.00%,50,60.0%,-15.5%
```

### Key Metrics
- **rank**: Overall ranking (1 = best)
- **strategy**: Strategy name
- **risk_level**: Optimal risk percentage
- **total_return**: Return on initial balance
- **num_trades**: Number of trades executed
- **win_rate**: Percentage of winning trades
- **max_drawdown**: Maximum equity drawdown

## 🏆 Finding the Legendaries

The "Grande Teste" identifies the top 13 strategies (the Legendaries):

1. Run for a full month: `python necrozma.py --full 2026-01`
2. Check `results/2026-01/ranking_all_lookbacks.csv`
3. Top 13 strategies = Your Legendaries
4. Deploy these to live trading (future feature)

## 🔧 Troubleshooting

### Issue: No module named 'pandas'
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Universe not found
**Solution**: Create universe first
```bash
python necrozma.py --universe 2026-01
```

### Issue: No strategies discovered
**Solution**: Check that strategy classes are properly imported in category `__init__.py`

### Issue: All strategies return 0% return
**Solution**: Strategies are placeholders. Implement actual logic in `generate_signals()`

## 📝 Next Steps

### Immediate (This Release)
- ✅ Core architecture
- ✅ 265+ strategy placeholders
- ✅ Complete workflow
- ✅ Ranking system

### Short Term (Future PRs)
- [ ] Implement all 265 strategies with real logic
- [ ] Add more performance metrics (Sharpe, Sortino, etc.)
- [ ] Multi-month backtesting
- [ ] Equity curve visualization

### Long Term (Not in Laboratory)
- [ ] Telegram notifications
- [ ] Live ranking dashboard
- [ ] Account swapping system
- [ ] MT4/MT5 Expert Advisors
- [ ] Live trading integration

## 🤝 Contributing

To add a new strategy:

1. Choose appropriate category (or create new one)
2. Create strategy file: `strategies/category/my_strategy.py`
3. Implement BaseStrategy interface
4. Add to category's `__init__.py`
5. Test with: `python necrozma.py --full 2026-01`

## 📜 License

This is a personal trading research project. Use at your own risk.

## ⚠️ Disclaimer

**This is a LABORATORY for testing strategies, not financial advice.**

- Past performance does not guarantee future results
- Trading involves substantial risk of loss
- Test thoroughly before any live trading
- Never risk more than you can afford to lose
- The authors are not responsible for any losses

---

**🐉 NECROZMA v2 - "265 strategies enter. 13 Legendaries emerge."**
