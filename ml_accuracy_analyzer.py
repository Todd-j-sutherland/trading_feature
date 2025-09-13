#!/usr/bin/env python3
"""
ML Accuracy and Training Analysis Tool
Comprehensive analysis of machine learning model performance, feature importance, and training metrics
"""

import sqlite3
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLAccuracyAnalyzer:
    """Comprehensive ML accuracy and training analysis"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.predictions_df = None
        self.outcomes_df = None
        self.ml_features_df = None
        
    def load_data(self, days: int = 90) -> bool:
        """Load prediction and outcome data for analysis"""
        try:
            if not self.db_path.exists():
                logger.error(f"Database not found: {self.db_path}")
                return False
                
            conn = sqlite3.connect(self.db_path)
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Load predictions with features
            predictions_query = """
            SELECT 
                p.prediction_id,
                p.symbol,
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                p.entry_price,
                p.tech_score,
                p.news_sentiment,
                p.volume_trend,
                p.market_context,
                p.market_trend_pct,
                p.buy_threshold_used,
                p.confidence_breakdown,
                p.technical_indicators,
                p.model_version,
                p.feature_vector,
                p.news_impact_score,
                p.volume_trend_score,
                p.market_volatility,
                p.market_momentum
            FROM predictions p
            WHERE p.prediction_timestamp >= ?
            AND p.model_version NOT IN ('test_v1.0', 'test_model', 'dashboard_test_v1.0')
            ORDER BY p.prediction_timestamp DESC
            """
            
            self.predictions_df = pd.read_sql_query(predictions_query, conn, params=[cutoff_date.isoformat()])
            
            # Load outcomes
            outcomes_query = """
            SELECT 
                o.prediction_id,
                o.actual_return,
                o.entry_price as outcome_entry_price,
                o.exit_price,
                o.evaluation_timestamp,
                o.return_pct,
                o.success
            FROM outcomes o
            WHERE o.evaluation_timestamp >= ?
            """
            
            self.outcomes_df = pd.read_sql_query(outcomes_query, conn, params=[cutoff_date.isoformat()])
            conn.close()
            
            # Merge predictions with outcomes
            self.ml_features_df = self.predictions_df.merge(
                self.outcomes_df, 
                on='prediction_id', 
                how='left'
            )
            
            # Clean and prepare data
            self._prepare_ml_features()
            
            logger.info(f"Loaded {len(self.predictions_df)} predictions and {len(self.outcomes_df)} outcomes")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def _prepare_ml_features(self):
        """Prepare ML features for analysis"""
        if self.ml_features_df is None or self.ml_features_df.empty:
            return
            
        # Parse confidence breakdown for ML components
        self.ml_features_df['technical_component'] = 0.0
        self.ml_features_df['news_component'] = 0.0
        self.ml_features_df['volume_component'] = 0.0
        self.ml_features_df['risk_component'] = 0.0
        
        for idx, row in self.ml_features_df.iterrows():
            breakdown = self._parse_confidence_breakdown(row.get('confidence_breakdown', ''))
            self.ml_features_df.at[idx, 'technical_component'] = breakdown.get('tech', 0)
            self.ml_features_df.at[idx, 'news_component'] = breakdown.get('news', 0)
            self.ml_features_df.at[idx, 'volume_component'] = breakdown.get('volume', 0)
            self.ml_features_df.at[idx, 'risk_component'] = breakdown.get('risk', 0)
        
        # Create success labels for ML evaluation
        self.ml_features_df['success_binary'] = 0
        mask_buy_success = (self.ml_features_df['predicted_action'] == 'BUY') & (self.ml_features_df['actual_return'] > 0)
        mask_sell_success = (self.ml_features_df['predicted_action'] == 'SELL') & (self.ml_features_df['actual_return'] < 0)
        mask_hold_success = (self.ml_features_df['predicted_action'] == 'HOLD') & (abs(self.ml_features_df['actual_return']) < 1.0)
        
        self.ml_features_df.loc[mask_buy_success | mask_sell_success | mask_hold_success, 'success_binary'] = 1
        
        # Fill missing values
        numeric_columns = ['tech_score', 'news_sentiment', 'volume_trend', 'market_trend_pct', 
                          'technical_component', 'news_component', 'volume_component', 'action_confidence']
        
        for col in numeric_columns:
            if col in self.ml_features_df.columns:
                self.ml_features_df[col] = pd.to_numeric(self.ml_features_df[col], errors='coerce').fillna(0)
    
    def _parse_confidence_breakdown(self, breakdown_str: str) -> Dict[str, float]:
        """Parse confidence breakdown string"""
        components = {'tech': 0, 'news': 0, 'volume': 0, 'risk': 0}
        
        if not breakdown_str:
            return components
            
        try:
            # Try JSON format first
            if breakdown_str.startswith('{'):
                breakdown_json = json.loads(breakdown_str)
                components['tech'] = breakdown_json.get('technical_component', 0)
                components['news'] = breakdown_json.get('news_component', 0)
                components['volume'] = breakdown_json.get('volume_component', 0)
                components['risk'] = breakdown_json.get('risk_component', 0)
            else:
                # Parse string format: "Tech:0.381 + News:0.045 + Vol:0.030"
                parts = breakdown_str.split('+')
                for part in parts:
                    part = part.strip()
                    if 'Tech:' in part:
                        components['tech'] = float(part.split('Tech:')[1].strip().split()[0])
                    elif 'News:' in part:
                        components['news'] = float(part.split('News:')[1].strip().split()[0])
                    elif 'Vol:' in part:
                        components['volume'] = float(part.split('Vol:')[1].strip().split()[0])
                    elif 'Risk:' in part:
                        components['risk'] = float(part.split('Risk:')[1].strip().split()[0])
        except Exception as e:
            logger.debug(f"Error parsing breakdown: {e}")
            
        return components
    
    def analyze_ml_accuracy(self) -> Dict:
        """Comprehensive ML accuracy analysis"""
        if self.ml_features_df is None or self.ml_features_df.empty:
            return {"error": "No data loaded"}
        
        # Filter for predictions with outcomes
        df_with_outcomes = self.ml_features_df.dropna(subset=['actual_return'])
        
        if df_with_outcomes.empty:
            return {"error": "No predictions with outcomes found"}
        
        results = {}
        
        # Overall accuracy metrics
        results['overall'] = self._calculate_overall_accuracy(df_with_outcomes)
        
        # Component-wise accuracy
        results['component_analysis'] = self._analyze_component_accuracy(df_with_outcomes)
        
        # Feature importance analysis
        results['feature_importance'] = self._analyze_feature_importance(df_with_outcomes)
        
        # Model performance by conditions
        results['conditional_performance'] = self._analyze_conditional_performance(df_with_outcomes)
        
        # Training data quality assessment
        results['training_quality'] = self._assess_training_data_quality(df_with_outcomes)
        
        return results
    
    def _calculate_overall_accuracy(self, df: pd.DataFrame) -> Dict:
        """Calculate overall ML accuracy metrics"""
        try:
            total_predictions = len(df)
            successful_predictions = df['success_binary'].sum()
            overall_accuracy = successful_predictions / total_predictions if total_predictions > 0 else 0
            
            # Action-specific accuracy
            action_accuracy = {}
            for action in ['BUY', 'SELL', 'HOLD']:
                action_df = df[df['predicted_action'] == action]
                if len(action_df) > 0:
                    action_success = action_df['success_binary'].sum()
                    action_accuracy[action] = {
                        'accuracy': action_success / len(action_df),
                        'count': len(action_df),
                        'successful': action_success
                    }
            
            # Confidence-based accuracy
            confidence_buckets = {
                'low': df[df['action_confidence'] < 0.6],
                'medium': df[(df['action_confidence'] >= 0.6) & (df['action_confidence'] < 0.8)],
                'high': df[df['action_confidence'] >= 0.8]
            }
            
            confidence_accuracy = {}
            for bucket, bucket_df in confidence_buckets.items():
                if len(bucket_df) > 0:
                    confidence_accuracy[bucket] = {
                        'accuracy': bucket_df['success_binary'].mean(),
                        'count': len(bucket_df),
                        'avg_confidence': bucket_df['action_confidence'].mean()
                    }
            
            return {
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions,
                'overall_accuracy': overall_accuracy,
                'action_accuracy': action_accuracy,
                'confidence_accuracy': confidence_accuracy,
                'avg_confidence': df['action_confidence'].mean(),
                'confidence_std': df['action_confidence'].std()
            }
            
        except Exception as e:
            logger.error(f"Error calculating overall accuracy: {e}")
            return {"error": str(e)}
    
    def _analyze_component_accuracy(self, df: pd.DataFrame) -> Dict:
        """Analyze accuracy by ML component strength"""
        try:
            component_analysis = {}
            
            # Define component categories
            components = {
                'technical_component': 'Technical Analysis',
                'news_component': 'News Sentiment', 
                'volume_component': 'Volume Analysis'
            }
            
            for comp_col, comp_name in components.items():
                if comp_col not in df.columns:
                    continue
                    
                # Categorize by component strength
                comp_data = df[df[comp_col].notna()]
                if comp_data.empty:
                    continue
                
                # Define quartiles for component strength
                quartiles = comp_data[comp_col].quantile([0.25, 0.5, 0.75])
                
                categories = {
                    'weak': comp_data[comp_data[comp_col] <= quartiles[0.25]],
                    'moderate': comp_data[(comp_data[comp_col] > quartiles[0.25]) & (comp_data[comp_col] <= quartiles[0.75])],
                    'strong': comp_data[comp_data[comp_col] > quartiles[0.75]]
                }
                
                comp_results = {}
                for cat_name, cat_df in categories.items():
                    if len(cat_df) > 0:
                        comp_results[cat_name] = {
                            'accuracy': cat_df['success_binary'].mean(),
                            'count': len(cat_df),
                            'avg_component_value': cat_df[comp_col].mean(),
                            'avg_return': cat_df['actual_return'].mean() if 'actual_return' in cat_df.columns else 0
                        }
                
                # Component correlation with success
                correlation = comp_data[comp_col].corr(comp_data['success_binary'])
                
                component_analysis[comp_name] = {
                    'categories': comp_results,
                    'correlation_with_success': correlation,
                    'avg_value': comp_data[comp_col].mean(),
                    'std_value': comp_data[comp_col].std()
                }
            
            return component_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing component accuracy: {e}")
            return {"error": str(e)}
    
    def _analyze_feature_importance(self, df: pd.DataFrame) -> Dict:
        """Analyze feature importance using Random Forest"""
        try:
            # Prepare features for ML analysis
            feature_columns = [
                'action_confidence', 'tech_score', 'news_sentiment', 'volume_trend',
                'technical_component', 'news_component', 'volume_component',
                'market_trend_pct', 'buy_threshold_used'
            ]
            
            # Filter to only available columns
            available_features = [col for col in feature_columns if col in df.columns]
            
            if len(available_features) < 3:
                return {"error": "Insufficient features for importance analysis"}
            
            # Prepare feature matrix
            X = df[available_features].fillna(0)
            y = df['success_binary']
            
            # Remove rows with missing targets
            mask = y.notna()
            X = X[mask]
            y = y[mask]
            
            if len(X) < 10:
                return {"error": "Insufficient training samples"}
            
            # Train Random Forest for feature importance
            rf = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
            rf.fit(X, y)
            
            # Get feature importance
            importance_scores = rf.feature_importances_
            feature_importance = dict(zip(available_features, importance_scores))
            
            # Sort by importance
            sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            # Calculate ML model performance on this data
            y_pred = rf.predict(X)
            ml_accuracy = accuracy_score(y, y_pred)
            
            # Feature correlations
            feature_correlations = {}
            for feature in available_features:
                corr = X[feature].corr(y)
                feature_correlations[feature] = corr
            
            return {
                'feature_importance': feature_importance,
                'sorted_importance': sorted_importance,
                'ml_model_accuracy': ml_accuracy,
                'feature_correlations': feature_correlations,
                'training_samples': len(X),
                'feature_count': len(available_features)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing feature importance: {e}")
            return {"error": str(e)}
    
    def _analyze_conditional_performance(self, df: pd.DataFrame) -> Dict:
        """Analyze performance under different market conditions"""
        try:
            conditional_results = {}
            
            # Performance by market context
            if 'market_context' in df.columns:
                market_performance = {}
                for context in df['market_context'].unique():
                    if pd.isna(context):
                        continue
                    context_df = df[df['market_context'] == context]
                    if len(context_df) > 0:
                        market_performance[context] = {
                            'accuracy': context_df['success_binary'].mean(),
                            'count': len(context_df),
                            'avg_return': context_df['actual_return'].mean() if 'actual_return' in context_df.columns else 0,
                            'avg_confidence': context_df['action_confidence'].mean()
                        }
                conditional_results['market_context'] = market_performance
            
            # Performance by tech score ranges
            if 'tech_score' in df.columns:
                tech_score_ranges = {
                    'low_tech': df[df['tech_score'] < 50],
                    'medium_tech': df[(df['tech_score'] >= 50) & (df['tech_score'] < 70)],
                    'high_tech': df[df['tech_score'] >= 70]
                }
                
                tech_performance = {}
                for range_name, range_df in tech_score_ranges.items():
                    if len(range_df) > 0:
                        tech_performance[range_name] = {
                            'accuracy': range_df['success_binary'].mean(),
                            'count': len(range_df),
                            'avg_tech_score': range_df['tech_score'].mean()
                        }
                conditional_results['tech_score_ranges'] = tech_performance
            
            # Performance by news sentiment
            if 'news_sentiment' in df.columns:
                sentiment_ranges = {
                    'negative': df[df['news_sentiment'] < -0.05],
                    'neutral': df[(df['news_sentiment'] >= -0.05) & (df['news_sentiment'] <= 0.05)],
                    'positive': df[df['news_sentiment'] > 0.05]
                }
                
                sentiment_performance = {}
                for range_name, range_df in sentiment_ranges.items():
                    if len(range_df) > 0:
                        sentiment_performance[range_name] = {
                            'accuracy': range_df['success_binary'].mean(),
                            'count': len(range_df),
                            'avg_sentiment': range_df['news_sentiment'].mean()
                        }
                conditional_results['sentiment_ranges'] = sentiment_performance
            
            return conditional_results
            
        except Exception as e:
            logger.error(f"Error analyzing conditional performance: {e}")
            return {"error": str(e)}
    
    def _assess_training_data_quality(self, df: pd.DataFrame) -> Dict:
        """Assess quality of training data"""
        try:
            quality_metrics = {}
            
            # Data completeness
            total_predictions = len(df)
            predictions_with_outcomes = df['actual_return'].notna().sum()
            completeness_rate = predictions_with_outcomes / total_predictions if total_predictions > 0 else 0
            
            # Feature completeness
            feature_columns = ['tech_score', 'news_sentiment', 'volume_trend', 'action_confidence']
            feature_completeness = {}
            for col in feature_columns:
                if col in df.columns:
                    non_null_count = df[col].notna().sum()
                    feature_completeness[col] = non_null_count / len(df)
            
            # Label distribution
            label_distribution = df['success_binary'].value_counts(normalize=True).to_dict()
            
            # Data recency
            if 'prediction_timestamp' in df.columns:
                df['prediction_timestamp'] = pd.to_datetime(df['prediction_timestamp'])
                latest_prediction = df['prediction_timestamp'].max()
                oldest_prediction = df['prediction_timestamp'].min()
                data_span_days = (latest_prediction - oldest_prediction).days
            else:
                data_span_days = 0
            
            # Feature variance (to detect if features are actually varying)
            feature_variance = {}
            for col in feature_columns:
                if col in df.columns and df[col].notna().sum() > 1:
                    feature_variance[col] = df[col].var()
            
            quality_metrics = {
                'total_predictions': total_predictions,
                'predictions_with_outcomes': predictions_with_outcomes,
                'data_completeness_rate': completeness_rate,
                'feature_completeness': feature_completeness,
                'label_distribution': label_distribution,
                'data_span_days': data_span_days,
                'feature_variance': feature_variance,
                'avg_features_per_prediction': sum(feature_completeness.values()) / len(feature_completeness) if feature_completeness else 0
            }
            
            # Quality score (0-1)
            quality_score = (
                completeness_rate * 0.4 +  # 40% weight on outcome completeness
                (sum(feature_completeness.values()) / len(feature_completeness) if feature_completeness else 0) * 0.3 +  # 30% on feature completeness
                min(1.0, data_span_days / 30) * 0.2 +  # 20% on data recency (30 days = full score)
                min(1.0, len(df) / 100) * 0.1  # 10% on data volume (100 samples = full score)
            )
            
            quality_metrics['overall_quality_score'] = quality_score
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error assessing training data quality: {e}")
            return {"error": str(e)}
    
    def get_ml_training_features_used(self) -> Dict:
        """Analyze what features are actually being used in ML training"""
        try:
            if self.ml_features_df is None or self.ml_features_df.empty:
                return {"error": "No data loaded"}
            
            feature_analysis = {}
            
            # Analyze feature vector if available
            if 'feature_vector' in self.ml_features_df.columns:
                feature_vectors = self.ml_features_df['feature_vector'].dropna()
                if len(feature_vectors) > 0:
                    # Try to parse feature vectors
                    try:
                        sample_vector = feature_vectors.iloc[0]
                        if isinstance(sample_vector, str) and sample_vector.startswith('['):
                            parsed_vector = json.loads(sample_vector)
                            feature_analysis['feature_vector_length'] = len(parsed_vector)
                            feature_analysis['sample_features'] = parsed_vector[:10]  # First 10 features
                    except:
                        feature_analysis['feature_vector_parsing'] = "Unable to parse feature vectors"
            
            # Analyze confidence breakdown components
            component_stats = {}
            for component in ['technical_component', 'news_component', 'volume_component']:
                if component in self.ml_features_df.columns:
                    comp_data = pd.to_numeric(self.ml_features_df[component], errors='coerce')
                    comp_data = comp_data.dropna()
                    if len(comp_data) > 0:
                        component_stats[component] = {
                            'mean': comp_data.mean(),
                            'std': comp_data.std(),
                            'min': comp_data.min(),
                            'max': comp_data.max(),
                            'non_zero_count': (comp_data != 0).sum(),
                            'usage_rate': (comp_data != 0).sum() / len(comp_data)
                        }
            
            feature_analysis['ml_components'] = component_stats
            
            # Analyze raw features being tracked
            raw_features = {}
            feature_columns = ['tech_score', 'news_sentiment', 'volume_trend', 'market_trend_pct', 
                             'action_confidence', 'buy_threshold_used']
            
            for feature in feature_columns:
                if feature in self.ml_features_df.columns:
                    feat_data = pd.to_numeric(self.ml_features_df[feature], errors='coerce')
                    feat_data = feat_data.dropna()
                    if len(feat_data) > 0:
                        raw_features[feature] = {
                            'mean': feat_data.mean(),
                            'std': feat_data.std(),
                            'range': feat_data.max() - feat_data.min(),
                            'completeness': len(feat_data) / len(self.ml_features_df)
                        }
            
            feature_analysis['raw_features'] = raw_features
            
            # Model versions being used
            if 'model_version' in self.ml_features_df.columns:
                model_versions = self.ml_features_df['model_version'].value_counts().to_dict()
                feature_analysis['model_versions'] = model_versions
            
            return feature_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing ML training features: {e}")
            return {"error": str(e)}
    
    def generate_ml_accuracy_report(self) -> str:
        """Generate comprehensive ML accuracy report"""
        if not self.load_data():
            return "Error: Could not load data for analysis"
        
        accuracy_results = self.analyze_ml_accuracy()
        training_features = self.get_ml_training_features_used()
        
        report = []
        report.append("=" * 80)
        report.append("MACHINE LEARNING ACCURACY ANALYSIS REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Data source: {self.db_path}")
        report.append("")
        
        # Overall Performance
        if 'overall' in accuracy_results and 'error' not in accuracy_results['overall']:
            overall = accuracy_results['overall']
            report.append("📊 OVERALL ML PERFORMANCE")
            report.append("-" * 40)
            report.append(f"Total Predictions Analyzed: {overall['total_predictions']}")
            report.append(f"Successful Predictions: {overall['successful_predictions']}")
            report.append(f"Overall Accuracy: {overall['overall_accuracy']:.1%}")
            report.append(f"Average Confidence: {overall['avg_confidence']:.1%}")
            report.append("")
            
            # Action-specific accuracy
            if 'action_accuracy' in overall:
                report.append("🎯 ACTION-SPECIFIC ACCURACY")
                report.append("-" * 30)
                for action, stats in overall['action_accuracy'].items():
                    report.append(f"{action}: {stats['accuracy']:.1%} ({stats['successful']}/{stats['count']} predictions)")
                report.append("")
            
            # Confidence-based accuracy
            if 'confidence_accuracy' in overall:
                report.append("🔒 CONFIDENCE-BASED ACCURACY")
                report.append("-" * 35)
                for conf_level, stats in overall['confidence_accuracy'].items():
                    report.append(f"{conf_level.upper()} Confidence: {stats['accuracy']:.1%} ({stats['count']} predictions)")
                report.append("")
        
        # Component Analysis
        if 'component_analysis' in accuracy_results and 'error' not in accuracy_results['component_analysis']:
            report.append("🤖 ML COMPONENT ANALYSIS")
            report.append("-" * 30)
            comp_analysis = accuracy_results['component_analysis']
            
            for comp_name, comp_data in comp_analysis.items():
                if 'correlation_with_success' in comp_data:
                    corr = comp_data['correlation_with_success']
                    report.append(f"{comp_name}:")
                    report.append(f"  Correlation with success: {corr:+.3f}")
                    report.append(f"  Average value: {comp_data['avg_value']:.3f}")
                    
                    if 'categories' in comp_data:
                        for cat_name, cat_stats in comp_data['categories'].items():
                            report.append(f"  {cat_name.upper()}: {cat_stats['accuracy']:.1%} accuracy ({cat_stats['count']} predictions)")
                    report.append("")
        
        # Feature Importance
        if 'feature_importance' in accuracy_results and 'error' not in accuracy_results['feature_importance']:
            feat_imp = accuracy_results['feature_importance']
            report.append("🏆 FEATURE IMPORTANCE RANKING")
            report.append("-" * 35)
            report.append(f"ML Model Accuracy on Training Data: {feat_imp['ml_model_accuracy']:.1%}")
            report.append(f"Training Samples: {feat_imp['training_samples']}")
            report.append("")
            
            if 'sorted_importance' in feat_imp:
                report.append("Top Features by Importance:")
                for i, (feature, importance) in enumerate(feat_imp['sorted_importance'][:10], 1):
                    correlation = feat_imp['feature_correlations'].get(feature, 0)
                    report.append(f"  {i:2d}. {feature:20s}: {importance:.3f} (corr: {correlation:+.3f})")
                report.append("")
        
        # Training Data Quality
        if 'training_quality' in accuracy_results and 'error' not in accuracy_results['training_quality']:
            quality = accuracy_results['training_quality']
            report.append("📈 TRAINING DATA QUALITY")
            report.append("-" * 30)
            report.append(f"Overall Quality Score: {quality['overall_quality_score']:.1%}")
            report.append(f"Data Completeness: {quality['data_completeness_rate']:.1%}")
            report.append(f"Data Span: {quality['data_span_days']} days")
            report.append("")
            
            if 'label_distribution' in quality:
                report.append("Success/Failure Distribution:")
                for label, ratio in quality['label_distribution'].items():
                    label_name = "Successful" if label == 1 else "Failed"
                    report.append(f"  {label_name}: {ratio:.1%}")
                report.append("")
        
        # ML Training Features
        if 'error' not in training_features:
            report.append("⚙️ ML TRAINING FEATURES")
            report.append("-" * 25)
            
            if 'ml_components' in training_features:
                report.append("ML Component Usage:")
                for comp_name, comp_stats in training_features['ml_components'].items():
                    usage_rate = comp_stats.get('usage_rate', 0)
                    mean_val = comp_stats.get('mean', 0)
                    report.append(f"  {comp_name:20s}: {usage_rate:.1%} usage, avg={mean_val:.3f}")
                report.append("")
            
            if 'raw_features' in training_features:
                report.append("Raw Feature Completeness:")
                for feat_name, feat_stats in training_features['raw_features'].items():
                    completeness = feat_stats.get('completeness', 0)
                    mean_val = feat_stats.get('mean', 0)
                    report.append(f"  {feat_name:20s}: {completeness:.1%} complete, avg={mean_val:.3f}")
                report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 20)
        
        if 'overall' in accuracy_results and 'error' not in accuracy_results['overall']:
            overall_acc = accuracy_results['overall']['overall_accuracy']
            if overall_acc < 0.5:
                report.append("❌ CRITICAL: Model accuracy below random chance (50%)")
                report.append("   Recommend: Complete model retraining with feature engineering")
            elif overall_acc < 0.6:
                report.append("⚠️  WARNING: Model accuracy below target (60%)")
                report.append("   Recommend: Review feature engineering and model parameters")
            elif overall_acc < 0.7:
                report.append("✅ GOOD: Model performing reasonably well")
                report.append("   Recommend: Continue monitoring and periodic retraining")
            else:
                report.append("🎉 EXCELLENT: Model performing very well")
                report.append("   Recommend: Maintain current approach, consider ensemble methods")
        
        # Feature-specific recommendations
        if 'feature_importance' in accuracy_results and 'error' not in accuracy_results['feature_importance']:
            feat_imp = accuracy_results['feature_importance']
            if 'sorted_importance' in feat_imp and len(feat_imp['sorted_importance']) > 0:
                top_feature = feat_imp['sorted_importance'][0]
                report.append(f"📊 Top performing feature: {top_feature[0]} (importance: {top_feature[1]:.3f})")
                
                # Check for low-importance features
                low_importance_features = [f for f, imp in feat_imp['sorted_importance'] if imp < 0.05]
                if low_importance_features:
                    report.append(f"🗑️  Consider removing low-importance features: {', '.join(low_importance_features[:3])}")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)

def main():
    """Main function to run ML accuracy analysis"""
    analyzer = MLAccuracyAnalyzer()
    
    print("🤖 Machine Learning Accuracy Analyzer")
    print("=" * 50)
    
    # Generate comprehensive report
    report = analyzer.generate_ml_accuracy_report()
    print(report)
    
    # Save report to file
    report_path = Path("logs") / f"ml_accuracy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to: {report_path}")

if __name__ == "__main__":
    main()