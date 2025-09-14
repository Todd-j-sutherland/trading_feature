#!/usr/bin/env python3
"""
Enhanced ML Model Service with Complete Configuration Integration
Integrates settings.py ML_CONFIG and ml_config.yaml for comprehensive model management
"""
import asyncio
import pickle
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Union
import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.base_service import BaseService

class EnhancedMLModelService(BaseService):
    """Enhanced ML model service with comprehensive configuration integration"""

    def __init__(self):
        super().__init__("enhanced-ml-model")
        
        # Configuration loaded from enhanced config service
        self.config_loaded = False
        self.ml_config = {}
        self.bank_profiles = {}
        self.enhanced_ml_config = {}
        
        # Model management
        self.active_models = {}
        self.model_registry = {}
        self.model_performance = {}
        self.training_history = {}
        
        # Initialize with fallback configuration
        self._initialize_fallback_config()
        
        # Register methods
        self.register_handler("load_model", self.load_model)
        self.register_handler("predict", self.predict)
        self.register_handler("batch_predict", self.batch_predict)
        self.register_handler("train_model", self.train_model)
        self.register_handler("evaluate_model", self.evaluate_model)
        self.register_handler("get_model_info", self.get_model_info)
        self.register_handler("list_models", self.list_models)
        self.register_handler("get_training_config", self.get_training_config)
        self.register_handler("get_feature_config", self.get_feature_config)
        self.register_handler("update_model_performance", self.update_model_performance)
        self.register_handler("get_best_model", self.get_best_model)
        self.register_handler("model_health_check", self.model_health_check)

    async def _load_enhanced_config(self):
        """Load configuration from enhanced configuration service"""
        if self.config_loaded:
            return
            
        try:
            # Load enhanced ML configuration
            enhanced_ml_config = await self.call_service("enhanced-config", "get_ml_config")
            if enhanced_ml_config:
                self.enhanced_ml_config = enhanced_ml_config
                self.ml_config = enhanced_ml_config  # Use enhanced as primary
                
            # Load bank profiles for bank-specific models
            bank_profiles = await self.call_service("enhanced-config", "get_bank_profiles")
            if bank_profiles:
                self.bank_profiles = bank_profiles
                
            self.config_loaded = True
            self.logger.info("Loaded enhanced ML configuration from config service")
            
            # Initialize model registry with enhanced configuration
            await self._initialize_model_registry()
            
        except Exception as e:
            self.logger.warning(f"Could not load from enhanced config service: {e}")
            # Keep using fallback configuration

    def _initialize_fallback_config(self):
        """Initialize fallback configuration"""
        self.ml_config = {
            "models": {
                "random_forest": {"enabled": True, "n_estimators": 100, "random_state": 42},
                "gradient_boosting": {"enabled": True, "n_estimators": 100, "learning_rate": 0.1},
                "svm": {"enabled": False},
                "neural_network": {"enabled": True, "hidden_layer_sizes": [100, 50]}
            },
            "training": {
                "test_size": 0.2,
                "random_state": 42,
                "cv_folds": 5,
                "scoring": "accuracy"
            },
            "feature_engineering": {
                "technical_features": ["rsi", "macd", "bollinger_bands", "moving_averages"],
                "sentiment_features": ["sentiment_score", "news_volume", "news_quality"],
                "market_features": ["market_sentiment", "volume_ratio", "volatility"]
            },
            "performance_thresholds": {
                "minimum_accuracy": 0.65,
                "minimum_precision": 0.60,
                "minimum_recall": 0.60,
                "minimum_f1": 0.60
            }
        }
        
        self.bank_profiles = {
            "CBA.AX": {"name": "Commonwealth Bank", "sector": "Banking"},
            "ANZ.AX": {"name": "ANZ Banking Group", "sector": "Banking"},
            "NAB.AX": {"name": "National Australia Bank", "sector": "Banking"},
            "WBC.AX": {"name": "Westpac Banking Corporation", "sector": "Banking"}
        }

    async def _initialize_model_registry(self):
        """Initialize model registry with available models"""
        models_dir = Path("models")
        
        if models_dir.exists():
            # Scan for existing models
            for model_file in models_dir.glob("**/*.pkl"):
                try:
                    # Extract model info from filename/path
                    model_path = str(model_file)
                    model_name = model_file.stem
                    
                    # Check if it's a bank-specific model
                    bank_symbol = None
                    for symbol in self.bank_profiles.keys():
                        if symbol.replace(".AX", "") in model_path:
                            bank_symbol = symbol
                            break
                    
                    self.model_registry[model_name] = {
                        "path": model_path,
                        "bank_symbol": bank_symbol,
                        "loaded": False,
                        "last_modified": model_file.stat().st_mtime,
                        "model_type": self._infer_model_type(model_name)
                    }
                    
                except Exception as e:
                    self.logger.warning(f"Error registering model {model_file}: {e}")
        
        self.logger.info(f"Registered {len(self.model_registry)} models")

    def _infer_model_type(self, model_name: str) -> str:
        """Infer model type from filename"""
        model_name_lower = model_name.lower()
        
        if "random_forest" in model_name_lower or "rf" in model_name_lower:
            return "random_forest"
        elif "gradient_boost" in model_name_lower or "gb" in model_name_lower or "xgb" in model_name_lower:
            return "gradient_boosting"
        elif "svm" in model_name_lower:
            return "svm"
        elif "neural" in model_name_lower or "nn" in model_name_lower or "mlp" in model_name_lower:
            return "neural_network"
        elif "logistic" in model_name_lower:
            return "logistic_regression"
        else:
            return "unknown"

    async def load_model(self, model_name: str, symbol: str = None, force_reload: bool = False) -> Dict[str, Any]:
        """Load a specific model"""
        # Load enhanced configuration if not already loaded
        if not self.config_loaded:
            await self._load_enhanced_config()
        
        try:
            # Create model key
            model_key = f"{model_name}_{symbol}" if symbol else model_name
            
            # Check if already loaded
            if not force_reload and model_key in self.active_models:
                return {
                    "model_key": model_key,
                    "status": "already_loaded",
                    "symbol": symbol,
                    "loaded_at": self.active_models[model_key]["loaded_at"]
                }
            
            # Find model file
            model_path = await self._find_model_path(model_name, symbol)
            if not model_path:
                return {"error": f"Model not found: {model_name} for symbol {symbol}"}
            
            # Load model
            if model_path.endswith('.pkl'):
                with open(model_path, 'rb') as f:
                    model = pickle.load(f)
            elif model_path.endswith('.joblib'):
                model = joblib.load(model_path)
            else:
                return {"error": f"Unsupported model format: {model_path}"}
            
            # Store in active models
            self.active_models[model_key] = {
                "model": model,
                "symbol": symbol,
                "model_name": model_name,
                "model_path": model_path,
                "loaded_at": datetime.now().isoformat(),
                "model_type": self._infer_model_type(model_name),
                "prediction_count": 0
            }
            
            # Load model-specific configuration
            model_config = self._get_model_config(model_name, symbol)
            
            return {
                "model_key": model_key,
                "status": "loaded",
                "symbol": symbol,
                "model_path": model_path,
                "model_type": self.active_models[model_key]["model_type"],
                "configuration": model_config,
                "loaded_at": self.active_models[model_key]["loaded_at"]
            }
            
        except Exception as e:
            self.logger.error(f"Error loading model {model_name} for {symbol}: {e}")
            return {"error": str(e)}

    async def _find_model_path(self, model_name: str, symbol: str = None) -> Optional[str]:
        """Find the path to a model file"""
        possible_paths = []
        
        if symbol:
            # Look for bank-specific models first
            bank_code = symbol.replace(".AX", "")
            possible_paths.extend([
                f"models/{symbol}/{model_name}.pkl",
                f"models/{bank_code}/{model_name}.pkl",
                f"models/{model_name}_{symbol}.pkl",
                f"models/{model_name}_{bank_code}.pkl"
            ])
        
        # Look for general models
        possible_paths.extend([
            f"models/{model_name}.pkl",
            f"models/general/{model_name}.pkl",
            f"models/{model_name}.joblib"
        ])
        
        # Check which path exists
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None

    def _get_model_config(self, model_name: str, symbol: str = None) -> Dict[str, Any]:
        """Get configuration for a specific model"""
        model_type = self._infer_model_type(model_name)
        
        # Get general model configuration
        general_config = self.ml_config.get("models", {}).get(model_type, {})
        
        # Get bank-specific configuration if available
        bank_config = {}
        if symbol and symbol in self.bank_profiles:
            bank_profile = self.bank_profiles[symbol]
            bank_config = bank_profile.get("ml_preferences", {})
        
        # Get enhanced model configuration if available
        enhanced_config = {}
        if "enhanced_models" in self.enhanced_ml_config:
            enhanced_config = self.enhanced_ml_config["enhanced_models"].get(model_type, {})
        
        # Merge configurations
        merged_config = {**general_config, **enhanced_config, **bank_config}
        
        return merged_config

    async def predict(self, model_name: str, features: Dict[str, Any], symbol: str = None) -> Dict[str, Any]:
        """Make prediction using specified model"""
        try:
            model_key = f"{model_name}_{symbol}" if symbol else model_name
            
            # Load model if not already loaded
            if model_key not in self.active_models:
                load_result = await self.load_model(model_name, symbol)
                if "error" in load_result:
                    return load_result
            
            model_data = self.active_models[model_key]
            model = model_data["model"]
            
            # Prepare features according to model requirements
            feature_vector = await self._prepare_features(features, model_name, symbol)
            
            # Make prediction
            if hasattr(model, 'predict_proba'):
                # Classification with probabilities
                prediction_proba = model.predict_proba([feature_vector])
                prediction = model.predict([feature_vector])
                
                result = {
                    "prediction": prediction.tolist()[0],
                    "probabilities": prediction_proba.tolist()[0],
                    "confidence": float(max(prediction_proba[0]))
                }
            else:
                # Simple prediction
                prediction = model.predict([feature_vector])
                result = {
                    "prediction": prediction.tolist()[0],
                    "confidence": 0.8  # Default confidence for non-probabilistic models
                }
            
            # Add metadata
            result.update({
                "model_name": model_name,
                "symbol": symbol,
                "model_type": model_data["model_type"],
                "timestamp": datetime.now().isoformat(),
                "features_used": list(features.keys())
            })
            
            # Update prediction count
            model_data["prediction_count"] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error making prediction with {model_name} for {symbol}: {e}")
            return {"error": str(e)}

    async def batch_predict(self, model_name: str, features_list: List[Dict[str, Any]], symbol: str = None) -> Dict[str, Any]:
        """Make batch predictions"""
        try:
            predictions = []
            errors = []
            
            for i, features in enumerate(features_list):
                result = await self.predict(model_name, features, symbol)
                if "error" in result:
                    errors.append({"index": i, "error": result["error"]})
                else:
                    predictions.append(result)
            
            return {
                "predictions": predictions,
                "total_predictions": len(predictions),
                "total_errors": len(errors),
                "errors": errors,
                "success_rate": len(predictions) / len(features_list) if features_list else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in batch prediction: {e}")
            return {"error": str(e)}

    async def _prepare_features(self, features: Dict[str, Any], model_name: str, symbol: str = None) -> List[float]:
        """Prepare features according to model requirements"""
        # Get feature engineering configuration
        feature_config = self.ml_config.get("feature_engineering", {})
        
        # Define expected features based on configuration
        expected_features = []
        
        # Technical features
        technical_features = feature_config.get("technical_features", [])
        for tech_feature in technical_features:
            if tech_feature == "rsi":
                expected_features.append(features.get("rsi", 50.0))
            elif tech_feature == "macd":
                macd_data = features.get("macd", {})
                expected_features.extend([
                    macd_data.get("line", 0.0),
                    macd_data.get("signal", 0.0),
                    macd_data.get("histogram", 0.0)
                ])
            elif tech_feature == "bollinger_bands":
                bb_data = features.get("bollinger_bands", {})
                # Use position relative to bands
                current_price = features.get("current_price", 0.0)
                bb_middle = bb_data.get("middle", current_price)
                bb_upper = bb_data.get("upper", current_price * 1.02)
                bb_lower = bb_data.get("lower", current_price * 0.98)
                
                # Calculate relative position (0-1 scale)
                if bb_upper != bb_lower:
                    bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
                else:
                    bb_position = 0.5
                expected_features.append(bb_position)
            elif tech_feature == "moving_averages":
                ma_data = features.get("moving_averages", {})
                current_price = features.get("current_price", 0.0)
                sma_20 = ma_data.get("sma_20", current_price)
                sma_50 = ma_data.get("sma_50", current_price)
                
                # Price relative to moving averages
                expected_features.extend([
                    current_price / sma_20 if sma_20 > 0 else 1.0,
                    current_price / sma_50 if sma_50 > 0 else 1.0,
                    sma_20 / sma_50 if sma_50 > 0 else 1.0
                ])
        
        # Sentiment features
        sentiment_features = feature_config.get("sentiment_features", [])
        for sent_feature in sentiment_features:
            if sent_feature == "sentiment_score":
                expected_features.append(features.get("sentiment_score", 0.0))
            elif sent_feature == "news_volume":
                expected_features.append(features.get("news_volume", 0.0))
            elif sent_feature == "news_quality":
                expected_features.append(features.get("news_quality_score", 0.5))
        
        # Market features
        market_features = feature_config.get("market_features", [])
        for market_feature in market_features:
            if market_feature == "market_sentiment":
                # Convert market sentiment to numeric
                market_sentiment = features.get("market_sentiment", "NEUTRAL")
                sentiment_map = {"BEARISH": -1.0, "NEUTRAL": 0.0, "BULLISH": 1.0}
                expected_features.append(sentiment_map.get(market_sentiment, 0.0))
            elif market_feature == "volume_ratio":
                expected_features.append(features.get("volume_ratio", 1.0))
            elif market_feature == "volatility":
                expected_features.append(features.get("daily_volatility", 0.02))
        
        # Add basic price features if not already included
        if "price_change_percent" not in str(expected_features):
            expected_features.append(features.get("price_change_percent", 0.0))
        
        return expected_features

    async def get_training_config(self) -> Dict[str, Any]:
        """Get training configuration"""
        # Load enhanced configuration if not already loaded
        if not self.config_loaded:
            await self._load_enhanced_config()
        
        training_config = self.ml_config.get("training", {})
        
        # Add enhanced training configuration if available
        if "training" in self.enhanced_ml_config:
            enhanced_training = self.enhanced_ml_config["training"]
            training_config = {**training_config, **enhanced_training}
        
        return training_config

    async def get_feature_config(self) -> Dict[str, Any]:
        """Get feature engineering configuration"""
        # Load enhanced configuration if not already loaded
        if not self.config_loaded:
            await self._load_enhanced_config()
        
        feature_config = self.ml_config.get("feature_engineering", {})
        
        # Add enhanced feature configuration if available
        if "feature_engineering" in self.enhanced_ml_config:
            enhanced_features = self.enhanced_ml_config["feature_engineering"]
            feature_config = {**feature_config, **enhanced_features}
        
        return feature_config

    async def train_model(self, model_type: str, training_data: Dict[str, Any], symbol: str = None) -> Dict[str, Any]:
        """Train a new model (placeholder for future implementation)"""
        return {
            "status": "not_implemented",
            "message": "Model training will be implemented in future version",
            "model_type": model_type,
            "symbol": symbol
        }

    async def evaluate_model(self, model_name: str, test_data: Dict[str, Any], symbol: str = None) -> Dict[str, Any]:
        """Evaluate model performance (placeholder for future implementation)"""
        return {
            "status": "not_implemented",
            "message": "Model evaluation will be implemented in future version",
            "model_name": model_name,
            "symbol": symbol
        }

    async def get_model_info(self, model_name: str, symbol: str = None) -> Dict[str, Any]:
        """Get information about a specific model"""
        model_key = f"{model_name}_{symbol}" if symbol else model_name
        
        if model_key in self.active_models:
            model_data = self.active_models[model_key]
            return {
                "model_key": model_key,
                "status": "loaded",
                "model_type": model_data["model_type"],
                "symbol": symbol,
                "loaded_at": model_data["loaded_at"],
                "prediction_count": model_data["prediction_count"],
                "model_path": model_data["model_path"],
                "configuration": self._get_model_config(model_name, symbol)
            }
        elif model_name in self.model_registry:
            registry_data = self.model_registry[model_name]
            return {
                "model_key": model_key,
                "status": "registered_not_loaded",
                "model_type": registry_data["model_type"],
                "symbol": registry_data["bank_symbol"],
                "model_path": registry_data["path"],
                "last_modified": registry_data["last_modified"]
            }
        else:
            return {"error": f"Model not found: {model_name}"}

    async def list_models(self) -> Dict[str, Any]:
        """List all available models"""
        return {
            "active_models": list(self.active_models.keys()),
            "registered_models": list(self.model_registry.keys()),
            "model_types_supported": list(self.ml_config.get("models", {}).keys()),
            "total_active": len(self.active_models),
            "total_registered": len(self.model_registry)
        }

    async def update_model_performance(self, model_name: str, performance_metrics: Dict[str, float], symbol: str = None) -> Dict[str, Any]:
        """Update model performance metrics"""
        model_key = f"{model_name}_{symbol}" if symbol else model_name
        
        self.model_performance[model_key] = {
            **performance_metrics,
            "updated_at": datetime.now().isoformat(),
            "symbol": symbol
        }
        
        return {
            "status": "updated",
            "model_key": model_key,
            "performance_metrics": performance_metrics
        }

    async def get_best_model(self, symbol: str = None, metric: str = "accuracy") -> Dict[str, Any]:
        """Get the best performing model for a symbol"""
        if not self.model_performance:
            return {"error": "No performance data available"}
        
        # Filter by symbol if specified
        candidates = {}
        for model_key, perf_data in self.model_performance.items():
            if symbol is None or perf_data.get("symbol") == symbol:
                if metric in perf_data:
                    candidates[model_key] = perf_data[metric]
        
        if not candidates:
            return {"error": f"No models found for symbol {symbol} with metric {metric}"}
        
        # Find best model
        best_model_key = max(candidates.keys(), key=lambda k: candidates[k])
        best_score = candidates[best_model_key]
        
        return {
            "best_model": best_model_key,
            "best_score": best_score,
            "metric": metric,
            "symbol": symbol,
            "all_candidates": candidates
        }

    async def model_health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for ML models"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "config_loaded": self.config_loaded,
            "active_models_count": len(self.active_models),
            "registered_models_count": len(self.model_registry),
            "models_status": {},
            "performance_data_available": len(self.model_performance),
            "issues": []
        }
        
        # Check each active model
        for model_key, model_data in self.active_models.items():
            try:
                model = model_data["model"]
                
                # Basic health check - try a dummy prediction
                dummy_features = [0.0] * 10  # Assume 10 features
                
                if hasattr(model, 'predict'):
                    test_prediction = model.predict([dummy_features])
                    model_status = "healthy"
                else:
                    model_status = "no_predict_method"
                    health_status["issues"].append(f"Model {model_key} has no predict method")
                
            except Exception as e:
                model_status = f"error: {str(e)}"
                health_status["issues"].append(f"Model {model_key} failed health check: {e}")
            
            health_status["models_status"][model_key] = model_status
        
        # Check configuration completeness
        required_config_sections = ["models", "training", "feature_engineering"]
        for section in required_config_sections:
            if section not in self.ml_config:
                health_status["issues"].append(f"Missing configuration section: {section}")
        
        # Overall health status
        if not health_status["issues"]:
            health_status["overall_status"] = "healthy"
        elif len(health_status["issues"]) <= 2:
            health_status["overall_status"] = "degraded"
        else:
            health_status["overall_status"] = "unhealthy"
        
        return health_status

    async def health_check(self):
        """Enhanced health check with ML model specific metrics"""
        base_health = await super().health_check()
        model_health = await self.model_health_check()
        
        enhanced_health = {
            **base_health,
            "ml_specific": model_health,
            "config_integration": {
                "enhanced_config_loaded": self.config_loaded,
                "ml_config_sections": len(self.ml_config),
                "bank_profiles_loaded": len(self.bank_profiles),
                "enhanced_ml_config_available": bool(self.enhanced_ml_config)
            }
        }
        
        return enhanced_health

async def main():
    service = EnhancedMLModelService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
