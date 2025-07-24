#!/usr/bin/env python3
"""
Enhanced Ensemble Learning System
Implements Claude's suggestions for advanced transformer ensemble with meta-learning
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime
import json
import pickle
from dataclasses import dataclass
from collections import defaultdict
import warnings

logger = logging.getLogger(__name__)

@dataclass
class ModelPrediction:
    """Represents a prediction from a single model"""
    model_name: str
    prediction: float
    confidence: float
    probability_scores: Dict[str, float]
    processing_time: float
    model_version: str = "1.0"

@dataclass
class EnsemblePrediction:
    """Represents the ensemble prediction result"""
    ensemble_prediction: float
    ensemble_confidence: float
    individual_predictions: List[ModelPrediction]
    meta_learner_prediction: Optional[float]
    weighted_prediction: float
    model_weights: Dict[str, float]
    ensemble_method: str
    reasoning: List[str]

class EnhancedTransformerEnsemble:
    """
    Advanced transformer ensemble with multiple combination strategies
    Implements Claude's suggestions for meta-learning and dynamic weighting
    """
    
    def __init__(self, base_analyzer=None):
        self.base_analyzer = base_analyzer
        self.meta_learner = None
        self.model_performance_history = defaultdict(list)
        self.ensemble_weights = {}
        self.confidence_threshold = 0.75
        self.models_initialized = False
        self.financial_models = {}
        
        # Performance tracking
        self.prediction_history = []
        self.model_accuracy_scores = defaultdict(float)
        
        # Ensemble strategies
        self.strategies = {
            'weighted_voting': self._weighted_voting_ensemble,
            'confidence_weighted': self._confidence_weighted_ensemble,
            'meta_learner': self._meta_learner_ensemble,
            'adaptive_hybrid': self._adaptive_hybrid_ensemble
        }
        
    def initialize_financial_ensemble(self) -> bool:
        """
        Initialize enhanced financial transformer models
        """
        try:
            # Check if transformers are available
            try:
                from transformers import pipeline
                import torch
                
                logger.info("Initializing enhanced financial transformer ensemble...")
                
                # Financial-specific models
                financial_models = {
                    'finbert_prosus': {
                        'model': "ProsusAI/finbert",
                        'task': "sentiment-analysis",
                        'weight': 0.3,
                        'specialty': 'financial_sentiment'
                    },
                    'finbert_yiyang': {
                        'model': "yiyanghkust/finbert-tone",
                        'task': "sentiment-analysis", 
                        'weight': 0.25,
                        'specialty': 'financial_tone'
                    },
                    'finance_bert': {
                        'model': "ahmedrachid/FinancialBERT-Sentiment-Analysis",
                        'task': "sentiment-analysis",
                        'weight': 0.2,
                        'specialty': 'financial_analysis'
                    },
                    'roberta_sentiment': {
                        'model': "cardiffnlp/twitter-roberta-base-sentiment-latest",
                        'task': "sentiment-analysis",
                        'weight': 0.15,
                        'specialty': 'general_sentiment'
                    },
                    'distilbert_financial': {
                        'model': "nlptown/bert-base-multilingual-uncased-sentiment",
                        'task': "sentiment-analysis",
                        'weight': 0.1,
                        'specialty': 'multilingual_sentiment'
                    }
                }
                
                # Initialize models with error handling
                initialized_models = {}
                for name, config in financial_models.items():
                    try:
                        logger.info(f"Loading {name}...")
                        model = pipeline(
                            config['task'],
                            model=config['model'],
                            return_all_scores=True,
                            device=0 if torch.cuda.is_available() else -1
                        )
                        initialized_models[name] = {
                            'pipeline': model,
                            'config': config,
                            'status': 'loaded',
                            'load_time': datetime.now()
                        }
                        logger.info(f"✅ {name} loaded successfully")
                        
                    except Exception as e:
                        logger.warning(f"❌ Failed to load {name}: {e}")
                        # Add fallback or skip
                        continue
                
                self.financial_models = initialized_models
                self.models_initialized = len(initialized_models) > 0
                
                if self.models_initialized:
                    # Initialize ensemble weights
                    self._initialize_ensemble_weights()
                    logger.info(f"✅ Financial ensemble initialized with {len(initialized_models)} models")
                    return True
                else:
                    logger.error("❌ No models could be loaded")
                    return False
                    
            except ImportError as e:
                logger.error(f"Transformers not available: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing financial ensemble: {e}")
            return False
    
    def ensemble_predict(self, text: str, symbol: str = None) -> EnsemblePrediction:
        """
        Generate ensemble prediction using multiple strategies
        """
        if not self.models_initialized:
            logger.warning("Models not initialized, attempting to initialize...")
            if not self.initialize_financial_ensemble():
                return self._fallback_prediction(text, "Models not available")
        
        try:
            # Get predictions from all models
            individual_predictions = self._get_individual_predictions(text)
            
            if not individual_predictions:
                return self._fallback_prediction(text, "No valid predictions")
            
            # Apply multiple ensemble strategies
            strategies_results = {}
            
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    result = strategy_func(individual_predictions, text)
                    strategies_results[strategy_name] = result
                except Exception as e:
                    logger.warning(f"Strategy {strategy_name} failed: {e}")
                    continue
            
            # Select best strategy based on confidence and historical performance
            best_strategy = self._select_best_strategy(strategies_results, individual_predictions)
            
            # Generate final ensemble prediction
            ensemble_prediction = self._generate_final_prediction(
                strategies_results, best_strategy, individual_predictions, text
            )
            
            # Update performance tracking
            self._update_performance_tracking(ensemble_prediction, individual_predictions)
            
            return ensemble_prediction
            
        except Exception as e:
            logger.error(f"Ensemble prediction failed: {e}")
            return self._fallback_prediction(text, str(e))
    
    def _get_individual_predictions(self, text: str) -> List[ModelPrediction]:
        """Get predictions from all available models"""
        predictions = []
        
        for model_name, model_info in self.financial_models.items():
            try:
                start_time = datetime.now()
                
                # Get model prediction
                result = model_info['pipeline'](text)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                # Parse results
                prediction_score, confidence = self._parse_model_output(result)
                
                prediction = ModelPrediction(
                    model_name=model_name,
                    prediction=prediction_score,
                    confidence=confidence,
                    probability_scores=self._extract_probability_scores(result),
                    processing_time=processing_time,
                    model_version=model_info['config'].get('version', '1.0')
                )
                
                predictions.append(prediction)
                
            except Exception as e:
                logger.warning(f"Model {model_name} prediction failed: {e}")
                continue
        
        return predictions
    
    def _parse_model_output(self, result: Any) -> Tuple[float, float]:
        """Parse model output to extract prediction and confidence"""
        try:
            if isinstance(result, list) and len(result) > 0:
                # Handle list of predictions
                if isinstance(result[0], dict):
                    # Standard transformer output
                    positive_score = 0
                    negative_score = 0
                    
                    for item in result:
                        label = item.get('label', '').upper()
                        score = item.get('score', 0)
                        
                        if 'POSITIVE' in label or 'POS' in label or label == 'LABEL_2':
                            positive_score = score
                        elif 'NEGATIVE' in label or 'NEG' in label or label == 'LABEL_0':
                            negative_score = score
                    
                    # Convert to sentiment score (-1 to 1)
                    if positive_score > 0 or negative_score > 0:
                        prediction = positive_score - negative_score
                        confidence = max(positive_score, negative_score)
                    else:
                        prediction = 0
                        confidence = 0.5
                else:
                    # Handle other formats
                    prediction = 0
                    confidence = 0.5
            else:
                prediction = 0
                confidence = 0.5
                
            return prediction, confidence
            
        except Exception as e:
            logger.warning(f"Error parsing model output: {e}")
            return 0.0, 0.5
    
    def _extract_probability_scores(self, result: Any) -> Dict[str, float]:
        """Extract detailed probability scores from model output"""
        try:
            scores = {}
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict):
                        label = item.get('label', 'unknown')
                        score = item.get('score', 0)
                        scores[label] = score
            return scores
        except:
            return {}
    
    def _weighted_voting_ensemble(self, predictions: List[ModelPrediction], text: str) -> Dict:
        """Simple weighted voting ensemble"""
        if not predictions:
            return {'prediction': 0, 'confidence': 0, 'method': 'weighted_voting'}
        
        total_weight = 0
        weighted_sum = 0
        
        for pred in predictions:
            model_weight = self.ensemble_weights.get(pred.model_name, 1.0)
            confidence_weight = pred.confidence
            
            combined_weight = model_weight * confidence_weight
            weighted_sum += pred.prediction * combined_weight
            total_weight += combined_weight
        
        final_prediction = weighted_sum / total_weight if total_weight > 0 else 0
        avg_confidence = np.mean([p.confidence for p in predictions])
        
        return {
            'prediction': final_prediction,
            'confidence': avg_confidence,
            'method': 'weighted_voting',
            'weights_used': {p.model_name: self.ensemble_weights.get(p.model_name, 1.0) for p in predictions}
        }
    
    def _confidence_weighted_ensemble(self, predictions: List[ModelPrediction], text: str) -> Dict:
        """Confidence-weighted ensemble"""
        if not predictions:
            return {'prediction': 0, 'confidence': 0, 'method': 'confidence_weighted'}
        
        total_confidence = sum(p.confidence for p in predictions)
        
        if total_confidence == 0:
            return {'prediction': 0, 'confidence': 0, 'method': 'confidence_weighted'}
        
        weighted_prediction = sum(p.prediction * p.confidence for p in predictions) / total_confidence
        ensemble_confidence = np.mean([p.confidence for p in predictions])
        
        return {
            'prediction': weighted_prediction,
            'confidence': ensemble_confidence,
            'method': 'confidence_weighted'
        }
    
    def _meta_learner_ensemble(self, predictions: List[ModelPrediction], text: str) -> Dict:
        """Meta-learner ensemble using trained meta-model"""
        if not predictions or not self.meta_learner:
            return self._confidence_weighted_ensemble(predictions, text)
        
        try:
            # Prepare features for meta-learner
            features = self._prepare_meta_features(predictions, text)
            
            # Get meta-learner prediction
            meta_prediction = self.meta_learner.predict_proba([features])[0]
            
            return {
                'prediction': meta_prediction[1] - meta_prediction[0],  # Convert to -1,1 scale
                'confidence': max(meta_prediction),
                'method': 'meta_learner',
                'meta_features': features
            }
        except Exception as e:
            logger.warning(f"Meta-learner prediction failed: {e}")
            return self._confidence_weighted_ensemble(predictions, text)
    
    def _adaptive_hybrid_ensemble(self, predictions: List[ModelPrediction], text: str) -> Dict:
        """Adaptive hybrid ensemble that combines multiple strategies"""
        if not predictions:
            return {'prediction': 0, 'confidence': 0, 'method': 'adaptive_hybrid'}
        
        # Get results from different strategies
        weighted_result = self._weighted_voting_ensemble(predictions, text)
        confidence_result = self._confidence_weighted_ensemble(predictions, text)
        
        # Determine which strategy to favor based on conditions
        avg_confidence = np.mean([p.confidence for p in predictions])
        prediction_variance = np.var([p.prediction for p in predictions])
        
        if avg_confidence > 0.8 and prediction_variance < 0.1:
            # High confidence, low variance -> favor confidence weighting
            alpha = 0.7
            primary_result = confidence_result
            reasoning = "High confidence, low variance - favoring confidence weighting"
        elif prediction_variance > 0.3:
            # High variance -> use weighted voting for stability
            alpha = 0.3
            primary_result = weighted_result
            reasoning = "High prediction variance - favoring weighted voting for stability"
        else:
            # Balanced approach
            alpha = 0.5
            primary_result = confidence_result
            reasoning = "Balanced conditions - equal weighting"
        
        # Combine results
        final_prediction = (alpha * primary_result['prediction'] + 
                          (1 - alpha) * weighted_result['prediction'])
        final_confidence = (alpha * primary_result['confidence'] + 
                          (1 - alpha) * weighted_result['confidence'])
        
        return {
            'prediction': final_prediction,
            'confidence': final_confidence,
            'method': 'adaptive_hybrid',
            'alpha': alpha,
            'reasoning': reasoning,
            'component_results': {
                'weighted': weighted_result,
                'confidence': confidence_result
            }
        }
    
    def _prepare_meta_features(self, predictions: List[ModelPrediction], text: str) -> List[float]:
        """Prepare features for meta-learner"""
        features = []
        
        # Individual model predictions
        for pred in predictions:
            features.append(pred.prediction)
            features.append(pred.confidence)
        
        # Ensemble statistics
        pred_values = [p.prediction for p in predictions]
        conf_values = [p.confidence for p in predictions]
        
        features.extend([
            np.mean(pred_values),
            np.std(pred_values),
            np.mean(conf_values),
            np.std(conf_values),
            len(predictions),
            len(text),  # Text length as a feature
            text.count('!'),  # Exclamation marks
            text.count('?'),  # Question marks
        ])
        
        # Pad features to fixed length (if needed)
        while len(features) < 20:
            features.append(0.0)
        
        return features[:20]  # Ensure fixed length
    
    def _select_best_strategy(self, strategies_results: Dict, predictions: List[ModelPrediction]) -> str:
        """Select the best ensemble strategy based on various criteria"""
        if not strategies_results:
            return 'confidence_weighted'  # Default fallback
        
        # Score each strategy
        strategy_scores = {}
        
        for strategy_name, result in strategies_results.items():
            score = 0
            
            # Confidence score
            score += result.get('confidence', 0) * 0.4
            
            # Historical performance (if available)
            historical_accuracy = self.model_accuracy_scores.get(strategy_name, 0.5)
            score += historical_accuracy * 0.3
            
            # Prediction reasonableness (not too extreme)
            prediction = result.get('prediction', 0)
            if -1 <= prediction <= 1:
                score += 0.2
            
            # Strategy-specific bonuses
            if strategy_name == 'meta_learner' and self.meta_learner:
                score += 0.1  # Bonus for having trained meta-learner
            
            strategy_scores[strategy_name] = score
        
        # Return strategy with highest score
        best_strategy = max(strategy_scores.items(), key=lambda x: x[1])[0]
        logger.debug(f"Selected strategy: {best_strategy} (score: {strategy_scores[best_strategy]:.3f})")
        
        return best_strategy
    
    def _generate_final_prediction(self, strategies_results: Dict, best_strategy: str,
                                 predictions: List[ModelPrediction], text: str) -> EnsemblePrediction:
        """Generate the final ensemble prediction"""
        
        best_result = strategies_results.get(best_strategy, {'prediction': 0, 'confidence': 0})
        
        # Calculate weighted prediction as backup
        weighted_result = strategies_results.get('weighted_voting', {'prediction': 0, 'confidence': 0})
        
        # Generate reasoning
        reasoning = [
            f"Used {best_strategy} ensemble strategy",
            f"Based on {len(predictions)} transformer models",
            f"Average model confidence: {np.mean([p.confidence for p in predictions]):.3f}"
        ]
        
        if best_strategy in strategies_results:
            strategy_info = strategies_results[best_strategy]
            if 'reasoning' in strategy_info:
                reasoning.append(strategy_info['reasoning'])
        
        # Model weights
        model_weights = {}
        for pred in predictions:
            base_weight = self.ensemble_weights.get(pred.model_name, 1.0)
            confidence_weight = pred.confidence
            model_weights[pred.model_name] = base_weight * confidence_weight
        
        # Normalize weights
        total_weight = sum(model_weights.values())
        if total_weight > 0:
            model_weights = {k: v/total_weight for k, v in model_weights.items()}
        
        return EnsemblePrediction(
            ensemble_prediction=best_result['prediction'],
            ensemble_confidence=best_result['confidence'],
            individual_predictions=predictions,
            meta_learner_prediction=strategies_results.get('meta_learner', {}).get('prediction'),
            weighted_prediction=weighted_result['prediction'],
            model_weights=model_weights,
            ensemble_method=best_strategy,
            reasoning=reasoning
        )
    
    def _initialize_ensemble_weights(self):
        """Initialize ensemble weights for loaded models"""
        default_weights = {
            'finbert_prosus': 0.3,
            'finbert_yiyang': 0.25,
            'finance_bert': 0.2,
            'roberta_sentiment': 0.15,
            'distilbert_financial': 0.1
        }
        
        # Set weights only for loaded models
        self.ensemble_weights = {}
        total_weight = 0
        
        for model_name in self.financial_models.keys():
            weight = default_weights.get(model_name, 0.1)
            self.ensemble_weights[model_name] = weight
            total_weight += weight
        
        # Normalize weights
        if total_weight > 0:
            self.ensemble_weights = {k: v/total_weight for k, v in self.ensemble_weights.items()}
        
        logger.info(f"Initialized ensemble weights: {self.ensemble_weights}")
    
    def _update_performance_tracking(self, ensemble_prediction: EnsemblePrediction, 
                                   individual_predictions: List[ModelPrediction]):
        """Update performance tracking for models and strategies"""
        # Store prediction for later evaluation
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'ensemble_prediction': ensemble_prediction,
            'individual_predictions': individual_predictions
        })
        
        # Keep only recent history
        if len(self.prediction_history) > 1000:
            self.prediction_history = self.prediction_history[-1000:]
    
    def _fallback_prediction(self, text: str, error_msg: str) -> EnsemblePrediction:
        """Generate fallback prediction when ensemble fails"""
        logger.warning(f"Using fallback prediction: {error_msg}")
        
        # Simple TextBlob fallback
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            fallback_sentiment = blob.sentiment.polarity
            fallback_confidence = abs(blob.sentiment.polarity) * 0.6  # Lower confidence for fallback
        except:
            fallback_sentiment = 0.0
            fallback_confidence = 0.1
        
        return EnsemblePrediction(
            ensemble_prediction=fallback_sentiment,
            ensemble_confidence=fallback_confidence,
            individual_predictions=[],
            meta_learner_prediction=None,
            weighted_prediction=fallback_sentiment,
            model_weights={},
            ensemble_method='fallback',
            reasoning=[f"Fallback due to: {error_msg}"]
        )
    
    def train_meta_learner(self, training_data: List[Dict]) -> bool:
        """
        Train XGBoost meta-learner for ensemble combination
        """
        try:
            # Try to import XGBoost
            try:
                import xgboost as xgb
            except ImportError:
                # Fallback to Random Forest
                from sklearn.ensemble import RandomForestClassifier
                logger.warning("XGBoost not available, using RandomForest for meta-learning")
                
                self.meta_learner = RandomForestClassifier(
                    n_estimators=100,
                    random_state=42,
                    class_weight='balanced'
                )
            else:
                self.meta_learner = xgb.XGBClassifier(
                    n_estimators=100,
                    random_state=42,
                    eval_metric='logloss'
                )
            
            # Prepare training data
            X = []
            y = []
            
            for sample in training_data:
                # Extract features from ensemble predictions
                features = self._prepare_meta_features_from_sample(sample)
                if features:
                    X.append(features)
                    # Binary classification: profitable (1) vs unprofitable (0)
                    outcome = 1 if sample.get('actual_outcome') == 'PROFITABLE' else 0
                    y.append(outcome)
            
            if len(X) < 10:
                logger.warning(f"Insufficient training data for meta-learner: {len(X)} samples")
                return False
            
            # Train meta-learner
            logger.info(f"Training meta-learner with {len(X)} samples...")
            self.meta_learner.fit(X, y)
            
            # Evaluate meta-learner
            if len(X) > 20:
                from sklearn.model_selection import cross_val_score
                scores = cross_val_score(self.meta_learner, X, y, cv=3)
                logger.info(f"Meta-learner cross-validation score: {np.mean(scores):.3f} ± {np.std(scores):.3f}")
            
            logger.info("✅ Meta-learner trained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Meta-learner training failed: {e}")
            return False
    
    def _prepare_meta_features_from_sample(self, sample: Dict) -> Optional[List[float]]:
        """Prepare meta-features from a training sample"""
        try:
            # Extract individual model predictions
            model_predictions = sample.get('model_predictions', {})
            if not model_predictions:
                return None
            
            features = []
            
            # Individual model scores
            for model_name in ['finbert_prosus', 'finbert_yiyang', 'finance_bert', 
                             'roberta_sentiment', 'distilbert_financial']:
                pred_data = model_predictions.get(model_name, {})
                features.append(pred_data.get('prediction', 0))
                features.append(pred_data.get('confidence', 0.5))
            
            # Additional features
            features.extend([
                sample.get('sentiment_score', 0),
                sample.get('confidence', 0.5),
                sample.get('news_count', 0),
                len(sample.get('text', '')),
                sample.get('market_volatility', 0.5)
            ])
            
            # Pad to fixed length
            while len(features) < 20:
                features.append(0.0)
            
            return features[:20]
            
        except Exception as e:
            logger.warning(f"Error preparing meta-features: {e}")
            return None
    
    def update_model_weights(self, performance_data: Dict):
        """Update ensemble weights based on recent performance"""
        try:
            for model_name, accuracy in performance_data.items():
                if model_name in self.ensemble_weights:
                    # Adjust weight based on performance
                    current_weight = self.ensemble_weights[model_name]
                    
                    if accuracy > 0.7:  # Good performance
                        new_weight = min(1.0, current_weight * 1.1)
                    elif accuracy < 0.4:  # Poor performance
                        new_weight = max(0.05, current_weight * 0.9)
                    else:  # Average performance
                        new_weight = current_weight
                    
                    self.ensemble_weights[model_name] = new_weight
            
            # Renormalize weights
            total_weight = sum(self.ensemble_weights.values())
            if total_weight > 0:
                self.ensemble_weights = {k: v/total_weight for k, v in self.ensemble_weights.items()}
            
            logger.info(f"Updated ensemble weights: {self.ensemble_weights}")
            
        except Exception as e:
            logger.error(f"Error updating model weights: {e}")
    
    def get_ensemble_status(self) -> Dict:
        """Get current status of the ensemble system"""
        return {
            'models_initialized': self.models_initialized,
            'loaded_models': list(self.financial_models.keys()),
            'ensemble_weights': self.ensemble_weights,
            'meta_learner_trained': self.meta_learner is not None,
            'prediction_history_count': len(self.prediction_history),
            'available_strategies': list(self.strategies.keys()),
            'model_accuracy_scores': dict(self.model_accuracy_scores)
        }
