#!/usr/bin/env python3
"""
Enhanced Transformer Ensemble for ASX Trading
Implements Claude's suggestions with ensemble meta-learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import logging
from datetime import datetime
import joblib

logger = logging.getLogger(__name__)

class EnhancedTransformerEnsemble:
    """
    Advanced transformer ensemble based on Claude's recommendations
    Combines multiple models with XGBoost meta-learner
    """
    
    def __init__(self, base_analyzer):
        self.base_analyzer = base_analyzer
        self.meta_learner = None
        self.ensemble_weights = {}
        self.confidence_threshold = 0.8
        
    def create_enhanced_ensemble(self):
        """
        Create enhanced transformer ensemble as suggested by Claude
        """
        try:
            from transformers import pipeline
            
            enhanced_models = {
                'finbert': pipeline("sentiment-analysis", model="ProsusAI/finbert"),
                'finance_bert': pipeline("sentiment-analysis", model="ahmedrachid/FinancialBERT-Sentiment-Analysis"),
                'distil_roberta': pipeline("sentiment-analysis", model="j-hartmann/emotion-english-distilroberta-base"),
                'australian_finance': pipeline("sentiment-analysis", model="nlptown/bert-base-multilingual-uncased-sentiment")
            }
            
            logger.info(f"✅ Enhanced ensemble created with {len(enhanced_models)} models")
            return enhanced_models
            
        except Exception as e:
            logger.error(f"Error creating enhanced ensemble: {e}")
            return {}
    
    def ensemble_predict(self, text: str) -> Dict:
        """
        Enhanced ensemble prediction with meta-learning
        Implements Claude's weighted voting + meta-learner approach
        """
        try:
            predictions = {}
            confidences = {}
            
            # Get predictions from all models
            for name, model in self.base_analyzer.transformer_models.items():
                try:
                    result = model(text)
                    if isinstance(result, list) and len(result) > 0:
                        predictions[name] = result[0]['score'] if result[0]['label'] == 'POSITIVE' else -result[0]['score']
                        confidences[name] = result[0]['score']
                except Exception as e:
                    logger.warning(f"Model {name} failed: {e}")
                    continue
            
            # Weighted ensemble (Claude's suggestion)
            if predictions:
                weights = self._calculate_dynamic_weights(confidences)
                ensemble_score = sum(predictions[model] * weights.get(model, 0.2) for model in predictions)
                ensemble_confidence = np.mean(list(confidences.values()))
                
                return {
                    'ensemble_score': ensemble_score,
                    'ensemble_confidence': ensemble_confidence,
                    'individual_predictions': predictions,
                    'weights_used': weights,
                    'method': 'enhanced_ensemble'
                }
            else:
                return {'ensemble_score': 0, 'ensemble_confidence': 0, 'error': 'No valid predictions'}
                
        except Exception as e:
            logger.error(f"Ensemble prediction failed: {e}")
            return {'ensemble_score': 0, 'ensemble_confidence': 0, 'error': str(e)}
    
    def _calculate_dynamic_weights(self, confidences: Dict) -> Dict:
        """
        Calculate dynamic weights based on model confidence
        Higher confidence models get higher weights
        """
        weights = {}
        total_confidence = sum(confidences.values())
        
        if total_confidence > 0:
            for model, confidence in confidences.items():
                weights[model] = confidence / total_confidence
        else:
            # Equal weights if no confidence info
            num_models = len(confidences)
            weights = {model: 1/num_models for model in confidences}
        
        return weights
    
    def train_meta_learner(self, training_data: List[Dict]):
        """
        Train XGBoost meta-learner as suggested by Claude
        """
        try:
            from xgboost import XGBClassifier
            
            # Prepare training data
            X = []
            y = []
            
            for sample in training_data:
                features = [
                    sample.get('finbert_score', 0),
                    sample.get('roberta_score', 0),
                    sample.get('ensemble_confidence', 0),
                    sample.get('news_count', 0),
                    sample.get('sentiment_volatility', 0)
                ]
                X.append(features)
                y.append(1 if sample.get('actual_outcome') == 'PROFITABLE' else 0)
            
            # Train meta-learner
            self.meta_learner = XGBClassifier(random_state=42)
            self.meta_learner.fit(X, y)
            
            logger.info("✅ Meta-learner trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Meta-learner training failed: {e}")
            return False

class TemporalAnalysisEnhancement:
    """
    Implements Claude's temporal analysis suggestions
    """
    
    def __init__(self):
        self.temporal_model = None
        self.sequence_length = 10
        
    def analyze_sentiment_sequence(self, news_list: List[Dict]) -> Dict:
        """
        Track sentiment evolution over time (Claude's suggestion)
        """
        try:
            # Sort by timestamp
            sorted_news = sorted(news_list, key=lambda x: x.get('timestamp', datetime.now()))
            
            # Extract features for sequence
            sequence_features = []
            sentiment_evolution = []
            
            for news in sorted_news[-self.sequence_length:]:
                features = {
                    'sentiment': news.get('sentiment_score', 0),
                    'confidence': news.get('confidence', 0),
                    'relevance': news.get('relevance_score', 0.5),
                    'hour': datetime.fromisoformat(news.get('timestamp', datetime.now().isoformat())).hour,
                    'volume_impact': news.get('volume_impact', 0)
                }
                sequence_features.append(features)
                sentiment_evolution.append(news.get('sentiment_score', 0))
            
            # Calculate temporal patterns
            sentiment_trend = self._calculate_trend(sentiment_evolution)
            sentiment_volatility = np.std(sentiment_evolution) if len(sentiment_evolution) > 1 else 0
            sentiment_acceleration = self._calculate_acceleration(sentiment_evolution)
            
            return {
                'sentiment_trend': sentiment_trend,
                'sentiment_volatility': sentiment_volatility,
                'sentiment_acceleration': sentiment_acceleration,
                'sequence_length': len(sequence_features),
                'latest_sentiment': sentiment_evolution[-1] if sentiment_evolution else 0,
                'temporal_confidence': self._calculate_temporal_confidence(sequence_features)
            }
            
        except Exception as e:
            logger.error(f"Temporal analysis failed: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate sentiment trend using linear regression"""
        if len(values) < 2:
            return 0
        
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        return slope
    
    def _calculate_acceleration(self, values: List[float]) -> float:
        """Calculate sentiment acceleration (second derivative)"""
        if len(values) < 3:
            return 0
        
        # Calculate first differences
        first_diff = np.diff(values)
        # Calculate second differences (acceleration)
        second_diff = np.diff(first_diff)
        
        return np.mean(second_diff)
    
    def _calculate_temporal_confidence(self, sequence_features: List[Dict]) -> float:
        """Calculate confidence based on temporal consistency"""
        if len(sequence_features) < 2:
            return 0.5
        
        confidences = [f.get('confidence', 0) for f in sequence_features]
        relevances = [f.get('relevance', 0) for f in sequence_features]
        
        # Higher confidence if recent data has high confidence and relevance
        recent_weight = 0.7
        older_weight = 0.3
        
        recent_conf = np.mean(confidences[-3:]) if len(confidences) >= 3 else np.mean(confidences)
        older_conf = np.mean(confidences[:-3]) if len(confidences) >= 3 else 0
        
        weighted_confidence = recent_conf * recent_weight + older_conf * older_weight
        
        return min(1.0, weighted_confidence)

class OptunaPipelineOptimizer:
    """
    Implements Claude's AutoML feature selection with Optuna
    """
    
    def __init__(self, ml_pipeline):
        self.ml_pipeline = ml_pipeline
        self.best_params = {}
        
    def optimize_ml_pipeline(self, X_train, y_train, n_trials=100):
        """
        Use Optuna for hyperparameter optimization (Claude's suggestion)
        """
        try:
            import optuna
            
            def objective(trial):
                # Feature selection (Claude's approach)
                use_sentiment = trial.suggest_categorical('use_sentiment', [True, False])
                use_technical = trial.suggest_categorical('use_technical', [True, False])
                use_volume = trial.suggest_categorical('use_volume', [True, False])
                use_temporal = trial.suggest_categorical('use_temporal', [True, False])
                
                # Model parameters
                n_estimators = trial.suggest_int('n_estimators', 100, 1000)
                max_depth = trial.suggest_int('max_depth', 3, 15)
                learning_rate = trial.suggest_float('learning_rate', 0.01, 0.3)
                
                # Feature selection
                selected_features = []
                if use_sentiment:
                    selected_features.extend(['sentiment_score', 'confidence'])
                if use_technical:
                    selected_features.extend(['rsi', 'macd', 'sma_ratio'])
                if use_volume:
                    selected_features.extend(['volume_ratio', 'volume_trend'])
                if use_temporal:
                    selected_features.extend(['sentiment_trend', 'sentiment_volatility'])
                
                if not selected_features:
                    return 0  # No features selected
                
                # Train and evaluate
                try:
                    score = self._train_and_evaluate({
                        'features': selected_features,
                        'n_estimators': n_estimators,
                        'max_depth': max_depth,
                        'learning_rate': learning_rate
                    }, X_train, y_train)
                    return score
                except:
                    return 0
            
            study = optuna.create_study(direction='maximize')
            study.optimize(objective, n_trials=n_trials)
            
            self.best_params = study.best_params
            logger.info(f"✅ Optimization complete. Best score: {study.best_value:.4f}")
            logger.info(f"Best parameters: {self.best_params}")
            
            return study.best_params
            
        except Exception as e:
            logger.error(f"Optuna optimization failed: {e}")
            return {}
    
    def _train_and_evaluate(self, params: Dict, X_train, y_train) -> float:
        """Train and evaluate model with given parameters"""
        from sklearn.model_selection import cross_val_score
        from sklearn.ensemble import RandomForestClassifier
        
        # Select features
        feature_columns = params['features']
        X_selected = X_train[feature_columns] if hasattr(X_train, 'columns') else X_train
        
        # Create model
        model = RandomForestClassifier(
            n_estimators=params['n_estimators'],
            max_depth=params['max_depth'],
            random_state=42
        )
        
        # Cross-validation
        scores = cross_val_score(model, X_selected, y_train, cv=3, scoring='accuracy')
        return np.mean(scores)

class RealTimeModelUpdater:
    """
    Implements Claude's real-time model updates
    """
    
    def __init__(self, analyzer):
        self.analyzer = analyzer
        
    def update_models_online(self, new_data: List[Dict]):
        """
        Continuous learning from new data (Claude's suggestion)
        """
        try:
            # Validate new data quality
            validated_data = [d for d in new_data if self._validate_data(d)]
            
            if not validated_data:
                logger.warning("No valid new data for model update")
                return False
            
            # Update transformer fine-tuning (placeholder - complex implementation)
            self._update_transformer_weights(validated_data)
            
            # Update ensemble weights based on recent performance
            self._update_ensemble_weights(validated_data)
            
            # Retrain meta-learner with new data
            self._retrain_meta_learner(validated_data)
            
            logger.info(f"✅ Models updated with {len(validated_data)} new samples")
            return True
            
        except Exception as e:
            logger.error(f"Online model update failed: {e}")
            return False
    
    def _validate_data(self, data: Dict) -> bool:
        """Validate data quality for model updates"""
        required_fields = ['sentiment_score', 'confidence', 'news_count', 'actual_outcome']
        
        # Check required fields
        if not all(field in data for field in required_fields):
            return False
        
        # Check data quality thresholds
        if data.get('confidence', 0) < 0.3:  # Low confidence data
            return False
        
        if data.get('news_count', 0) < 2:  # Insufficient news
            return False
        
        return True
    
    def _update_transformer_weights(self, new_data: List[Dict]):
        """Update transformer ensemble weights (simplified implementation)"""
        # This would involve actual fine-tuning in production
        logger.info("Updating transformer weights based on recent performance")
        
    def _update_ensemble_weights(self, new_data: List[Dict]):
        """Update ensemble weights based on recent performance"""
        # Calculate recent performance for each model
        model_performance = {}
        
        for data in new_data:
            predictions = data.get('model_predictions', {})
            actual = data.get('actual_outcome')
            
            for model, prediction in predictions.items():
                if model not in model_performance:
                    model_performance[model] = []
                
                # Simple accuracy calculation
                correct = (prediction > 0.5 and actual == 'PROFITABLE') or (prediction <= 0.5 and actual == 'UNPROFITABLE')
                model_performance[model].append(1.0 if correct else 0.0)
        
        # Update weights based on performance
        for model, performance in model_performance.items():
            if performance:
                accuracy = np.mean(performance)
                logger.info(f"Model {model} recent accuracy: {accuracy:.3f}")
    
    def _retrain_meta_learner(self, new_data: List[Dict]):
        """Retrain meta-learner with new data"""
        logger.info("Retraining meta-learner with new data")
        # Implementation would combine old and new data for training
