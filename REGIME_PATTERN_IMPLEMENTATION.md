# NECROZMA v2 - Regime Detector & Pattern Miner Implementation

## Overview

Successfully implemented two advanced ML-based analysis modules from NECROZMA v1 into v2:

1. **RegimeDetector** - Market regime detection using unsupervised learning
2. **PatternMiner** - ML-based pattern discovery and feature importance

## Files Created/Modified

### New Files
- `core/regime_detector.py` - Market regime detection module (305 lines)
- `core/pattern_miner.py` - Pattern mining module (438 lines)

### Modified Files
- `necrozma.py` - Integrated both modules into workflow
- `config.yaml` - Added configuration sections for regime and pattern_mining
- `requirements.txt` - Added ML dependencies

## Features Implemented

### RegimeDetector (`core/regime_detector.py`)

**Clustering Methods:**
- HDBSCAN (primary) - Hierarchical density-based clustering
- KMeans (fallback) - Traditional k-means clustering

**Features Extracted:**
- Volatility (20-period rolling std)
- ATR normalized (14-period ATR / close)
- Trend strength (standardized price distance from SMA)
- Momentum (10-period price change)
- Range percentage (high-low / close)

**Capabilities:**
- `detect_regimes()` - Detect market regimes using clustering
- `analyze_regimes()` - Analyze regime characteristics and statistics
- `characterize_regime()` - Provide human-readable regime description
- Transition probability matrices between regimes

**Regime Types Detected:**
- Trending_Up (Regime 0)
- Trending_Down (Regime 1)
- Ranging (Regime 2)
- High_Volatility (Regime 3)

### PatternMiner (`core/pattern_miner.py`)

**ML Models Used:**
- XGBoost (primary)
- LightGBM (alternative)
- RandomForest (fallback)

**Importance Methods:**
- Feature importance from tree-based models
- Permutation importance
- SHAP values for interpretability

**Capabilities:**
- `discover_patterns()` - Train models and discover patterns
- `get_feature_importance()` - Get ranked feature importance
- `get_shap_summary()` - Get SHAP value summary
- Automatic feature extraction from DataFrames
- Binary classification with multi-method importance

## Configuration

### Regime Detection Config (`config.yaml`)

```yaml
regime:
  n_regimes: 4                # Number of regimes for KMeans
  method: "hdbscan"           # Clustering method: "hdbscan" or "kmeans"
  min_cluster_size: 100       # Minimum cluster size for HDBSCAN
  features:                   # Features to use (currently hardcoded)
    - volatility
    - trend_strength
    - momentum
    - range_pct
```

### Pattern Mining Config (`config.yaml`)

```yaml
pattern_mining:
  enabled: true               # Enable/disable pattern mining
  methods:                    # ML methods to use (currently trains all available)
    - xgboost
    - random_forest
    - permutation
  top_features: 50           # Number of top features to return
  use_shap: true             # Calculate SHAP values (requires shap package)
```

## Dependencies Added

```
scikit-learn>=1.3.0
hdbscan>=0.8.29
xgboost>=1.7.0
lightgbm>=3.3.0
shap>=0.41.0
```

## Integration into Workflow

Both modules are integrated into the `cmd_full()` workflow in `necrozma.py`:

### Step 2.5: Regime Detection
```python
detector = RegimeDetector(
    n_regimes=config['regime']['n_regimes'],
    method=config['regime'].get('method', 'hdbscan'),
    min_cluster_size=config['regime'].get('min_cluster_size', 100)
)
universe_with_regimes = detector.detect_regimes(universe_df)
regime_analysis = detector.analyze_regimes(universe_with_regimes)
```

**Output:**
- Adds 'regime' column to universe DataFrame
- Prints regime distribution statistics
- Shows percentage of data in each regime

### Step 2.6: Pattern Mining
```python
miner = PatternMiner(
    use_shap=config['pattern_mining'].get('use_shap', True),
    top_features=config['pattern_mining'].get('top_features', 50)
)
mining_results = miner.discover_patterns(universe_with_regimes, first_labels)
importance = miner.get_feature_importance()
```

**Output:**
- Trains XGBoost/LightGBM/RandomForest models
- Calculates SHAP values (if enabled)
- Prints top 10 important features
- Saves feature importance to `ml_patterns.csv`

## Usage Example

```bash
# Run full workflow with regime detection and pattern mining
python necrozma.py --full 2026-01
```

**Expected Output:**
```
🔮 Detecting market regimes...
   Detected 4 regimes:
   - Trending_Up: 28.3% of data
   - Trending_Down: 24.1% of data
   - Ranging: 31.2% of data
   - High_Volatility: 16.4% of data

⛏️  Mining patterns with ML...
   Training models for feature importance...
   Calculating SHAP values...
   Top 10 important features:
   1. rsi_14: 0.0823
   2. bb_width: 0.0712
   3. macd_diff: 0.0654
   4. atr_14: 0.0598
   5. momentum: 0.0521
   ...
   💾 ML patterns saved: results/2026-01/universe_1m_10lb/ml_patterns.csv
```

## Testing

Created comprehensive test script (`/tmp/test_regime_pattern.py`) with synthetic data:

**RegimeDetector Test:**
- ✅ Creates 500 samples with regime-like behavior
- ✅ Tests KMeans clustering
- ✅ Tests regime detection and analysis
- ✅ Validates regime statistics and transitions

**PatternMiner Test:**
- ✅ Creates 500 samples with 7 features
- ✅ Tests all 3 model types (XGBoost, LightGBM, RandomForest)
- ✅ Tests SHAP value calculation
- ✅ Validates feature importance ranking

**All tests passed successfully.**

## Code Quality

### Code Review Addressed:
- ✅ Fixed iterrows() index usage for correct numbering
- ✅ Added warning when falling back to KMeans
- ✅ Protected division by zero in calculations
- ✅ Removed unused imports
- ✅ Fixed correlation calculation with aligned indices
- ✅ Added check for single-class labels
- ✅ Handle edge case when all HDBSCAN points are noise

### Security Scan:
- ✅ CodeQL scan: **0 vulnerabilities found**

## Benefits

1. **Regime-Aware Strategies** - Universe includes regime labels for regime-specific strategy selection
2. **Feature Selection** - Identifies most important features for prediction
3. **Interpretability** - SHAP values explain model decisions
4. **Better Ranking** - Can filter strategies by regime performance
5. **Automated Discovery** - ML automatically finds important patterns

## Notes

- Both modules work in single-pair and multi-pair modes
- HDBSCAN is optional - falls back to KMeans if not available
- SHAP calculation is optional - can be disabled in config
- Pattern mining saves results to CSV for further analysis
- Regime column added to universe can be used by strategies

## Compatibility

- ✅ Python 3.8+
- ✅ Pandas 2.0+
- ✅ NumPy 1.24+
- ✅ Scikit-learn 1.3+
- ✅ Optional: HDBSCAN, XGBoost, LightGBM, SHAP
