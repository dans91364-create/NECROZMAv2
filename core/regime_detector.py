#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - REGIME DETECTOR

Market Regime Detection using unsupervised learning.
Detects: Trending, Ranging, Volatile, Low-Volatility regimes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False


class RegimeDetector:
    """
    Market regime detection using unsupervised learning.
    
    Usage:
        detector = RegimeDetector()
        regimes = detector.detect_regimes(df)
        analysis = detector.analyze_regimes(regimes)
    """
    
    def __init__(self, n_regimes: int = 4, method: str = "hdbscan", min_cluster_size: int = 100):
        """
        Initialize regime detector.
        
        Args:
            n_regimes: Number of regimes to detect (for KMeans)
            method: Clustering method ('hdbscan' or 'kmeans')
            min_cluster_size: Minimum cluster size for HDBSCAN
        """
        self.n_regimes = n_regimes
        self.method = method
        self.min_cluster_size = min_cluster_size
        self.scaler = StandardScaler()
        self.model = None
        self.regime_names = {
            0: "Trending_Up",
            1: "Trending_Down", 
            2: "Ranging",
            3: "High_Volatility"
        }
    
    def _extract_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features for regime detection.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with regime features
        """
        features = pd.DataFrame(index=df.index)
        
        # Volatility features
        features['volatility'] = df['close'].pct_change().rolling(20).std()
        
        # Use ATR if available, otherwise calculate it
        if 'atr_14' in df.columns:
            features['atr_norm'] = df['atr_14'] / df['close']
        else:
            # Calculate simple ATR approximation
            if 'high' in df.columns and 'low' in df.columns:
                features['atr_norm'] = (df['high'] - df['low']).rolling(14).mean() / df['close']
            else:
                features['atr_norm'] = df['close'].rolling(14).std() / df['close']
        
        # Trend features
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        features['trend_strength'] = (df['close'] - sma_20) / (std_20 + 1e-8)
        features['momentum'] = df['close'].pct_change(10)
        
        # Range features
        if 'high' in df.columns and 'low' in df.columns:
            features['range_pct'] = (df['high'] - df['low']) / df['close']
        else:
            # Approximate range from volatility
            features['range_pct'] = features['volatility'] * 2
        
        return features.dropna()
    
    def detect_regimes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect market regimes using clustering.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            DataFrame with added 'regime' column
        """
        # Extract features
        features = self._extract_regime_features(df)
        
        if len(features) == 0:
            raise ValueError("No valid features extracted. Check input data.")
        
        # Scale features
        X_scaled = self.scaler.fit_transform(features)
        
        # Choose clustering method
        if self.method == "hdbscan" and HDBSCAN_AVAILABLE:
            # Use HDBSCAN
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=min(self.min_cluster_size, len(features) // 10),
                min_samples=5,
                metric='euclidean'
            )
            labels = clusterer.fit_predict(X_scaled)
            
            # Handle noise points (label -1) by assigning to nearest cluster
            if -1 in labels:
                noise_mask = labels == -1
                valid_labels = labels[~noise_mask]
                if len(valid_labels) > 0:
                    # Assign noise to most common cluster
                    most_common = pd.Series(valid_labels).mode()[0]
                    labels[noise_mask] = most_common
            
            self.model = clusterer
            
        else:
            # Use KMeans as fallback
            kmeans = KMeans(
                n_clusters=self.n_regimes,
                random_state=42,
                n_init=10
            )
            labels = kmeans.fit_predict(X_scaled)
            self.model = kmeans
        
        # Add regime labels to dataframe
        result = df.copy()
        regime_series = pd.Series(index=df.index, dtype='int64')
        regime_series.loc[features.index] = labels
        result['regime'] = regime_series
        
        # Forward fill regime labels for missing values
        result['regime'] = result['regime'].ffill().bfill()
        
        return result
    
    def analyze_regimes(self, df: pd.DataFrame) -> Dict:
        """
        Analyze regime characteristics and transitions.
        
        Args:
            df: DataFrame with 'regime' column
            
        Returns:
            Dictionary with regime analysis
        """
        if 'regime' not in df.columns:
            raise ValueError("DataFrame must have 'regime' column. Run detect_regimes() first.")
        
        regimes = df['regime'].dropna()
        unique_regimes = sorted(regimes.unique())
        
        analysis = {
            'regimes': {},
            'transitions': {},
            'n_regimes': len(unique_regimes)
        }
        
        # Analyze each regime
        for regime_id in unique_regimes:
            regime_mask = regimes == regime_id
            regime_data = df[regime_mask]
            
            # Calculate regime characteristics
            if len(regime_data) > 0:
                regime_info = {
                    'id': int(regime_id),
                    'name': self.regime_names.get(regime_id, f"Regime_{regime_id}"),
                    'count': int(regime_mask.sum()),
                    'pct': float(regime_mask.sum() / len(regimes) * 100),
                }
                
                # Calculate returns if possible
                if 'close' in regime_data.columns:
                    returns = regime_data['close'].pct_change().dropna()
                    if len(returns) > 0:
                        regime_info.update({
                            'avg_return': float(returns.mean()),
                            'volatility': float(returns.std()),
                            'sharpe': float(returns.mean() / (returns.std() + 1e-8))
                        })
                
                analysis['regimes'][int(regime_id)] = regime_info
        
        # Calculate transition probability matrix
        transitions = np.zeros((len(unique_regimes), len(unique_regimes)))
        regime_array = regimes.values
        
        for i in range(len(regime_array) - 1):
            from_regime = int(regime_array[i])
            to_regime = int(regime_array[i + 1])
            
            # Map to index in unique_regimes
            from_idx = unique_regimes.index(from_regime)
            to_idx = unique_regimes.index(to_regime)
            
            transitions[from_idx, to_idx] += 1
        
        # Normalize to probabilities
        row_sums = transitions.sum(axis=1, keepdims=True)
        transition_probs = np.divide(
            transitions, 
            row_sums, 
            out=np.zeros_like(transitions), 
            where=row_sums != 0
        )
        
        # Store as dictionary
        for i, from_regime in enumerate(unique_regimes):
            analysis['transitions'][int(from_regime)] = {
                int(to_regime): float(transition_probs[i, j])
                for j, to_regime in enumerate(unique_regimes)
            }
        
        return analysis
    
    def characterize_regime(self, regime_id: int, df: pd.DataFrame) -> str:
        """
        Characterize a regime based on its features.
        
        Args:
            regime_id: Regime identifier
            df: DataFrame with regime features
            
        Returns:
            String description of regime characteristics
        """
        if 'regime' not in df.columns:
            return "Unknown"
        
        regime_data = df[df['regime'] == regime_id]
        
        if len(regime_data) == 0:
            return "No data"
        
        # Extract feature statistics
        features = self._extract_regime_features(regime_data)
        
        if len(features) == 0:
            return "Insufficient data"
        
        # Characterize based on feature values
        avg_volatility = features['volatility'].mean()
        avg_trend = features['trend_strength'].mean()
        avg_momentum = features['momentum'].mean()
        
        characteristics = []
        
        # Volatility
        if avg_volatility > features['volatility'].quantile(0.75):
            characteristics.append("High Volatility")
        elif avg_volatility < features['volatility'].quantile(0.25):
            characteristics.append("Low Volatility")
        
        # Trend
        if avg_trend > 0.5:
            characteristics.append("Strong Uptrend")
        elif avg_trend < -0.5:
            characteristics.append("Strong Downtrend")
        elif abs(avg_trend) < 0.2:
            characteristics.append("Ranging")
        
        # Momentum
        if avg_momentum > 0.02:
            characteristics.append("Positive Momentum")
        elif avg_momentum < -0.02:
            characteristics.append("Negative Momentum")
        
        return ", ".join(characteristics) if characteristics else "Neutral"
