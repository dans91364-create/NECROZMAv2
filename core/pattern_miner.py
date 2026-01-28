#!/usr/bin/env python3
"""
🐉 NECROZMAv2 - PATTERN MINER

ML-based pattern discovery using feature importance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False


class PatternMiner:
    """
    ML-based pattern discovery and feature importance analysis.
    
    Usage:
        miner = PatternMiner()
        patterns = miner.discover_patterns(df, labels)
        importance = miner.get_feature_importance()
    """
    
    def __init__(self, use_shap: bool = True, top_features: int = 50):
        """
        Initialize pattern miner.
        
        Args:
            use_shap: Whether to calculate SHAP values (requires shap package)
            top_features: Number of top features to return
        """
        self.use_shap = use_shap and SHAP_AVAILABLE
        self.top_features = top_features
        self.models = {}
        self.feature_importance = {}
        self.shap_values = None
        self.feature_names = []
    
    def discover_patterns(self, df: pd.DataFrame, labels: pd.DataFrame) -> Dict:
        """
        Discover important patterns using ML.
        
        Args:
            df: DataFrame with features
            labels: DataFrame with labels/targets
            
        Returns:
            Dictionary with discovered patterns and importance scores
        """
        # Prepare features and target
        X, y = self._prepare_data(df, labels)
        
        if X is None or len(X) == 0:
            return {
                'patterns': {},
                'feature_importance': pd.DataFrame(),
                'message': 'No valid features extracted'
            }
        
        # Store feature names
        self.feature_names = list(X.columns)
        
        # Train models
        print("   Training models for feature importance...")
        self.models = self._train_models(X, y)
        
        # Calculate feature importance
        self._calculate_feature_importance(X, y)
        
        # Calculate SHAP values if enabled
        if self.use_shap and 'xgboost' in self.models:
            print("   Calculating SHAP values...")
            self.shap_values = self._calculate_shap_values(X)
        
        # Extract patterns
        patterns = self._extract_patterns(X, y)
        
        return {
            'patterns': patterns,
            'feature_importance': self.get_feature_importance(),
            'models': list(self.models.keys()),
            'n_features': len(self.feature_names),
            'n_samples': len(X)
        }
    
    def _prepare_data(self, df: pd.DataFrame, labels: pd.DataFrame) -> Tuple[Optional[pd.DataFrame], Optional[pd.Series]]:
        """
        Prepare features and target for training.
        
        Args:
            df: DataFrame with features
            labels: DataFrame with labels
            
        Returns:
            Tuple of (features, target)
        """
        # Select numeric columns as features
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Exclude certain columns
        exclude_cols = ['regime', 'label', 'target', 'signal', 'position']
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        if len(feature_cols) == 0:
            return None, None
        
        X = df[feature_cols].copy()
        
        # Create binary target from labels
        if 'signal' in labels.columns:
            y = labels['signal'].copy()
        elif 'label' in labels.columns:
            y = labels['label'].copy()
        else:
            # Use first column as target
            y = labels.iloc[:, 0].copy()
        
        # Align indices
        common_idx = X.index.intersection(y.index)
        X = X.loc[common_idx]
        y = y.loc[common_idx]
        
        # Drop NaN values
        valid_mask = ~(X.isna().any(axis=1) | y.isna())
        X = X[valid_mask]
        y = y[valid_mask]
        
        # Convert to binary classification if needed
        if y.nunique() > 2:
            # Convert to binary: positive (1) vs non-positive (0)
            y = (y > 0).astype(int)
        
        # Check if we have at least two classes
        if y.nunique() < 2:
            print("   ⚠️  Warning: Target has only one class. Cannot train classification models.")
            return None, None
        
        return X, y
    
    def _train_models(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Train XGBoost/RandomForest/LightGBM for feature importance.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Dictionary of trained models
        """
        models = {}
        
        # Split data for validation
        if len(X) > 100:
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(y.unique()) > 1 else None
            )
        else:
            X_train, X_val, y_train, y_val = X, X, y, y
        
        # Train XGBoost if available
        if XGBOOST_AVAILABLE:
            try:
                xgb_model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1,
                    eval_metric='logloss'
                )
                xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
                models['xgboost'] = xgb_model
            except Exception as e:
                print(f"   Warning: XGBoost training failed: {e}")
        
        # Train LightGBM if available
        if LIGHTGBM_AVAILABLE:
            try:
                lgb_model = lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
                lgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)])
                models['lightgbm'] = lgb_model
            except Exception as e:
                print(f"   Warning: LightGBM training failed: {e}")
        
        # Train RandomForest as fallback
        try:
            rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            rf_model.fit(X_train, y_train)
            models['random_forest'] = rf_model
        except Exception as e:
            print(f"   Warning: RandomForest training failed: {e}")
        
        return models
    
    def _calculate_feature_importance(self, X: pd.DataFrame, y: pd.Series):
        """
        Calculate feature importance from trained models.
        
        Args:
            X: Feature DataFrame
            y: Target Series
        """
        importance_dict = {}
        
        # XGBoost importance
        if 'xgboost' in self.models:
            model = self.models['xgboost']
            importance_dict['xgboost'] = dict(zip(
                X.columns,
                model.feature_importances_
            ))
        
        # LightGBM importance
        if 'lightgbm' in self.models:
            model = self.models['lightgbm']
            importance_dict['lightgbm'] = dict(zip(
                X.columns,
                model.feature_importances_
            ))
        
        # RandomForest importance
        if 'random_forest' in self.models:
            model = self.models['random_forest']
            importance_dict['random_forest'] = dict(zip(
                X.columns,
                model.feature_importances_
            ))
        
        # Permutation importance (using first available model)
        if self.models:
            first_model = list(self.models.values())[0]
            try:
                # Use a sample if data is too large
                if len(X) > 1000:
                    sample_idx = np.random.choice(len(X), 1000, replace=False)
                    X_sample = X.iloc[sample_idx]
                    y_sample = y.iloc[sample_idx]
                else:
                    X_sample = X
                    y_sample = y
                
                perm_importance = permutation_importance(
                    first_model, X_sample, y_sample,
                    n_repeats=5,
                    random_state=42,
                    n_jobs=-1
                )
                importance_dict['permutation'] = dict(zip(
                    X.columns,
                    perm_importance.importances_mean
                ))
            except Exception as e:
                print(f"   Warning: Permutation importance failed: {e}")
        
        self.feature_importance = importance_dict
    
    def _calculate_shap_values(self, X: pd.DataFrame) -> Optional[np.ndarray]:
        """
        Calculate SHAP values for interpretability.
        
        Args:
            X: Feature DataFrame
            
        Returns:
            SHAP values array or None
        """
        if not SHAP_AVAILABLE or 'xgboost' not in self.models:
            return None
        
        try:
            # Use a sample if data is too large
            if len(X) > 500:
                sample_idx = np.random.choice(len(X), 500, replace=False)
                X_sample = X.iloc[sample_idx]
            else:
                X_sample = X
            
            # Create SHAP explainer
            explainer = shap.TreeExplainer(self.models['xgboost'])
            shap_values = explainer.shap_values(X_sample)
            
            return shap_values
            
        except Exception as e:
            print(f"   Warning: SHAP calculation failed: {e}")
            return None
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        Get ranked feature importance.
        
        Returns:
            DataFrame with features ranked by importance
        """
        if not self.feature_importance:
            return pd.DataFrame()
        
        # Combine importance from all methods
        combined_importance = {}
        
        for method, importance in self.feature_importance.items():
            for feature, score in importance.items():
                if feature not in combined_importance:
                    combined_importance[feature] = []
                combined_importance[feature].append(score)
        
        # Average importance across methods
        avg_importance = {
            feature: np.mean(scores)
            for feature, scores in combined_importance.items()
        }
        
        # Create DataFrame
        importance_df = pd.DataFrame([
            {'feature': feature, 'importance': score}
            for feature, score in avg_importance.items()
        ])
        
        # Sort by importance
        importance_df = importance_df.sort_values('importance', ascending=False)
        importance_df = importance_df.reset_index(drop=True)
        
        # Limit to top features
        if len(importance_df) > self.top_features:
            importance_df = importance_df.head(self.top_features)
        
        return importance_df
    
    def _extract_patterns(self, X: pd.DataFrame, y: pd.Series) -> Dict:
        """
        Extract patterns from feature importance.
        
        Args:
            X: Feature DataFrame
            y: Target Series
            
        Returns:
            Dictionary of patterns
        """
        patterns = {}
        
        # Get top features
        importance_df = self.get_feature_importance()
        
        if len(importance_df) == 0:
            return patterns
        
        # Extract patterns from top features
        top_10 = importance_df.head(10)
        
        for rank, (idx, row) in enumerate(top_10.iterrows(), start=1):
            feature = row['feature']
            importance = row['importance']
            
            if feature in X.columns:
                feature_values = X[feature]
                
                # Calculate correlation with target
                if len(feature_values) > 0 and len(y) > 0:
                    # Align indices before correlation
                    aligned_features = feature_values.loc[y.index]
                    correlation = np.corrcoef(aligned_features, y)[0, 1]
                else:
                    correlation = 0.0
                
                patterns[feature] = {
                    'importance': float(importance),
                    'correlation': float(correlation),
                    'mean': float(feature_values.mean()),
                    'std': float(feature_values.std()),
                    'rank': rank
                }
        
        return patterns
    
    def get_shap_summary(self) -> Optional[Dict]:
        """
        Get SHAP values summary.
        
        Returns:
            Dictionary with SHAP summary statistics or None
        """
        if self.shap_values is None:
            return None
        
        try:
            # Calculate mean absolute SHAP values
            mean_shap = np.abs(self.shap_values).mean(axis=0)
            
            # Create summary
            shap_summary = pd.DataFrame({
                'feature': self.feature_names,
                'mean_shap': mean_shap
            })
            shap_summary = shap_summary.sort_values('mean_shap', ascending=False)
            
            return {
                'top_features': shap_summary.head(10).to_dict('records'),
                'total_features': len(self.feature_names)
            }
            
        except Exception as e:
            print(f"   Warning: SHAP summary failed: {e}")
            return None
