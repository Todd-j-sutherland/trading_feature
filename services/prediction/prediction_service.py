"""
Prediction Service - Trading Signal Generation

Purpose:
This is the core prediction engine that generates BUY/SELL/HOLD signals for ASX stocks
using the enhanced market-aware prediction system. It combines technical analysis,
sentiment analysis, and market context to produce actionable trading recommendations.

Key Features:
- Enhanced prediction engine with sentiment integration
- Batch prediction processing for multiple symbols
- Intelligent caching with 30-minute TTL
- BUY rate monitoring and alerting
- Comprehensive prediction metrics and logging
- Integration with market data and sentiment services

Prediction Algorithm:
Based on enhanced_efficient_system_market_aware.py:
- Technical indicators (RSI, price trends, volume)
- Market sentiment from news analysis
- ASX market context and conditions
- Volume quality and trend analysis
- Confidence scoring and thresholds

API Endpoints:
- generate_predictions(symbols[], force_refresh) - Generate predictions for symbols
- generate_single_prediction(symbol) - Generate prediction for one symbol
- get_prediction(symbol) - Get cached prediction
- get_buy_rate() - Get current BUY signal rate
- clear_cache() - Clear prediction cache

Alerts:
- High BUY rate alerts (>70%) via Redis events
- Prediction failure notifications
- Performance degradation warnings

Dependencies:
- Market Data Service (technical data)
- Sentiment Service (news sentiment)
- ML Model Service (if using ML models)
- Enhanced prediction engine

Related Files:
- enhanced_efficient_system_market_aware.py
- app/core/prediction/enhanced_predictor.py
"""

import asyncio
import sys
import os
from typing import Dict, List
import json
from datetime import datetime
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

class EnhancedMarketAwarePredictor:
    """Enhanced prediction engine with market awareness"""
    
    def __init__(self):
        self.version = "v2.0_microservices"
    
    def calculate_confidence(self, symbol: str, tech_data: dict, news_data: dict, 
                           volume_data: dict, market_data: dict) -> dict:
        """
        Calculate prediction confidence using enhanced algorithm
        This is the core prediction logic from enhanced_efficient_system_market_aware.py
        """
        try:
            # Base confidence starting point
            base_confidence = 0.15  # Reduced from 0.20 for more conservative approach
            
            # Technical Analysis Component (40% weight)
            tech_score = tech_data.get('tech_score', 50)
            rsi = tech_data.get('rsi', 50)
            
            # Technical scoring
            technical_points = 0
            if 30 <= rsi <= 70:
                technical_points += 15
            elif rsi < 30:
                technical_points += 20  # Oversold opportunity
            
            if tech_score > 60:
                technical_points += 10
            
            # News Sentiment Component (30% weight)
            sentiment_score = news_data.get('sentiment_score', 0.0)
            news_confidence = news_data.get('news_confidence', 0.5)
            
            # Convert sentiment to points
            sentiment_points = sentiment_score * 15  # -15 to +15 range
            confidence_bonus = news_confidence * 10  # 0 to 10 points
            
            # Volume Analysis Component (20% weight)
            volume_ratio = volume_data.get('volume_ratio', 1.0)
            volume_points = min(10, volume_ratio * 5)  # Up to 10 points
            
            # Market Context Adjustment (10% weight)
            market_context = market_data.get('context', 'NEUTRAL')
            buy_threshold = market_data.get('buy_threshold', 0.70)
            
            context_adjustment = 0
            if market_context == 'BULLISH':
                context_adjustment = 5
            elif market_context == 'BEARISH':
                context_adjustment = -10
            
            # Calculate final confidence
            total_points = technical_points + sentiment_points + confidence_bonus + volume_points + context_adjustment
            final_confidence = base_confidence + (total_points / 100)
            final_confidence = max(0.0, min(1.0, final_confidence))
            
            # Determine action based on confidence and market context
            action = "HOLD"  # Default
            
            if market_context == "BEARISH":
                # Higher threshold during bearish markets
                if final_confidence > 0.85 and tech_score > 75 and sentiment_score > 0.15:
                    action = "BUY"
                elif final_confidence < 0.30:
                    action = "SELL"
            else:
                # Normal thresholds
                if final_confidence > buy_threshold and tech_score > 60 and sentiment_score > -0.05:
                    action = "BUY"
                elif final_confidence < 0.35:
                    action = "SELL"
            
            return {
                "action": action,
                "confidence": round(final_confidence, 3),
                "technical_score": tech_score,
                "sentiment_score": sentiment_score,
                "market_context": market_context,
                "components": {
                    "technical_points": technical_points,
                    "sentiment_points": round(sentiment_points, 2),
                    "volume_points": round(volume_points, 2),
                    "context_adjustment": context_adjustment
                },
                "thresholds": {
                    "buy_threshold": buy_threshold,
                    "applied_threshold": 0.85 if market_context == "BEARISH" else buy_threshold
                }
            }
            
        except Exception as e:
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "error": str(e),
                "fallback": True
            }

class PredictionService(BaseService):
    """Enhanced prediction service with caching, batching, and comprehensive monitoring"""
    
    def __init__(self):
        super().__init__("prediction")
        
        # Initialize prediction components
        self.predictor = EnhancedMarketAwarePredictor()
        self.prediction_cache = {}
        self.cache_ttl = 1800  # 30 minutes
        
        # Default symbols for prediction
        self.default_symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        # Metrics tracking
        self.prediction_count = 0
        self.buy_signal_count = 0
        self.sell_signal_count = 0
        self.hold_signal_count = 0
        self.error_count = 0
        
        # Register methods
        self.register_handler("generate_predictions", self.generate_predictions)
        self.register_handler("generate_single_prediction", self.generate_single_prediction)
        self.register_handler("get_prediction", self.get_prediction)
        self.register_handler("get_buy_rate", self.get_buy_rate)
        self.register_handler("get_signal_distribution", self.get_signal_distribution)
        self.register_handler("clear_cache", self.clear_cache)
        self.register_handler("get_prediction_stats", self.get_prediction_stats)
        self.register_handler("get_cache_stats", self.get_cache_stats)
        self.register_handler("validate_predictor", self.validate_predictor)
        
        # Performance tracking
        self.request_times = []
        self.cache_hit_count = 0
        
        # Background cache cleanup
        asyncio.create_task(self._cache_cleanup_task())
    
    async def generate_predictions(self, symbols: List[str] = None, force_refresh: bool = False):
        """Generate predictions for multiple symbols with enhanced validation and error handling"""
        # Input validation
        if symbols is not None:
            if not isinstance(symbols, list):
                return {"error": "Symbols must be provided as a list"}
            if len(symbols) == 0:
                return {"error": "Empty symbols list provided"}
            if len(symbols) > 20:  # Rate limiting
                return {"error": "Too many symbols requested (max 20)"}
            
            # Validate and sanitize each symbol
            validated_symbols = []
            for symbol in symbols:
                if isinstance(symbol, str) and symbol.strip():
                    clean_symbol = symbol.upper().strip()
                    if clean_symbol.replace('.', '').replace('-', '').isalnum() and len(clean_symbol) <= 10:
                        validated_symbols.append(clean_symbol)
                    else:
                        self.logger.warning(f'"invalid_symbol": "{symbol}", "action": "symbol_skipped"')
            
            if not validated_symbols:
                return {"error": "No valid symbols provided after validation"}
            
            symbols = validated_symbols
        else:
            symbols = self.default_symbols.copy()
        
        predictions = {}
        cache_hits = 0
        fresh_predictions = 0
        error_symbols = []
        
        self.logger.info(f'"symbols": {symbols}, "force_refresh": {force_refresh}, "symbol_count": {len(symbols)}, "action": "prediction_batch_started"')
        
        # Process symbols with error isolation
        for symbol in symbols:
            try:
                # Check cache first
                cache_key = f"prediction:{symbol}"
                
                if not force_refresh and cache_key in self.prediction_cache:
                    cached_data, timestamp = self.prediction_cache[cache_key]
                    cache_age = datetime.now().timestamp() - timestamp
                    
                    if cache_age < self.cache_ttl:
                        # Enhance cached data with current cache info
                        enhanced_cached = {
                            **cached_data,
                            "cached": True,
                            "cache_age": round(cache_age, 1),
                            "cache_expires_in": round(self.cache_ttl - cache_age, 1)
                        }
                        predictions[symbol] = enhanced_cached
                        cache_hits += 1
                        continue
                
                # Generate fresh prediction with timeout
                try:
                    prediction = await asyncio.wait_for(
                        self._generate_fresh_prediction(symbol), 
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    self.logger.error(f'"symbol": "{symbol}", "error": "prediction_timeout", "action": "prediction_generation_timeout"')
                    prediction = {
                        "symbol": symbol,
                        "action": "HOLD",
                        "confidence": 0.5,
                        "error": "Prediction generation timeout",
                        "timestamp": datetime.now().isoformat(),
                        "fallback_prediction": True
                    }
                
                predictions[symbol] = prediction
                
                # Cache successful predictions only
                if "error" not in prediction or prediction.get("fallback_prediction"):
                    self.prediction_cache[cache_key] = (prediction, datetime.now().timestamp())
                    fresh_predictions += 1
                
                # Update metrics only for valid predictions
                if "error" not in prediction and not prediction.get("fallback_prediction"):
                    self.prediction_count += 1
                    action = prediction.get('action', 'HOLD')
                    if action == 'BUY':
                        self.buy_signal_count += 1
                    elif action == 'SELL':
                        self.sell_signal_count += 1
                    else:
                        self.hold_signal_count += 1
                    
                    # Publish prediction event for successful predictions
                    self.publish_event("prediction_generated", {
                        "symbol": symbol,
                        "action": action,
                        "confidence": prediction.get("confidence", 0.5),
                        "cache_hit": False
                    }, priority="high")
                else:
                    error_symbols.append(symbol)
                
            except Exception as e:
                self.error_count += 1
                error_symbols.append(symbol)
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "prediction_generation_failed"')
                predictions[symbol] = {
                    "symbol": symbol,
                    "error": str(e),
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Calculate comprehensive statistics
        successful_predictions = [p for p in predictions.values() 
                                if "error" not in p and not p.get("fallback_prediction")]
        fallback_predictions = [p for p in predictions.values() 
                              if p.get("fallback_prediction")]
        failed_predictions = [p for p in predictions.values() 
                            if "error" in p and not p.get("fallback_prediction")]
        
        # Signal distribution analysis
        buy_signals = [p for p in successful_predictions if p.get('action') == 'BUY']
        sell_signals = [p for p in successful_predictions if p.get('action') == 'SELL']
        hold_signals = [p for p in successful_predictions if p.get('action') == 'HOLD']
        
        total_actionable = len(successful_predictions) + len(fallback_predictions)
        buy_rate = (len(buy_signals) / total_actionable * 100) if total_actionable > 0 else 0
        sell_rate = (len(sell_signals) / total_actionable * 100) if total_actionable > 0 else 0
        hold_rate = (len(hold_signals) / total_actionable * 100) if total_actionable > 0 else 0
        
        # Quality metrics
        success_rate = (len(successful_predictions) / len(symbols) * 100) if symbols else 0
        
        self.logger.info(f'"total_symbols": {len(symbols)}, "successful": {len(successful_predictions)}, "fallback": {len(fallback_predictions)}, "failed": {len(failed_predictions)}, "cache_hits": {cache_hits}, "fresh_predictions": {fresh_predictions}, "buy_rate": {buy_rate:.1f}, "sell_rate": {sell_rate:.1f}, "success_rate": {success_rate:.1f}, "action": "prediction_batch_completed"')
        
        # Intelligent alerting based on context
        if buy_rate > 70 and len(successful_predictions) >= 3:
            self.publish_event("buy_rate_alert", {
                "buy_rate": buy_rate,
                "total_predictions": len(successful_predictions),
                "buy_signals": len(buy_signals),
                "alert_type": "high_buy_rate",
                "recommendation": "Review market context - high BUY rate may indicate system bias or strong market conditions",
                "symbols_affected": [p["symbol"] for p in buy_signals]
            }, priority="urgent")
        
        # Alert on high failure rate
        if len(failed_predictions) > len(symbols) * 0.3:  # More than 30% failures
            self.publish_event("prediction_failure_alert", {
                "failure_rate": (len(failed_predictions) / len(symbols)) * 100,
                "failed_symbols": error_symbols,
                "total_symbols": len(symbols),
                "alert_type": "high_failure_rate"
            }, priority="high")
        
        return {
            "predictions": predictions,
            "summary": {
                "total_symbols": len(symbols),
                "successful": len(successful_predictions),
                "fallback": len(fallback_predictions),
                "failed": len(failed_predictions),
                "cache_hits": cache_hits,
                "fresh_predictions": fresh_predictions,
                "success_rate": round(success_rate, 1),
                "signal_distribution": {
                    "buy_rate": round(buy_rate, 1),
                    "sell_rate": round(sell_rate, 1),
                    "hold_rate": round(hold_rate, 1)
                },
                "error_symbols": error_symbols
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def _generate_fresh_prediction(self, symbol: str) -> Dict:
        """Generate a fresh prediction for a single symbol with comprehensive error handling"""
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Invalid symbol provided")
        
        symbol = symbol.upper().strip()
        prediction_start_time = time.time()
        
        # Initialize default data structures for fallback
        default_technical_data = {
            "current_price": None,
            "rsi": 50.0,
            "macd": 0.0,
            "bb_upper": None,
            "bb_lower": None,
            "tech_score": 50.0,
            "volatility": 0.15
        }
        
        default_volume_data = {
            "volume_ratio": 1.0,
            "volume_quality_score": 0.5,
            "avg_volume": 1000000
        }
        
        default_market_context = {
            "context": "NEUTRAL",
            "buy_threshold": 0.70,
            "market_session": "unknown"
        }
        
        default_sentiment_data = {
            "sentiment_score": 0.0,
            "news_confidence": 0.5,
            "news_quality_score": 0.5,
            "article_count": 0
        }
        
        technical_data = default_technical_data.copy()
        volume_data = default_volume_data.copy()
        market_context_data = default_market_context.copy()
        sentiment_data = default_sentiment_data.copy()
        
        data_quality_flags = {
            "market_data_available": False,
            "sentiment_data_available": False,
            "has_current_price": False,
            "asx_context_available": False
        }
        
        try:
            # Get market data from market data service with timeout
            try:
                market_response = await asyncio.wait_for(
                    self.call_service("market-data", "get_market_data", symbol=symbol),
                    timeout=15.0
                )
                
                if isinstance(market_response, dict) and "error" not in market_response:
                    # Safely extract and validate technical data
                    if "technical" in market_response and isinstance(market_response["technical"], dict):
                        tech_response = market_response["technical"]
                        for key in ["current_price", "rsi", "tech_score", "volatility"]:
                            if key in tech_response and isinstance(tech_response[key], (int, float)):
                                technical_data[key] = tech_response[key]
                        
                        data_quality_flags["market_data_available"] = True
                        if technical_data["current_price"] is not None and technical_data["current_price"] > 0:
                            data_quality_flags["has_current_price"] = True
                    
                    # Extract volume data
                    if "volume" in market_response:
                        if isinstance(market_response["volume"], dict):
                            volume_data.update(market_response["volume"])
                        elif isinstance(market_response["volume"], (int, float)):
                            volume_data["volume_ratio"] = market_response["volume"] / 1000000
                else:
                    raise Exception(f"Market data error: {market_response.get('error', 'Unknown error')}")
                
            except asyncio.TimeoutError:
                self.logger.warning(f'"symbol": "{symbol}", "error": "market_data_timeout", "action": "using_fallback_market_data"')
            except Exception as e:
                self.logger.warning(f'"symbol": "{symbol}", "error": "market_data_fetch_failed", "details": "{e}", "action": "using_fallback_market_data"')
            
            # Get ASX market context
            try:
                asx_response = await asyncio.wait_for(
                    self.call_service("market-data", "get_asx_context"),
                    timeout=10.0
                )
                
                if isinstance(asx_response, dict) and "error" not in asx_response:
                    market_context_data.update(asx_response)
                    data_quality_flags["asx_context_available"] = True
                    
            except Exception as e:
                self.logger.warning(f'"symbol": "{symbol}", "error": "asx_context_fetch_failed", "details": "{e}", "action": "using_default_context"')
            
            # Get sentiment from sentiment service
            try:
                sentiment_response = await asyncio.wait_for(
                    self.call_service("sentiment", "analyze_sentiment", symbol=symbol),
                    timeout=10.0
                )
                
                if isinstance(sentiment_response, dict) and "error" not in sentiment_response:
                    # Validate and clamp sentiment values
                    for key in ["sentiment_score", "news_confidence", "news_quality_score"]:
                        if key in sentiment_response and isinstance(sentiment_response[key], (int, float)):
                            if key == "sentiment_score":
                                sentiment_data[key] = max(-1.0, min(1.0, sentiment_response[key]))
                            else:
                                sentiment_data[key] = max(0.0, min(1.0, sentiment_response[key]))
                    
                    if "article_count" in sentiment_response:
                        sentiment_data["article_count"] = max(0, int(sentiment_response.get("article_count", 0)))
                    
                    data_quality_flags["sentiment_data_available"] = True
                else:
                    raise Exception(f"Sentiment error: {sentiment_response.get('error', 'Unknown error')}")
                    
            except asyncio.TimeoutError:
                self.logger.warning(f'"symbol": "{symbol}", "error": "sentiment_timeout", "action": "using_fallback_sentiment"')
            except Exception as e:
                self.logger.warning(f'"symbol": "{symbol}", "error": "sentiment_fetch_failed", "details": "{e}", "action": "using_fallback_sentiment"')
            
            # Generate prediction using enhanced logic with error containment
            try:
                if not hasattr(self, 'predictor') or self.predictor is None:
                    self.logger.error(f'"symbol": "{symbol}", "error": "predictor_unavailable", "action": "generating_simple_fallback"')
                    prediction = self._generate_simple_prediction(symbol, technical_data, sentiment_data)
                else:
                    prediction = self.predictor.calculate_confidence(
                        symbol=symbol,
                        tech_data=technical_data,
                        news_data=sentiment_data,
                        volume_data=volume_data,
                        market_data=market_context_data
                    )
                    
                    # Validate prediction structure
                    if not isinstance(prediction, dict):
                        raise ValueError("Predictor returned invalid prediction format")
                    
                    required_fields = ["action", "confidence", "rationale"]
                    for field in required_fields:
                        if field not in prediction:
                            prediction[field] = self._get_default_field_value(field)
                    
                    # Validate and clamp confidence
                    if not isinstance(prediction.get("confidence"), (int, float)):
                        prediction["confidence"] = 0.5
                    else:
                        prediction["confidence"] = max(0.0, min(1.0, float(prediction["confidence"])))
                    
                    # Validate action
                    valid_actions = ["BUY", "SELL", "HOLD"]
                    if prediction.get("action") not in valid_actions:
                        prediction["action"] = "HOLD"
                
            except Exception as e:
                self.logger.error(f'"symbol": "{symbol}", "error": "prediction_calculation_failed", "details": "{e}", "action": "generating_fallback_prediction"')
                prediction = self._generate_simple_prediction(symbol, technical_data, sentiment_data)
            
            # Enhance prediction with comprehensive metadata
            generation_time = time.time() - prediction_start_time
            enhanced_prediction = {
                **prediction,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "prediction_id": f"{symbol}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}",
                "generation_time_ms": round(generation_time * 1000, 2),
                "data_quality": data_quality_flags,
                "system_info": {
                    "service_version": "1.0.0",
                    "predictor_available": hasattr(self, 'predictor') and self.predictor is not None,
                    "predictor_version": getattr(self.predictor, 'version', 'unknown') if hasattr(self, 'predictor') and self.predictor else None,
                    "cache_enabled": True,
                    "cache_age": 0
                },
                "input_data": {
                    "current_price": technical_data.get("current_price"),
                    "rsi": technical_data.get("rsi"),
                    "sentiment_score": sentiment_data.get("sentiment_score"),
                    "market_context": market_context_data.get("context")
                }
            }
            
            # Add warning flags for data quality issues
            warnings = []
            if not data_quality_flags["market_data_available"]:
                warnings.append("market_data_unavailable")
            if not data_quality_flags["sentiment_data_available"]:
                warnings.append("sentiment_data_unavailable")
            if not data_quality_flags["has_current_price"]:
                warnings.append("no_current_price")
            if not data_quality_flags["asx_context_available"]:
                warnings.append("asx_context_unavailable")
            
            if warnings:
                enhanced_prediction["warnings"] = warnings
                enhanced_prediction["reliability"] = "reduced"
                # Lower confidence for predictions with data quality issues
                if enhanced_prediction["confidence"] > 0.7:
                    enhanced_prediction["confidence"] = 0.7
                    enhanced_prediction["confidence_adjusted"] = True
            else:
                enhanced_prediction["reliability"] = "high"
            
            return enhanced_prediction
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "prediction_generation_critical_error"')
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0.5,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "prediction_id": f"{symbol}_{int(datetime.now().timestamp())}_error",
                "fallback_prediction": True,
                "reliability": "critical_error",
                "generation_time_ms": round((time.time() - prediction_start_time) * 1000, 2)
            }
    
    def _generate_simple_prediction(self, symbol: str, technical_data: dict, sentiment_data: dict) -> dict:
        """Generate a simple fallback prediction when the main predictor is unavailable"""
        # Simple logic based on available data
        sentiment_score = sentiment_data.get("sentiment_score", 0.0)
        rsi = technical_data.get("rsi", 50.0)
        current_price = technical_data.get("current_price")
        
        # Simple rules-based prediction
        if sentiment_score > 0.3 and rsi < 40:  # Positive sentiment + oversold
            action = "BUY"
            confidence = 0.6
            rationale = "Positive sentiment with oversold technical conditions (simple model)"
        elif sentiment_score < -0.3 and rsi > 70:  # Negative sentiment + overbought
            action = "SELL"
            confidence = 0.6
            rationale = "Negative sentiment with overbought technical conditions (simple model)"
        elif sentiment_score > 0.1 and 40 <= rsi <= 60:  # Mild positive sentiment, neutral RSI
            action = "BUY"
            confidence = 0.55
            rationale = "Mild positive sentiment with neutral technical conditions (simple model)"
        elif current_price is None or current_price <= 0:  # No price data
            action = "HOLD"
            confidence = 0.3
            rationale = "Insufficient price data for reliable prediction (simple model)"
        else:
            action = "HOLD"
            confidence = 0.5
            rationale = "Insufficient signal strength for clear action (simple model)"
        
        return {
            "action": action,
            "confidence": confidence,
            "rationale": rationale,
            "prediction_method": "simple_fallback",
            "inputs_used": {
                "sentiment_score": sentiment_score,
                "rsi": rsi,
                "has_price": current_price is not None and current_price > 0
            }
        }
    
    def _get_default_field_value(self, field: str):
        """Get default values for missing prediction fields"""
        defaults = {
            "action": "HOLD",
            "confidence": 0.5,
            "rationale": "Default prediction due to missing predictor data",
            "recommendation": "Monitor for better data quality",
            "risk_level": "medium"
        }
        return defaults.get(field, None)
    
    async def generate_single_prediction(self, symbol: str, force_refresh: bool = False):
        """Generate prediction for a single symbol"""
        result = await self.generate_predictions([symbol], force_refresh)
        return result["predictions"].get(symbol, {"error": "Prediction failed"})
    
    async def get_prediction(self, symbol: str):
        """Get latest cached prediction for symbol"""
        cache_key = f"prediction:{symbol}"
        
        if cache_key in self.prediction_cache:
            cached_data, timestamp = self.prediction_cache[cache_key]
            age = datetime.now().timestamp() - timestamp
            
            cached_prediction = {
                **cached_data,
                "cache_age": round(age, 1),
                "cached": True,
                "cache_expires_in": round(self.cache_ttl - age, 1)
            }
            
            return cached_prediction
        else:
            return {"error": "No cached prediction available", "symbol": symbol}
    
    async def get_buy_rate(self, timeframe: str = "current"):
        """Get current signal distribution"""
        if self.prediction_count == 0:
            return {
                "buy_rate": 0,
                "sell_rate": 0,
                "hold_rate": 0,
                "total_predictions": 0
            }
        
        buy_rate = (self.buy_signal_count / self.prediction_count) * 100
        sell_rate = (self.sell_signal_count / self.prediction_count) * 100
        hold_rate = (self.hold_signal_count / self.prediction_count) * 100
        
        return {
            "buy_rate": round(buy_rate, 1),
            "sell_rate": round(sell_rate, 1), 
            "hold_rate": round(hold_rate, 1),
            "total_predictions": self.prediction_count,
            "buy_signals": self.buy_signal_count,
            "sell_signals": self.sell_signal_count,
            "hold_signals": self.hold_signal_count,
            "error_count": self.error_count,
            "timeframe": timeframe
        }
    
    async def clear_cache(self):
        """Clear prediction cache"""
        cache_size = len(self.prediction_cache)
        self.prediction_cache.clear()
        
        self.logger.info(f'"cache_size": {cache_size}, "action": "cache_cleared"')
        return {"cleared_entries": cache_size}
    
    async def get_prediction_stats(self):
        """Get comprehensive prediction statistics"""
        return {
            "service_stats": {
                "total_predictions": self.prediction_count,
                "error_rate": round((self.error_count / max(1, self.prediction_count)) * 100, 2),
                "cache_size": len(self.prediction_cache),
                "cache_ttl": self.cache_ttl
            },
            "signal_distribution": await self.get_buy_rate(),
            "predictor_info": {
                "version": self.predictor.version,
                "supported_symbols": self.default_symbols
            }
        }
    
    async def get_signal_distribution(self):
        """Get comprehensive signal distribution statistics"""
        total_signals = self.buy_signal_count + self.sell_signal_count + self.hold_signal_count
        
        if total_signals == 0:
            return {
                "total_signals": 0,
                "distribution": {"BUY": 0, "SELL": 0, "HOLD": 0},
                "percentages": {"BUY": 0, "SELL": 0, "HOLD": 0}
            }
        
        distribution = {
            "BUY": self.buy_signal_count,
            "SELL": self.sell_signal_count,
            "HOLD": self.hold_signal_count
        }
        
        percentages = {
            "BUY": round((self.buy_signal_count / total_signals) * 100, 1),
            "SELL": round((self.sell_signal_count / total_signals) * 100, 1),
            "HOLD": round((self.hold_signal_count / total_signals) * 100, 1)
        }
        
        return {
            "total_signals": total_signals,
            "distribution": distribution,
            "percentages": percentages,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_cache_stats(self):
        """Get detailed cache statistics"""
        cache_entries = []
        expired_count = 0
        current_time = datetime.now().timestamp()
        
        for cache_key, (data, timestamp) in self.prediction_cache.items():
            age = current_time - timestamp
            is_expired = age > self.cache_ttl
            
            if is_expired:
                expired_count += 1
            
            cache_entries.append({
                "symbol": cache_key.replace("prediction:", ""),
                "age_seconds": round(age, 1),
                "expires_in": round(self.cache_ttl - age, 1),
                "is_expired": is_expired,
                "action": data.get("action", "unknown"),
                "confidence": data.get("confidence", 0)
            })
        
        return {
            "total_entries": len(self.prediction_cache),
            "expired_entries": expired_count,
            "valid_entries": len(self.prediction_cache) - expired_count,
            "cache_hit_count": self.cache_hit_count,
            "cache_ttl": self.cache_ttl,
            "entries": cache_entries
        }
    
    async def validate_predictor(self):
        """Validate predictor functionality and dependencies"""
        validation_results = {
            "predictor_loaded": self.predictor is not None,
            "test_results": {},
            "dependencies": {},
            "warnings": []
        }
        
        # Test predictor with sample data
        if self.predictor is not None:
            try:
                test_symbol = "CBA.AX"
                test_tech_data = {"rsi": 45, "tech_score": 55, "current_price": 100}
                test_news_data = {"sentiment_score": 0.1, "news_confidence": 0.8}
                test_volume_data = {"volume_ratio": 1.2, "volume_quality_score": 0.7}
                test_market_data = {"context": "NEUTRAL", "buy_threshold": 0.7}
                
                test_prediction = self.predictor.calculate_confidence(
                    symbol=test_symbol,
                    tech_data=test_tech_data,
                    news_data=test_news_data,
                    volume_data=test_volume_data,
                    market_data=test_market_data
                )
                
                validation_results["test_results"]["predictor_calculation"] = "passed"
                validation_results["test_results"]["sample_action"] = test_prediction.get("action", "unknown")
                validation_results["test_results"]["sample_confidence"] = test_prediction.get("confidence", 0)
                
            except Exception as e:
                validation_results["test_results"]["predictor_calculation"] = "failed"
                validation_results["test_results"]["error"] = str(e)
                validation_results["warnings"].append(f"Predictor test failed: {e}")
        else:
            validation_results["warnings"].append("Predictor not loaded")
        
        # Test service dependencies
        try:
            market_health = await asyncio.wait_for(
                self.call_service("market-data", "health"), 
                timeout=5.0
            )
            validation_results["dependencies"]["market_data"] = "available"
        except Exception as e:
            validation_results["dependencies"]["market_data"] = f"unavailable: {e}"
            validation_results["warnings"].append("Market data service unavailable")
        
        try:
            sentiment_health = await asyncio.wait_for(
                self.call_service("sentiment", "health"), 
                timeout=5.0
            )
            validation_results["dependencies"]["sentiment"] = "available"
        except Exception as e:
            validation_results["dependencies"]["sentiment"] = f"unavailable: {e}"
            validation_results["warnings"].append("Sentiment service unavailable")
        
        # Overall status
        validation_results["overall_status"] = "healthy" if len(validation_results["warnings"]) == 0 else "degraded"
        validation_results["timestamp"] = datetime.now().isoformat()
        
        return validation_results
    
    async def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        while self.running:
            try:
                current_time = datetime.now().timestamp()
                expired_keys = []
                
                for cache_key, (data, timestamp) in self.prediction_cache.items():
                    if current_time - timestamp > self.cache_ttl:
                        expired_keys.append(cache_key)
                
                for key in expired_keys:
                    del self.prediction_cache[key]
                
                if expired_keys:
                    self.logger.info(f'"expired_cache_entries": {len(expired_keys)}, "action": "cache_cleanup"')
                
                # Clean up every 10 minutes
                await asyncio.sleep(600)
                
            except Exception as e:
                self.logger.error(f'"error": "{e}", "action": "cache_cleanup_error"')
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    async def health_check(self):
        """Enhanced health check with prediction service metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        prediction_health = {
            **base_health,
            "predictor_loaded": self.predictor is not None,
            "cache_size": len(self.prediction_cache),
            "prediction_count": self.prediction_count,
            "buy_signal_count": self.buy_signal_count,
            "sell_signal_count": self.sell_signal_count,
            "hold_signal_count": self.hold_signal_count,
            "error_count": self.error_count,
            "cache_hit_count": self.cache_hit_count,
            "current_buy_rate": round((self.buy_signal_count / max(1, self.prediction_count)) * 100, 1),
            "predictor_version": getattr(self.predictor, 'version', 'unknown') if self.predictor else None
        }
        
        # Health status based on error rate
        if self.prediction_count > 0:
            error_rate = (self.error_count / self.prediction_count) * 100
            if error_rate > 20:
                prediction_health["status"] = "degraded"
                prediction_health["warning"] = f"High error rate: {error_rate:.1f}%"
        
        # Test service dependencies
        try:
            # Test market data service
            await self.call_service("market-data", "health")
            prediction_health["market_data_service"] = "connected"
        except:
            prediction_health["market_data_service"] = "disconnected"
        
        try:
            # Test sentiment service
            await self.call_service("sentiment", "health")
            prediction_health["sentiment_service"] = "connected"
        except:
            prediction_health["sentiment_service"] = "disconnected"
        
        return prediction_health

async def main():
    service = PredictionService()
    
    # Setup event subscriptions
    event_handler = service.subscribe_to_events(["market_data_updated"], handle_market_data_event)
    if event_handler:
        asyncio.create_task(event_handler())
    
    await service.start_server()

async def handle_market_data_event(event_type: str, event_data: dict):
    """Handle market data update events"""
    if event_type == "market_data_updated":
        symbol = event_data.get("symbol")
        # Could invalidate cache for this symbol or trigger fresh prediction
        print(f"Market data updated for {symbol}")

if __name__ == "__main__":
    asyncio.run(main())
