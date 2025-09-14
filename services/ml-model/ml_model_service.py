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

class MLModelService(BaseService):
    """Machine Learning model management and prediction service"""
    
    def __init__(self):
        super().__init__("ml-model")
        
        # Model management
        self.loaded_models = {}
        self.model_metadata = {}
        self.model_performance = {}
        
        # Model directories
        self.models_dir = Path("models")
        self.bank_models_dir = {
            "CBA.AX": Path("models/CBA.AX"),
            "ANZ.AX": Path("models/ANZ.AX"), 
            "NAB.AX": Path("models/NAB.AX"),
            "WBC.AX": Path("models/WBC.AX")
        }
        
        # Supported model types
        self.model_types = [
            "ensemble_predictor",
            "technical_analyzer", 
            "sentiment_model",
            "volume_predictor",
            "risk_model"
        ]
        
        # Feature definitions for different model types
        self.feature_schemas = {
            "technical": ["price", "rsi", "macd", "bollinger_upper", "bollinger_lower", "volume"],
            "sentiment": ["sentiment_score", "news_confidence", "news_volume"],
            "volume": ["volume_ratio", "volume_trend", "volume_ma"],
            "market": ["market_sentiment", "sector_performance", "volatility_index"]
        }
        
        # Register methods
        self.register_handler("load_model", self.load_model)
        self.register_handler("predict", self.predict)
        self.register_handler("get_ensemble_prediction", self.get_ensemble_prediction)
        self.register_handler("list_available_models", self.list_available_models)
        self.register_handler("get_model_performance", self.get_model_performance)
        self.register_handler("unload_model", self.unload_model)
        self.register_handler("get_feature_importance", self.get_feature_importance)
        self.register_handler("validate_features", self.validate_features)
        
        # Initialize model discovery
        asyncio.create_task(self._discover_available_models())
    
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
        """Load a specific model into memory"""
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
                    "loaded_at": self.loaded_models[model_key]["loaded_at"]
                }
            
            # Find model file
            model_path = self._find_model_path(model_name, symbol)
            if not model_path:
                raise Exception(f"Model not found: {model_name} for symbol {symbol}")
            
            # Load the model
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            
            # Store in cache with metadata
            self.loaded_models[model_key] = {
                "model": model,
                "model_name": model_name,
                "symbol": symbol,
                "path": model_path,
                "loaded_at": datetime.now().isoformat(),
                "prediction_count": 0,
                "last_used": datetime.now().isoformat()
            }
            
            # Initialize performance tracking
            if model_key not in self.model_performance:
                self.model_performance[model_key] = {
                    "predictions_made": 0,
                    "average_confidence": 0.0,
                    "accuracy_history": [],
                    "last_evaluation": None
                }
            
            self.logger.info(f'"model": "{model_key}", "path": "{model_path}", "action": "model_loaded"')
            
            return {
                "model_name": model_name,
                "symbol": symbol,
                "status": "loaded",
                "loaded_at": self.loaded_models[model_key]["loaded_at"],
                "model_path": model_path
            }
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "symbol": "{symbol}", "error": "{e}", "action": "model_load_failed"')
            return {"error": str(e), "model_name": model_name, "symbol": symbol}
    
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
        """Generate prediction using specified model"""
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
            processed_features = self._prepare_features(features, model_name)
            
            # Generate prediction
            prediction_start = datetime.now()
            
            if hasattr(model, 'predict_proba'):
                # Classification model with probabilities
                probabilities = model.predict_proba([processed_features])[0]
                prediction = model.predict([processed_features])[0]
                confidence = max(probabilities)
            else:
                # Regression model or simple classifier
                prediction = model.predict([processed_features])[0]
                confidence = self._calculate_confidence(processed_features, model, model_name)
            
            prediction_time = (datetime.now() - prediction_start).total_seconds()
            
            # Update model usage statistics
            model_data["prediction_count"] += 1
            model_data["last_used"] = datetime.now().isoformat()
            
            # Update performance tracking
            self.model_performance[model_key]["predictions_made"] += 1
            
            result = {
                "model_name": model_name,
                "symbol": symbol,
                "prediction": float(prediction) if hasattr(prediction, 'item') else prediction,
                "features_used": processed_features,
                "prediction_time_ms": round(prediction_time * 1000, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            if return_confidence:
                result["confidence"] = float(confidence) if hasattr(confidence, 'item') else confidence
            
            self.logger.info(f'"model": "{model_key}", "prediction": {result["prediction"]}, "confidence": {result.get("confidence", "N/A")}, "action": "prediction_generated"')
            
            return result
            
        except Exception as e:
            self.logger.error(f'"model": "{model_name}", "symbol": "{symbol}", "error": "{e}", "action": "prediction_failed"')
            return {"error": str(e), "model_name": model_name, "symbol": symbol}
    
    def _prepare_features(self, features: Dict[str, Any], model_name: str) -> List[float]:
        """Prepare and validate features for model input"""
        # Determine expected feature schema based on model type
        if "technical" in model_name.lower():
            expected_features = self.feature_schemas["technical"]
        elif "sentiment" in model_name.lower():
            expected_features = self.feature_schemas["sentiment"]
        elif "volume" in model_name.lower():
            expected_features = self.feature_schemas["volume"]
        else:
            # Use all available features
            expected_features = list(features.keys())
        
        # Extract features in expected order
        processed_features = []
        for feature_name in expected_features:
            if feature_name in features:
                value = features[feature_name]
                # Convert to float and handle missing values
                try:
                    processed_features.append(float(value))
                except (ValueError, TypeError):
                    processed_features.append(0.0)  # Default for missing/invalid values
            else:
                processed_features.append(0.0)  # Default for missing features
        
        return processed_features
    
    def _calculate_confidence(self, features: List[float], model, model_name: str) -> float:
        """Calculate prediction confidence for non-probabilistic models"""
        try:
            # For models without predict_proba, estimate confidence based on feature quality
            feature_quality = 1.0
            
            # Penalize for zero/missing features
            zero_features = sum(1 for f in features if f == 0.0)
            if len(features) > 0:
                feature_quality -= (zero_features / len(features)) * 0.3
            
            # For tree-based models, try to get feature importance
            if hasattr(model, 'feature_importances_'):
                # Weight confidence by feature importance
                importances = model.feature_importances_
                if len(importances) == len(features):
                    weighted_confidence = sum(f * imp for f, imp in zip(features, importances))
                    feature_quality = min(1.0, abs(weighted_confidence) / 10.0)  # Normalize
            
            return max(0.1, min(1.0, feature_quality))
            
        except Exception:
            return 0.5  # Default moderate confidence
    
    async def get_ensemble_prediction(self, features: Dict[str, Any], symbol: str = None):
        """Generate ensemble prediction using multiple models"""
        try:
            ensemble_models = []
            
            # Find available models for this symbol/general
            for model_name in self.model_types:
                if symbol:
                    # Try bank-specific model first
                    bank_model_key = f"{symbol}_{model_name}"
                    if bank_model_key in self.model_metadata or self._find_model_path(model_name, symbol):
                        ensemble_models.append((model_name, symbol))
                
                # Add general model
                if self._find_model_path(model_name):
                    ensemble_models.append((model_name, None))
            
            if not ensemble_models:
                return {"error": "No models available for ensemble prediction"}
            
            # Generate predictions from all available models
            predictions = []
            confidences = []
            model_results = {}
            
            for model_name, model_symbol in ensemble_models[:5]:  # Limit to 5 models for performance
                try:
                    result = await self.predict(model_name, features, model_symbol, return_confidence=True)
                    
                    if "error" not in result:
                        pred = result["prediction"]
                        conf = result.get("confidence", 0.5)
                        
                        predictions.append(pred)
                        confidences.append(conf)
                        
                        model_key = f"{model_name}_{model_symbol}" if model_symbol else model_name
                        model_results[model_key] = {
                            "prediction": pred,
                            "confidence": conf
                        }
                        
                except Exception as e:
                    self.logger.error(f'"model": "{model_name}", "symbol": "{model_symbol}", "error": "{e}", "action": "ensemble_model_failed"')
            
            if not predictions:
                return {"error": "No successful predictions from ensemble models"}
            
            # Calculate ensemble prediction using confidence-weighted average
            total_weighted_prediction = sum(p * c for p, c in zip(predictions, confidences))
            total_confidence = sum(confidences)
            
            ensemble_prediction = total_weighted_prediction / total_confidence if total_confidence > 0 else 0.0
            ensemble_confidence = total_confidence / len(predictions) if predictions else 0.0
            
            result = {
                "ensemble_prediction": round(ensemble_prediction, 4),
                "ensemble_confidence": round(ensemble_confidence, 4),
                "models_used": len(predictions),
                "model_results": model_results,
                "prediction_variance": round(np.var(predictions), 4) if len(predictions) > 1 else 0.0,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat()
            }
            
            self.logger.info(f'"symbol": "{symbol}", "ensemble_prediction": {result["ensemble_prediction"]}, "models_used": {len(predictions)}, "action": "ensemble_prediction_generated"')
            
            return result
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "ensemble_prediction_failed"')
            return {"error": str(e)}
    
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
        """Enhanced health check with ML model service metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        ml_health = {
            **base_health,
            "loaded_models": len(self.loaded_models),
            "available_models": len(self.model_metadata),
            "total_predictions": sum(perf["predictions_made"] for perf in self.model_performance.values()),
            "model_directories_accessible": all(d.exists() for d in self.bank_models_dir.values() if d.exists()) and self.models_dir.exists()
        }
        
        # Check model loading capability
        try:
            # Try to find at least one model
            if self.model_metadata:
                ml_health["model_discovery"] = "ok"
            else:
                ml_health["model_discovery"] = "no_models_found"
                ml_health["status"] = "degraded"
        except:
            ml_health["model_discovery"] = "failed"
            ml_health["status"] = "unhealthy"
        
        return ml_health

async def main():
    service = MLModelService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
