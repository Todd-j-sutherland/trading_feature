"""
ML Model Management Service - Bank-Specific Model Loading and Prediction

Purpose:
This service manages machine learning models for trading predictions, including
bank-specific models, ensemble models, and model performance tracking. It handles
model loading, prediction generation, and model lifecycle management.

Key Features:
- Bank-specific model loading from models/ directory
- Ensemble prediction combining multiple models
- Model performance tracking and metrics
- Model versioning and rollback capabilities
- Feature engineering and preprocessing
- Prediction confidence scoring

Model Types:
- Individual bank models (CBA, ANZ, NAB, WBC specific)
- Sector-wide models (financial services)
- Technical analysis models
- Sentiment-enhanced models
- Ensemble models combining multiple approaches

API Endpoints:
- load_model(model_name, symbol) - Load specific model
- predict(model_name, features, symbol) - Generate prediction
- get_ensemble_prediction(features, symbol) - Multi-model prediction
- list_available_models() - Get available models
- get_model_performance(model_name) - Model metrics
- retrain_model(model_name, data) - Trigger model retraining

Model Management:
- Automatic model loading on first use
- Model caching for performance
- Performance monitoring and alerts
- Version control and rollback

Integration:
- Used by Prediction Service for enhanced accuracy
- Integrates with Data Quality Service for feature validation
- Publishes model performance events

Dependencies:
- scikit-learn for model operations
- pandas for data preprocessing
- pickle for model serialization
- Model files in models/ directory

Related Files:
- models/*.pkl - Trained model files
- models/[symbol]/*.pkl - Bank-specific models
- data_quality_system/ - Feature validation
"""

import asyncio
import sys
import os
import pickle
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Settings.py integration for configuration management
SETTINGS_AVAILABLE = False
try:
    sys.path.append("app/config")
    import settings as Settings
    SETTINGS_AVAILABLE = True
except ImportError:
    try:
        sys.path.append("paper-trading-app/app/config")
        import settings as Settings
        SETTINGS_AVAILABLE = True
    except ImportError:
        Settings = None
        print("Warning: settings.py not found - using fallback configuration")

class MLModelService(BaseService):
    """Machine Learning model management and prediction service with settings.py integration"""
    
    def __init__(self):
        super().__init__("ml-model")
        
        # Load configuration from settings.py or use fallbacks
        if SETTINGS_AVAILABLE and hasattr(Settings, 'ML_CONFIG'):
            self.ml_config = Settings.ML_CONFIG
            self.models_dir = Settings.MODELS_DIR if hasattr(Settings, 'MODELS_DIR') else Path("models")
            self.bank_symbols = Settings.BANK_SYMBOLS if hasattr(Settings, 'BANK_SYMBOLS') else ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX"]
            self.bank_names = Settings.BANK_NAMES if hasattr(Settings, 'BANK_NAMES') else {}
            
            # Training configuration from settings
            self.training_config = self.ml_config.get('training', {
                'min_samples': 100,
                'validation_split': 0.2,
                'retrain_frequency_days': 7,
                'auto_retrain': True
            })
            
            # Model configuration
            self.model_config = self.ml_config.get('models', {})
            
            self.logger.info("Loaded ML configuration from settings.py")
        else:
            # Fallback configuration
            self.models_dir = Path("models")
            self.bank_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX"]
            self.bank_names = {
                'CBA.AX': 'Commonwealth Bank',
                'WBC.AX': 'Westpac',
                'ANZ.AX': 'ANZ',
                'NAB.AX': 'National Australia Bank',
                'MQG.AX': 'Macquarie Group'
            }
            self.training_config = {
                'min_samples': 100,
                'validation_split': 0.2,
                'retrain_frequency_days': 7,
                'auto_retrain': True
            }
            self.model_config = {
                'sentiment_ensemble': {'enabled': True, 'models': ['transformers', 'statistical', 'lexicon']},
                'price_prediction': {'enabled': True, 'lookback_periods': [5, 10, 20]},
                'risk_assessment': {'enabled': True, 'volatility_window': 20}
            }
            self.logger.warning("Settings.py not available - using fallback ML configuration")
        
        # Model management
        self.loaded_models = {}
        self.model_metadata = {}
        self.model_performance = {}
        
        # Bank-specific model directories based on settings
        self.bank_models_dir = {
            symbol: self.models_dir / symbol for symbol in self.bank_symbols
        }
        
        # Supported model types from configuration
        self.model_types = list(self.model_config.keys()) + [
            "ensemble_predictor",
            "technical_analyzer", 
            "sentiment_model",
            "volume_predictor",
            "risk_model"
        ]
        
        # Enhanced feature definitions based on settings configuration
        self.feature_schemas = {
            "technical": ["price", "rsi", "macd", "bollinger_upper", "bollinger_lower", "volume", "sma_20", "sma_50"],
            "sentiment": ["sentiment_score", "news_confidence", "news_volume", "sentiment_trend"],
            "volume": ["volume_ratio", "volume_trend", "volume_ma", "volume_breakout"],
            "market": ["market_sentiment", "sector_performance", "volatility_index", "market_correlation"],
            "ensemble": ["price", "rsi", "macd", "sentiment_score", "volume_ratio", "market_sentiment"]
        }
        
        # Register enhanced methods with settings integration
        self.register_handler("load_model", self.load_model)
        self.register_handler("predict", self.predict)
        self.register_handler("get_ensemble_prediction", self.get_ensemble_prediction)
        self.register_handler("list_available_models", self.list_available_models)
        self.register_handler("get_model_performance", self.get_model_performance)
        self.register_handler("unload_model", self.unload_model)
        self.register_handler("get_feature_importance", self.get_feature_importance)
        self.register_handler("validate_features", self.validate_features)
        self.register_handler("get_ml_config", self.get_ml_config)
        self.register_handler("get_training_status", self.get_training_status)
        self.register_handler("get_model_recommendations", self.get_model_recommendations)
        self.register_handler("check_retrain_schedule", self.check_retrain_schedule)
        
        # Initialize model discovery
        asyncio.create_task(self._discover_available_models())
    
    async def get_ml_config(self):
        """Get current ML configuration"""
        return {
            "ml_config": self.ml_config if hasattr(self, 'ml_config') else {},
            "training_config": self.training_config,
            "model_config": self.model_config,
            "bank_symbols": self.bank_symbols,
            "bank_names": self.bank_names,
            "models_directory": str(self.models_dir),
            "supported_model_types": self.model_types,
            "feature_schemas": self.feature_schemas,
            "settings_integration": SETTINGS_AVAILABLE
        }
    
    async def get_training_status(self):
        """Get training configuration and status"""
        return {
            "training_config": self.training_config,
            "auto_retrain_enabled": self.training_config.get('auto_retrain', False),
            "retrain_frequency_days": self.training_config.get('retrain_frequency_days', 7),
            "min_samples_required": self.training_config.get('min_samples', 100),
            "validation_split": self.training_config.get('validation_split', 0.2),
            "last_training_check": getattr(self, 'last_training_check', None),
            "models_requiring_retrain": await self._check_models_for_retraining()
        }
    
    async def _check_models_for_retraining(self):
        """Check which models might need retraining based on configuration"""
        retrain_candidates = []
        
        if not self.training_config.get('auto_retrain', False):
            return retrain_candidates
        
        retrain_frequency = self.training_config.get('retrain_frequency_days', 7)
        cutoff_date = datetime.now() - timedelta(days=retrain_frequency)
        
        for model_name, metadata in self.model_metadata.items():
            try:
                model_modified = datetime.fromisoformat(metadata['modified'].replace('Z', '+00:00'))
                if model_modified < cutoff_date:
                    retrain_candidates.append({
                        'model_name': model_name,
                        'last_modified': metadata['modified'],
                        'days_since_update': (datetime.now() - model_modified).days,
                        'symbol': metadata.get('symbol')
                    })
            except Exception as e:
                self.logger.warning(f"Could not parse modification date for {model_name}: {e}")
        
        return retrain_candidates
    
    async def get_model_recommendations(self, symbol: str = None, use_case: str = "general"):
        """Get model recommendations based on symbol and use case"""
        recommendations = {
            "symbol": symbol,
            "use_case": use_case,
            "recommended_models": [],
            "reasoning": []
        }
        
        # Bank-specific recommendations
        if symbol and symbol in self.bank_symbols:
            bank_name = self.bank_names.get(symbol, symbol)
            
            # Check if bank-specific models exist
            bank_models = [name for name, meta in self.model_metadata.items() 
                          if meta.get('symbol') == symbol]
            
            if bank_models:
                recommendations["recommended_models"].extend(bank_models)
                recommendations["reasoning"].append(f"Bank-specific models available for {bank_name}")
            else:
                recommendations["reasoning"].append(f"No bank-specific models found for {bank_name}, falling back to general models")
        
        # Use case specific recommendations
        if use_case == "sentiment":
            if "sentiment_ensemble" in self.model_config and self.model_config["sentiment_ensemble"].get("enabled"):
                recommendations["recommended_models"].append("sentiment_ensemble")
                recommendations["reasoning"].append("Sentiment ensemble model is enabled and configured")
        
        elif use_case == "price_prediction":
            if "price_prediction" in self.model_config and self.model_config["price_prediction"].get("enabled"):
                recommendations["recommended_models"].append("price_prediction")
                recommendations["reasoning"].append("Price prediction model is enabled with configured lookback periods")
        
        elif use_case == "risk_assessment":
            if "risk_assessment" in self.model_config and self.model_config["risk_assessment"].get("enabled"):
                recommendations["recommended_models"].append("risk_assessment")
                recommendations["reasoning"].append("Risk assessment model is enabled with volatility analysis")
        
        # General model recommendations
        general_models = [name for name, meta in self.model_metadata.items() 
                         if meta.get('type') == 'general']
        
        if not recommendations["recommended_models"] and general_models:
            recommendations["recommended_models"].extend(general_models[:3])  # Top 3 general models
            recommendations["reasoning"].append("Using general models as fallback")
        
        # Add confidence scoring
        recommendations["confidence_score"] = self._calculate_recommendation_confidence(recommendations)
        
        return recommendations
    
    def _calculate_recommendation_confidence(self, recommendations):
        """Calculate confidence score for model recommendations"""
        score = 0.5  # Base score
        
        # Boost for bank-specific models
        if any("bank-specific" in str(reason) for reason in recommendations["reasoning"]):
            score += 0.3
        
        # Boost for enabled models in config
        enabled_models = sum(1 for model_type, config in self.model_config.items() 
                           if config.get("enabled", False))
        score += min(0.2, enabled_models * 0.05)
        
        # Boost for multiple model options
        if len(recommendations["recommended_models"]) > 1:
            score += 0.1
        
        return min(1.0, score)
    
    async def check_retrain_schedule(self):
        """Check retrain schedule and provide recommendations"""
        if not self.training_config.get('auto_retrain', False):
            return {
                "auto_retrain_enabled": False,
                "message": "Auto-retrain is disabled in configuration"
            }
        
        retrain_candidates = await self._check_models_for_retraining()
        
        return {
            "auto_retrain_enabled": True,
            "retrain_frequency_days": self.training_config.get('retrain_frequency_days', 7),
            "models_needing_retrain": len(retrain_candidates),
            "retrain_candidates": retrain_candidates,
            "next_check": datetime.now() + timedelta(days=1),
            "recommendation": "Schedule retraining" if retrain_candidates else "Models are up to date"
        }
    
    async def _discover_available_models(self):
        """Discover available models in the models directory"""
        try:
            available_models = {}
            
            # Check general models directory
            if self.models_dir.exists():
                for model_file in self.models_dir.glob("*.pkl"):
                    model_name = model_file.stem
                    available_models[model_name] = {
                        "path": str(model_file),
                        "type": "general",
                        "symbol": None,
                        "size": model_file.stat().st_size,
                        "modified": datetime.fromtimestamp(model_file.stat().st_mtime).isoformat()
                    }
            
            # Check bank-specific models
            for symbol, bank_dir in self.bank_models_dir.items():
                if bank_dir.exists():
                    for model_file in bank_dir.glob("*.pkl"):
                        model_name = f"{symbol}_{model_file.stem}"
                        available_models[model_name] = {
                            "path": str(model_file),
                            "type": "bank_specific",
                            "symbol": symbol,
                            "size": model_file.stat().st_size,
                            "modified": datetime.fromtimestamp(model_file.stat().st_mtime).isoformat()
                        }
            
            self.model_metadata = available_models
            
            self.logger.info(f'"discovered_models": {len(available_models)}, "action": "model_discovery_completed"')
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "model_discovery_failed"')
    
    async def load_model(self, model_name: str, symbol: str = None, force_reload: bool = False):
        """Load a specific model into memory with comprehensive validation"""
        # Input validation
        if not model_name or not isinstance(model_name, str):
            return {"error": "Invalid model_name parameter", "model_name": model_name}
        
        # Sanitize inputs
        model_name = model_name.strip()
        if symbol:
            symbol = symbol.upper().strip() if isinstance(symbol, str) else None
        
        # Validate model name format
        if not model_name.replace('_', '').replace('-', '').isalnum():
            return {"error": "Invalid model_name format", "model_name": model_name}
        
        try:
            # Determine model key for caching
            model_key = f"{model_name}_{symbol}" if symbol else model_name
            
            # Check if already loaded (unless force reload)
            if not force_reload and model_key in self.loaded_models:
                self.logger.info(f'"model": "{model_key}", "action": "model_already_loaded"')
                return {
                    "model_name": model_name,
                    "symbol": symbol,
                    "status": "already_loaded",
                    "loaded_at": self.loaded_models[model_key]["loaded_at"],
                    "prediction_count": self.loaded_models[model_key]["prediction_count"]
                }
            
            # Find model file with security validation
            model_path = self._find_model_path(model_name, symbol)
            if not model_path:
                return {
                    "error": f"Model not found: {model_name}" + (f" for symbol {symbol}" if symbol else ""),
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            # Validate model file security
            if not self._validate_model_file_security(model_path):
                return {
                    "error": "Model file failed security validation",
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            # Load the model with error handling and size limits
            try:
                file_size = Path(model_path).stat().st_size
                max_size = 100 * 1024 * 1024  # 100MB limit
                
                if file_size > max_size:
                    return {
                        "error": f"Model file too large: {file_size / 1024 / 1024:.1f}MB (max: {max_size / 1024 / 1024}MB)",
                        "model_name": model_name,
                        "symbol": symbol
                    }
                
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
                
                # Validate loaded model
                if not self._validate_loaded_model(model, model_name):
                    return {
                        "error": "Loaded model failed validation checks",
                        "model_name": model_name,
                        "symbol": symbol
                    }
                
            except (pickle.PickleError, EOFError) as e:
                return {
                    "error": f"Model file corrupted or invalid: {e}",
                    "model_name": model_name,
                    "symbol": symbol
                }
            except (PermissionError, FileNotFoundError) as e:
                return {
                    "error": f"Model file access error: {e}",
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            # Store in cache with metadata
            self.loaded_models[model_key] = {
                "model": model,
                "model_name": model_name,
                "symbol": symbol,
                "path": model_path,
                "loaded_at": datetime.now().isoformat(),
                "prediction_count": 0,
                "last_used": datetime.now().isoformat(),
                "file_size": file_size,
                "model_type": self._determine_model_type(model)
            }
            
            # Initialize performance tracking
            if model_key not in self.model_performance:
                self.model_performance[model_key] = {
                    "predictions_made": 0,
                    "average_confidence": 0.0,
                    "accuracy_history": [],
                    "last_evaluation": None,
                    "error_count": 0,
                    "total_prediction_time": 0.0
                }
            
            self.logger.info(f'"model": "{model_key}", "path": "{model_path}", "size_mb": {file_size / 1024 / 1024:.2f}, "action": "model_loaded"')
            
            return {
                "model_name": model_name,
                "symbol": symbol,
                "status": "loaded",
                "loaded_at": self.loaded_models[model_key]["loaded_at"],
                "model_path": model_path,
                "file_size_mb": round(file_size / 1024 / 1024, 2),
                "model_type": self.loaded_models[model_key]["model_type"]
            }
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "symbol": "{symbol}", "error": "{e}", "action": "model_load_failed"')
            return {"error": str(e), "model_name": model_name, "symbol": symbol}
    
    def _validate_model_file_security(self, model_path: str) -> bool:
        """Validate model file security and integrity"""
        try:
            path_obj = Path(model_path)
            
            # Check if file exists and is a file
            if not path_obj.exists() or not path_obj.is_file():
                return False
            
            # Validate file is within expected directories
            models_dir_abs = Path("models").resolve()
            model_path_abs = path_obj.resolve()
            
            try:
                model_path_abs.relative_to(models_dir_abs)
            except ValueError:
                # File is outside models directory tree
                self.logger.error(f'"model_path": "{model_path}", "error": "path_outside_models_directory", "action": "security_validation_failed"')
                return False
            
            # Check file permissions
            if not os.access(model_path, os.R_OK):
                return False
            
            # Basic file extension check
            if not model_path.endswith('.pkl'):
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f'"model_path": "{model_path}", "error": "{e}", "action": "security_validation_error"')
            return False
    
    def _validate_loaded_model(self, model, model_name: str) -> bool:
        """Validate that loaded model has expected methods and attributes"""
        try:
            # Check for basic prediction capability
            if not hasattr(model, 'predict'):
                self.logger.error(f'"model": "{model_name}", "error": "no_predict_method", "action": "model_validation_failed"')
                return False
            
            # Check if predict method is callable
            if not callable(getattr(model, 'predict')):
                self.logger.error(f'"model": "{model_name}", "error": "predict_not_callable", "action": "model_validation_failed"')
                return False
            
            # For classification models, check predict_proba if available
            if hasattr(model, 'predict_proba') and not callable(getattr(model, 'predict_proba')):
                self.logger.warning(f'"model": "{model_name}", "warning": "predict_proba_not_callable"')
            
            return True
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "error": "{e}", "action": "model_validation_error"')
            return False
    
    def _determine_model_type(self, model) -> str:
        """Determine the type of the loaded model"""
        try:
            model_class = model.__class__.__name__
            
            if 'RandomForest' in model_class:
                return 'random_forest'
            elif 'GradientBoosting' in model_class or 'XGB' in model_class:
                return 'gradient_boosting'
            elif 'LogisticRegression' in model_class:
                return 'logistic_regression'
            elif 'SVM' in model_class or 'SVC' in model_class:
                return 'svm'
            elif 'Neural' in model_class or 'MLP' in model_class:
                return 'neural_network'
            elif 'LinearRegression' in model_class:
                return 'linear_regression'
            else:
                return 'unknown'
                
        except Exception:
            return 'unknown'
    
    def _find_model_path(self, model_name: str, symbol: str = None) -> Optional[str]:
        """Find the appropriate model file path"""
        # Try bank-specific model first if symbol provided
        if symbol and symbol in self.bank_models_dir:
            bank_specific_path = self.bank_models_dir[symbol] / f"{model_name}.pkl"
            if bank_specific_path.exists():
                return str(bank_specific_path)
        
        # Try general models directory
        general_path = self.models_dir / f"{model_name}.pkl"
        if general_path.exists():
            return str(general_path)
        
        # Check discovered models metadata
        for discovered_name, metadata in self.model_metadata.items():
            if model_name in discovered_name and (not symbol or metadata["symbol"] == symbol):
                return metadata["path"]
        
        return None
    
    async def predict(self, model_name: str, features: Dict[str, Any], symbol: str = None, return_confidence: bool = True):
        """Generate prediction using specified model with enhanced validation"""
        # Input validation
        if not model_name or not isinstance(model_name, str):
            return {"error": "Invalid model_name parameter", "model_name": model_name}
        
        if not features or not isinstance(features, dict):
            return {"error": "Invalid features parameter - must be non-empty dict", "model_name": model_name}
        
        # Sanitize inputs
        model_name = model_name.strip()
        if symbol:
            symbol = symbol.upper().strip() if isinstance(symbol, str) else None
        
        try:
            model_key = f"{model_name}_{symbol}" if symbol else model_name
            
            # Ensure model is loaded
            if model_key not in self.loaded_models:
                load_result = await self.load_model(model_name, symbol)
                if "error" in load_result:
                    return load_result
            
            model_data = self.loaded_models[model_key]
            model = model_data["model"]
            
            # Validate and prepare features
            try:
                processed_features = self._prepare_features(features, model_name)
                if not processed_features:
                    return {
                        "error": "Feature preparation failed - no valid features",
                        "model_name": model_name,
                        "symbol": symbol
                    }
            except Exception as e:
                return {
                    "error": f"Feature preparation error: {e}",
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            # Generate prediction with error handling and timeout
            prediction_start = datetime.now()
            
            try:
                # Validate feature array shape and values
                if not isinstance(processed_features, list) or not processed_features:
                    raise ValueError("Invalid processed features format")
                
                # Check for infinite or NaN values
                if any(not np.isfinite(f) for f in processed_features):
                    raise ValueError("Features contain infinite or NaN values")
                
                # Generate prediction with timeout protection
                prediction_future = asyncio.create_task(
                    asyncio.to_thread(self._safe_predict, model, processed_features)
                )
                
                try:
                    prediction_result = await asyncio.wait_for(prediction_future, timeout=10.0)
                except asyncio.TimeoutError:
                    prediction_future.cancel()
                    raise Exception("Prediction timeout - model took too long")
                
                prediction, confidence = prediction_result
                
            except Exception as pred_error:
                # Update error metrics
                self.model_performance[model_key]["error_count"] += 1
                self.logger.error(f'"model": "{model_key}", "error": "{pred_error}", "action": "prediction_execution_failed"')
                return {
                    "error": f"Prediction execution failed: {pred_error}",
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            prediction_time = (datetime.now() - prediction_start).total_seconds()
            
            # Validate prediction output
            try:
                if hasattr(prediction, 'item'):
                    prediction_value = float(prediction.item())
                elif isinstance(prediction, (int, float)):
                    prediction_value = float(prediction)
                elif isinstance(prediction, np.ndarray) and prediction.size == 1:
                    prediction_value = float(prediction.flat[0])
                else:
                    prediction_value = float(prediction)
                
                # Validate prediction is finite
                if not np.isfinite(prediction_value):
                    raise ValueError(f"Prediction is not finite: {prediction_value}")
                
            except (ValueError, TypeError) as e:
                return {
                    "error": f"Invalid prediction output: {e}",
                    "model_name": model_name,
                    "symbol": symbol
                }
            
            # Update model usage statistics
            model_data["prediction_count"] += 1
            model_data["last_used"] = datetime.now().isoformat()
            
            # Update performance tracking
            perf_data = self.model_performance[model_key]
            perf_data["predictions_made"] += 1
            perf_data["total_prediction_time"] += prediction_time
            
            # Update average confidence (rolling average)
            if return_confidence and isinstance(confidence, (int, float)):
                prev_avg = perf_data["average_confidence"]
                count = perf_data["predictions_made"]
                perf_data["average_confidence"] = (prev_avg * (count - 1) + confidence) / count
            
            result = {
                "model_name": model_name,
                "symbol": symbol,
                "prediction": round(prediction_value, 6),
                "features_count": len(processed_features),
                "prediction_time_ms": round(prediction_time * 1000, 2),
                "timestamp": datetime.now().isoformat(),
                "model_type": model_data.get("model_type", "unknown")
            }
            
            if return_confidence:
                confidence_value = float(confidence) if hasattr(confidence, 'item') else confidence
                if isinstance(confidence_value, (int, float)) and np.isfinite(confidence_value):
                    result["confidence"] = round(max(0.0, min(1.0, confidence_value)), 4)
                else:
                    result["confidence"] = 0.5  # Default moderate confidence
            
            self.logger.info(f'"model": "{model_key}", "prediction": {result["prediction"]}, "confidence": {result.get("confidence", "N/A")}, "time_ms": {result["prediction_time_ms"]}, "action": "prediction_generated"')
            
            return result
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "symbol": "{symbol}", "error": "{e}", "action": "prediction_failed"')
    def _safe_predict(self, model, processed_features):
        """Safely execute model prediction in thread"""
        try:
            if hasattr(model, 'predict_proba'):
                # Classification model with probabilities
                probabilities = model.predict_proba([processed_features])[0]
                prediction = model.predict([processed_features])[0]
                confidence = max(probabilities)
            else:
                # Regression model or simple classifier
                prediction = model.predict([processed_features])[0]
                confidence = self._calculate_confidence(processed_features, model, "unknown")
            
            return prediction, confidence
            
        except Exception as e:
            raise Exception(f"Model prediction failed: {e}")
    
    def _prepare_features(self, features: Dict[str, Any], model_name: str) -> List[float]:
        """Prepare and validate features for model input with enhanced validation"""
        try:
            # Determine expected feature schema based on model type
            if "technical" in model_name.lower():
                expected_features = self.feature_schemas["technical"]
            elif "sentiment" in model_name.lower():
                expected_features = self.feature_schemas["sentiment"]
            elif "volume" in model_name.lower():
                expected_features = self.feature_schemas["volume"]
            elif "market" in model_name.lower():
                expected_features = self.feature_schemas["market"]
            else:
                # Use all available features, but limit to reasonable number
                expected_features = list(features.keys())[:20]  # Limit to 20 features max
            
            # Extract features in expected order with validation
            processed_features = []
            missing_features = []
            
            for feature_name in expected_features:
                if feature_name in features:
                    value = features[feature_name]
                    
                    # Convert to float and handle missing/invalid values
                    try:
                        float_value = float(value)
                        
                        # Check for invalid values
                        if not np.isfinite(float_value):
                            self.logger.warning(f'"feature": "{feature_name}", "value": "{value}", "action": "infinite_value_replaced"')
                            float_value = 0.0
                        
                        # Apply reasonable bounds to prevent extreme values
                        if abs(float_value) > 1e6:  # Very large values
                            self.logger.warning(f'"feature": "{feature_name}", "value": "{value}", "action": "extreme_value_capped"')
                            float_value = np.sign(float_value) * 1e6
                        
                        processed_features.append(float_value)
                        
                    except (ValueError, TypeError, OverflowError):
                        self.logger.warning(f'"feature": "{feature_name}", "value": "{value}", "action": "invalid_value_replaced"')
                        processed_features.append(0.0)  # Default for missing/invalid values
                else:
                    missing_features.append(feature_name)
                    processed_features.append(0.0)  # Default for missing features
            
            # Log warnings for missing features
            if missing_features:
                self.logger.warning(f'"missing_features": {missing_features}, "model": "{model_name}", "action": "features_defaulted"')
            
            # Validate minimum feature count
            if len(processed_features) == 0:
                raise ValueError("No valid features processed")
            
            # Check for all-zero features (potential data quality issue)
            non_zero_count = sum(1 for f in processed_features if f != 0.0)
            if non_zero_count == 0:
                self.logger.warning(f'"model": "{model_name}", "warning": "all_features_zero", "action": "prediction_may_be_unreliable"')
            elif non_zero_count < len(processed_features) * 0.3:  # Less than 30% non-zero
                self.logger.warning(f'"model": "{model_name}", "warning": "many_zero_features", "non_zero_ratio": {non_zero_count / len(processed_features):.2f}')
            
            return processed_features
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "error": "{e}", "action": "feature_preparation_failed"')
            raise Exception(f"Feature preparation failed: {e}")
    
    def _calculate_confidence(self, features: List[float], model, model_name: str) -> float:
        """Calculate prediction confidence for non-probabilistic models with enhanced validation"""
        try:
            # Input validation
            if not features or not isinstance(features, list):
                return 0.1
            
            # Base confidence calculation
            feature_quality = 1.0
            
            # Penalize for zero/missing features with more nuanced approach
            zero_features = sum(1 for f in features if f == 0.0)
            if len(features) > 0:
                zero_ratio = zero_features / len(features)
                # Exponential penalty for high zero ratios
                feature_quality *= (1.0 - zero_ratio ** 0.5)
            
            # Penalize for extreme values that might indicate data quality issues
            extreme_features = sum(1 for f in features if abs(f) > 1000)
            if extreme_features > 0:
                feature_quality *= (1.0 - (extreme_features / len(features)) * 0.2)
            
            # For tree-based models, try to get feature importance
            if hasattr(model, 'feature_importances_'):
                try:
                    importances = model.feature_importances_
                    if len(importances) == len(features):
                        # Calculate weighted feature contribution
                        normalized_features = np.array(features)
                        
                        # Normalize features to prevent overflow
                        if np.any(normalized_features != 0):
                            max_val = np.max(np.abs(normalized_features))
                            if max_val > 0:
                                normalized_features = normalized_features / max_val
                        
                        # Weight confidence by feature importance and values
                        weighted_contribution = np.sum(np.abs(normalized_features) * importances)
                        
                        # Scale to reasonable confidence range
                        importance_confidence = min(1.0, weighted_contribution / 2.0)
                        feature_quality = (feature_quality + importance_confidence) / 2.0
                        
                except Exception as imp_error:
                    self.logger.warning(f'"model": "{model_name}", "error": "{imp_error}", "action": "importance_calculation_failed"')
            
            # For models with decision functions (like SVM), use decision function confidence
            if hasattr(model, 'decision_function'):
                try:
                    decision_score = abs(model.decision_function([features])[0])
                    # Convert decision score to confidence (higher absolute score = higher confidence)
                    decision_confidence = min(1.0, decision_score / 5.0)  # Scale appropriately
                    feature_quality = (feature_quality + decision_confidence) / 2.0
                except Exception as dec_error:
                    self.logger.warning(f'"model": "{model_name}", "error": "{dec_error}", "action": "decision_function_failed"')
            
            # Ensure confidence is within valid bounds
            final_confidence = max(0.05, min(1.0, feature_quality))
            
            return final_confidence
            
        except Exception as e:
            self.logger.warning(f'"model": "{model_name}", "error": "{e}", "action": "confidence_calculation_failed"')
            return 0.5  # Default moderate confidence on error
    
    async def get_ensemble_prediction(self, features: Dict[str, Any], symbol: str = None):
        """Generate ensemble prediction using multiple models with enhanced error handling"""
        # Input validation
        if not features or not isinstance(features, dict):
            return {"error": "Invalid features parameter - must be non-empty dict"}
        
        # Sanitize symbol
        if symbol:
            symbol = symbol.upper().strip() if isinstance(symbol, str) else None
        
        try:
            ensemble_models = []
            
            # Find available models for this symbol/general with more robust discovery
            available_model_types = self.model_types.copy()
            
            for model_name in available_model_types:
                # Try bank-specific model first if symbol provided
                if symbol:
                    bank_model_key = f"{symbol}_{model_name}"
                    if (bank_model_key in self.model_metadata or 
                        self._find_model_path(model_name, symbol)):
                        ensemble_models.append((model_name, symbol))
                
                # Add general model if available
                if self._find_model_path(model_name):
                    ensemble_models.append((model_name, None))
            
            # Remove duplicates while preserving order (prefer bank-specific)
            seen = set()
            unique_models = []
            for model_name, model_symbol in ensemble_models:
                key = model_name  # Use model_name as key to avoid duplicates
                if key not in seen:
                    seen.add(key)
                    unique_models.append((model_name, model_symbol))
            
            ensemble_models = unique_models[:5]  # Limit to 5 models for performance
            
            if not ensemble_models:
                return {
                    "error": "No models available for ensemble prediction",
                    "symbol": symbol,
                    "available_models": list(self.model_metadata.keys())
                }
            
            # Generate predictions from all available models with error isolation
            predictions = []
            confidences = []
            model_results = {}
            successful_predictions = 0
            failed_predictions = 0
            
            for model_name, model_symbol in ensemble_models:
                try:
                    # Add timeout for individual model predictions
                    result = await asyncio.wait_for(
                        self.predict(model_name, features, model_symbol, return_confidence=True),
                        timeout=15.0
                    )
                    
                    if "error" not in result:
                        pred = result["prediction"]
                        conf = result.get("confidence", 0.5)
                        
                        # Validate prediction values
                        if isinstance(pred, (int, float)) and np.isfinite(pred):
                            if isinstance(conf, (int, float)) and 0 <= conf <= 1:
                                predictions.append(float(pred))
                                confidences.append(float(conf))
                                successful_predictions += 1
                                
                                model_key = f"{model_name}_{model_symbol}" if model_symbol else model_name
                                model_results[model_key] = {
                                    "prediction": round(float(pred), 6),
                                    "confidence": round(float(conf), 4),
                                    "prediction_time_ms": result.get("prediction_time_ms", 0)
                                }
                            else:
                                self.logger.warning(f'"model": "{model_name}", "confidence": "{conf}", "action": "invalid_confidence_skipped"')
                                failed_predictions += 1
                        else:
                            self.logger.warning(f'"model": "{model_name}", "prediction": "{pred}", "action": "invalid_prediction_skipped"')
                            failed_predictions += 1
                    else:
                        self.logger.warning(f'"model": "{model_name}", "error": "{result.get("error")}", "action": "model_prediction_failed"')
                        failed_predictions += 1
                        
                except asyncio.TimeoutError:
                    self.logger.error(f'"model": "{model_name}", "symbol": "{model_symbol}", "error": "prediction_timeout", "action": "ensemble_model_timeout"')
                    failed_predictions += 1
                except Exception as e:
                    self.logger.error(f'"model": "{model_name}", "symbol": "{model_symbol}", "error": "{e}", "action": "ensemble_model_failed"')
                    failed_predictions += 1
            
            if not predictions:
                return {
                    "error": "No successful predictions from ensemble models",
                    "symbol": symbol,
                    "attempted_models": len(ensemble_models),
                    "failed_predictions": failed_predictions
                }
            
            # Calculate ensemble prediction using confidence-weighted average
            try:
                total_confidence = sum(confidences)
                
                if total_confidence > 0:
                    total_weighted_prediction = sum(p * c for p, c in zip(predictions, confidences))
                    ensemble_prediction = total_weighted_prediction / total_confidence
                    ensemble_confidence = total_confidence / len(predictions)
                else:
                    # Fallback to simple average if confidence weighting fails
                    ensemble_prediction = sum(predictions) / len(predictions)
                    ensemble_confidence = 0.5
                
                # Calculate prediction variance for uncertainty estimation
                prediction_variance = float(np.var(predictions)) if len(predictions) > 1 else 0.0
                prediction_std = float(np.std(predictions)) if len(predictions) > 1 else 0.0
                
                # Calculate prediction range
                min_prediction = float(min(predictions))
                max_prediction = float(max(predictions))
                
                result = {
                    "ensemble_prediction": round(float(ensemble_prediction), 6),
                    "ensemble_confidence": round(float(ensemble_confidence), 4),
                    "models_used": successful_predictions,
                    "models_attempted": len(ensemble_models),
                    "model_results": model_results,
                    "prediction_statistics": {
                        "variance": round(prediction_variance, 6),
                        "std_deviation": round(prediction_std, 6),
                        "min_prediction": round(min_prediction, 6),
                        "max_prediction": round(max_prediction, 6),
                        "prediction_range": round(max_prediction - min_prediction, 6)
                    },
                    "quality_metrics": {
                        "success_rate": round(successful_predictions / len(ensemble_models), 3),
                        "confidence_spread": round(max(confidences) - min(confidences), 3) if confidences else 0.0,
                        "prediction_consensus": "high" if prediction_std < 0.1 else "medium" if prediction_std < 0.3 else "low"
                    },
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat()
                }
                
                self.logger.info(f'"symbol": "{symbol}", "ensemble_prediction": {result["ensemble_prediction"]}, "models_used": {successful_predictions}, "consensus": "{result["quality_metrics"]["prediction_consensus"]}", "action": "ensemble_prediction_generated"')
                
                return result
                
            except Exception as calc_error:
                self.logger.error(f'"error": "{calc_error}", "action": "ensemble_calculation_failed"')
                return {
                    "error": f"Ensemble calculation failed: {calc_error}",
                    "symbol": symbol,
                    "raw_predictions": predictions,
                    "raw_confidences": confidences
                }
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "ensemble_prediction_failed"')
            return {"error": str(e), "symbol": symbol}
    
    async def list_available_models(self):
        """List all available models"""
        # Refresh model discovery
        await self._discover_available_models()
        
        # Organize models by type and symbol
        organized_models = {
            "general_models": {},
            "bank_specific_models": {},
            "loaded_models": list(self.loaded_models.keys()),
            "total_models": len(self.model_metadata)
        }
        
        for model_name, metadata in self.model_metadata.items():
            if metadata["type"] == "bank_specific":
                symbol = metadata["symbol"]
                if symbol not in organized_models["bank_specific_models"]:
                    organized_models["bank_specific_models"][symbol] = []
                organized_models["bank_specific_models"][symbol].append({
                    "name": model_name,
                    "size_kb": round(metadata["size"] / 1024, 2),
                    "modified": metadata["modified"]
                })
            else:
                organized_models["general_models"][model_name] = {
                    "size_kb": round(metadata["size"] / 1024, 2),
                    "modified": metadata["modified"]
                }
        
        return organized_models
    
    async def get_model_performance(self, model_name: str = None):
        """Get performance metrics for models"""
        if model_name:
            return self.model_performance.get(model_name, {"error": "Model performance data not found"})
        else:
            return {
                "all_models": self.model_performance,
                "summary": {
                    "total_models_tracked": len(self.model_performance),
                    "total_predictions": sum(perf["predictions_made"] for perf in self.model_performance.values()),
                    "loaded_models": len(self.loaded_models)
                }
            }
    
    async def unload_model(self, model_name: str, symbol: str = None):
        """Unload model from memory"""
        model_key = f"{model_name}_{symbol}" if symbol else model_name
        
        if model_key in self.loaded_models:
            del self.loaded_models[model_key]
            self.logger.info(f'"model": "{model_key}", "action": "model_unloaded"')
            return {"status": "unloaded", "model": model_key}
        else:
            return {"error": "Model not loaded", "model": model_key}
    
    async def get_feature_importance(self, model_name: str, symbol: str = None):
        """Get feature importance from loaded model"""
        try:
            model_key = f"{model_name}_{symbol}" if symbol else model_name
            
            if model_key not in self.loaded_models:
                load_result = await self.load_model(model_name, symbol)
                if "error" in load_result:
                    return load_result
            
            model = self.loaded_models[model_key]["model"]
            
            if hasattr(model, 'feature_importances_'):
                # Get feature names based on model type
                if "technical" in model_name.lower():
                    feature_names = self.feature_schemas["technical"]
                elif "sentiment" in model_name.lower():
                    feature_names = self.feature_schemas["sentiment"]
                elif "volume" in model_name.lower():
                    feature_names = self.feature_schemas["volume"]
                else:
                    feature_names = [f"feature_{i}" for i in range(len(model.feature_importances_))]
                
                # Create feature importance mapping
                importances = dict(zip(feature_names, model.feature_importances_.tolist()))
                
                # Sort by importance
                sorted_importances = dict(sorted(importances.items(), key=lambda x: x[1], reverse=True))
                
                return {
                    "model": model_key,
                    "feature_importances": sorted_importances,
                    "total_features": len(feature_names)
                }
            else:
                return {"error": "Model does not support feature importance", "model": model_key}
                
        except Exception as e:
            return {"error": str(e), "model": model_key}
    
    async def validate_features(self, features: Dict[str, Any], model_type: str = "general"):
        """Validate features for model compatibility"""
        try:
            validation_result = {
                "valid": True,
                "missing_features": [],
                "invalid_features": [],
                "feature_count": len(features),
                "warnings": []
            }
            
            # Get expected schema based on model type
            if model_type in self.feature_schemas:
                expected_features = self.feature_schemas[model_type]
                
                # Check for missing features
                for expected in expected_features:
                    if expected not in features:
                        validation_result["missing_features"].append(expected)
                        validation_result["valid"] = False
            
            # Check for invalid feature values
            for feature_name, value in features.items():
                try:
                    float(value)
                except (ValueError, TypeError):
                    validation_result["invalid_features"].append(feature_name)
                    validation_result["valid"] = False
            
            # Add warnings
            if len(features) < 3:
                validation_result["warnings"].append("Low number of features may affect prediction quality")
            
            zero_count = sum(1 for v in features.values() if v == 0)
            if zero_count > len(features) * 0.5:
                validation_result["warnings"].append("High number of zero values detected")
            
            return validation_result
            
        except Exception as e:
            return {"error": str(e), "valid": False}
    
    async def health_check(self):
        """Enhanced health check with ML model service metrics and configuration validation"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        ml_health = {
            **base_health,
            "loaded_models": len(self.loaded_models),
            "available_models": len(self.model_metadata),
            "total_predictions": sum(perf["predictions_made"] for perf in self.model_performance.values()),
            "model_directories_accessible": self._check_model_directories(),
            "settings_integration": SETTINGS_AVAILABLE,
            "bank_symbols_count": len(self.bank_symbols),
            "supported_model_types": len(self.model_types),
            "training_config": {
                "auto_retrain": self.training_config.get('auto_retrain', False),
                "retrain_frequency_days": self.training_config.get('retrain_frequency_days', 7),
                "min_samples": self.training_config.get('min_samples', 100)
            }
        }
        
        # Validate configuration integrity
        config_issues = []
        
        # Check model configuration
        for model_type, config in self.model_config.items():
            if not isinstance(config, dict):
                config_issues.append(f"Invalid config for {model_type}")
            elif config.get('enabled') and not self._validate_model_config(model_type, config):
                config_issues.append(f"Configuration validation failed for {model_type}")
        
        # Check model directories
        missing_dirs = []
        for symbol, model_dir in self.bank_models_dir.items():
            if not model_dir.exists():
                missing_dirs.append(f"{symbol}: {model_dir}")
        
        if missing_dirs:
            config_issues.append(f"Missing model directories: {missing_dirs}")
        
        # Check models directory accessibility
        if not self.models_dir.exists():
            config_issues.append(f"Main models directory not accessible: {self.models_dir}")
        
        ml_health["configuration_issues"] = config_issues
        ml_health["configuration_valid"] = len(config_issues) == 0
        
        # Check model loading capability
        try:
            # Try to find at least one model
            if self.model_metadata:
                ml_health["model_discovery"] = "ok"
            else:
                ml_health["model_discovery"] = "no_models_found"
                if ml_health["status"] == "healthy":
                    ml_health["status"] = "degraded"
        except Exception as e:
            ml_health["model_discovery"] = f"failed: {e}"
            ml_health["status"] = "unhealthy"
        
        # Performance metrics
        if self.model_performance:
            total_predictions = sum(perf["predictions_made"] for perf in self.model_performance.values())
            total_errors = sum(perf.get("error_count", 0) for perf in self.model_performance.values())
            
            if total_predictions > 0:
                error_rate = (total_errors / total_predictions) * 100
                ml_health["error_rate_percent"] = round(error_rate, 2)
                
                if error_rate > 20:  # 20% error rate threshold
                    ml_health["status"] = "degraded"
                    ml_health["warning"] = f"High error rate: {error_rate:.1f}%"
        
        # Check retrain schedule
        if self.training_config.get('auto_retrain', False):
            try:
                retrain_candidates = await self._check_models_for_retraining()
                ml_health["models_needing_retrain"] = len(retrain_candidates)
                
                if len(retrain_candidates) > len(self.model_metadata) * 0.5:  # More than 50% need retraining
                    ml_health["warning"] = f"{len(retrain_candidates)} models may need retraining"
            except Exception as e:
                ml_health["retrain_check_error"] = str(e)
        
        return ml_health
    
    def _check_model_directories(self):
        """Check if model directories are accessible"""
        try:
            if not self.models_dir.exists():
                return False
            
            accessible_dirs = 0
            total_dirs = len(self.bank_models_dir)
            
            for model_dir in self.bank_models_dir.values():
                if model_dir.exists() and os.access(model_dir, os.R_OK):
                    accessible_dirs += 1
            
            # Return True if main dir exists and at least 70% of bank dirs are accessible
            return accessible_dirs >= (total_dirs * 0.7)
            
        except Exception:
            return False
    
    def _validate_model_config(self, model_type: str, config: Dict) -> bool:
        """Validate model configuration parameters"""
        try:
            if model_type == "sentiment_ensemble":
                required_fields = ['models', 'weights']
                if not all(field in config for field in required_fields):
                    return False
                
                models = config.get('models', [])
                weights = config.get('weights', [])
                
                if len(models) != len(weights):
                    return False
                
                if abs(sum(weights) - 1.0) > 0.01:  # Weights should sum to 1
                    return False
            
            elif model_type == "price_prediction":
                required_fields = ['lookback_periods', 'prediction_horizon']
                if not all(field in config for field in required_fields):
                    return False
                
                lookback_periods = config.get('lookback_periods', [])
                if not isinstance(lookback_periods, list) or not lookback_periods:
                    return False
            
            elif model_type == "risk_assessment":
                required_fields = ['volatility_window']
                if not all(field in config for field in required_fields):
                    return False
                
                volatility_window = config.get('volatility_window', 0)
                if not isinstance(volatility_window, int) or volatility_window <= 0:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model config validation error for {model_type}: {e}")
            return False

async def main():
    service = MLModelService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
