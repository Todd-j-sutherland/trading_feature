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
        self.register_handler("clear_cache", self.clear_cache)
        self.register_handler("get_prediction_stats", self.get_prediction_stats)
    
    async def generate_predictions(self, symbols: List[str] = None, force_refresh: bool = False):
        """Generate predictions for multiple symbols with intelligent caching"""
        if not symbols:
            symbols = self.default_symbols
        
        predictions = {}
        cache_hits = 0
        fresh_predictions = 0
        
        self.logger.info(f'"symbols": {symbols}, "force_refresh": {force_refresh}, "action": "prediction_batch_started"')
        
        for symbol in symbols:
            try:
                # Check cache first
                cache_key = f"prediction:{symbol}"
                
                if not force_refresh and cache_key in self.prediction_cache:
                    cached_data, timestamp = self.prediction_cache[cache_key]
                    if datetime.now().timestamp() - timestamp < self.cache_ttl:
                        predictions[symbol] = cached_data
                        cache_hits += 1
                        continue
                
                # Generate fresh prediction
                prediction = await self._generate_fresh_prediction(symbol)
                predictions[symbol] = prediction
                
                # Cache the result
                self.prediction_cache[cache_key] = (prediction, datetime.now().timestamp())
                fresh_predictions += 1
                
                # Update metrics
                self.prediction_count += 1
                action = prediction.get('action', 'HOLD')
                if action == 'BUY':
                    self.buy_signal_count += 1
                elif action == 'SELL':
                    self.sell_signal_count += 1
                else:
                    self.hold_signal_count += 1
                
                # Publish prediction event
                self.publish_event("prediction_generated", {
                    "symbol": symbol,
                    "prediction": prediction,
                    "cache_hit": False
                }, priority="high")
                
            except Exception as e:
                self.error_count += 1
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "prediction_generation_failed"')
                predictions[symbol] = {"error": str(e), "status": "failed"}
        
        # Calculate and log signal rates
        successful_predictions = [p for p in predictions.values() if "error" not in p]
        buy_signals = [p for p in successful_predictions if p.get('action') == 'BUY']
        sell_signals = [p for p in successful_predictions if p.get('action') == 'SELL']
        
        buy_rate = (len(buy_signals) / len(successful_predictions) * 100) if successful_predictions else 0
        sell_rate = (len(sell_signals) / len(successful_predictions) * 100) if successful_predictions else 0
        
        self.logger.info(f'"total_symbols": {len(symbols)}, "cache_hits": {cache_hits}, "fresh_predictions": {fresh_predictions}, "buy_rate": {buy_rate:.1f}, "sell_rate": {sell_rate:.1f}, "action": "prediction_batch_completed"')
        
        # Alert if BUY rate is concerning (too high in bear market)
        if buy_rate > 70:
            self.publish_event("buy_rate_alert", {
                "buy_rate": buy_rate,
                "total_predictions": len(successful_predictions),
                "buy_signals": len(buy_signals),
                "alert_type": "high_buy_rate",
                "recommendation": "Review market context - high BUY rate may indicate system bias"
            }, priority="urgent")
        
        return {
            "predictions": predictions,
            "summary": {
                "total_symbols": len(symbols),
                "successful": len(successful_predictions),
                "failed": len(symbols) - len(successful_predictions),
                "cache_hits": cache_hits,
                "fresh_predictions": fresh_predictions,
                "buy_rate": round(buy_rate, 1),
                "sell_rate": round(sell_rate, 1),
                "hold_rate": round(100 - buy_rate - sell_rate, 1)
            }
        }
    
    async def _generate_fresh_prediction(self, symbol: str) -> Dict:
        """Generate a fresh prediction for a single symbol"""
        try:
            # Get market data from market data service
            try:
                market_response = await self.call_service("market-data", "get_market_data", symbol=symbol)
                if "error" in market_response:
                    raise Exception(f"Market data error: {market_response['error']}")
                
                technical_data = market_response.get("technical", {})
                volume_data = {
                    "volume_ratio": market_response.get("volume", 1.0) / 1000000,  # Normalize volume
                    "volume_quality_score": 0.8  # Default quality score
                }
                
                # Get ASX market context
                asx_context = await self.call_service("market-data", "get_asx_context")
                market_context_data = asx_context if "error" not in asx_context else {
                    "context": "NEUTRAL", "buy_threshold": 0.70
                }
                
            except Exception as e:
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "market_data_fetch_failed"')
                # Fallback to basic data structure
                technical_data = {"tech_score": 50, "rsi": 50, "current_price": 0}
                volume_data = {"volume_ratio": 1.0, "volume_quality_score": 0.5}
                market_context_data = {"context": "NEUTRAL", "buy_threshold": 0.70}
            
            # Get sentiment from sentiment service
            try:
                sentiment_response = await self.call_service("sentiment", "analyze_sentiment", symbol=symbol)
                if "error" in sentiment_response:
                    raise Exception(f"Sentiment error: {sentiment_response['error']}")
                sentiment_data = sentiment_response
            except Exception as e:
                self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "sentiment_fetch_failed"')
                # Fallback sentiment data
                sentiment_data = {
                    "sentiment_score": 0.0,
                    "news_confidence": 0.5,
                    "news_quality_score": 0.5
                }
            
            # Generate prediction using enhanced logic
            prediction = self.predictor.calculate_confidence(
                symbol=symbol,
                tech_data=technical_data,
                news_data=sentiment_data,
                volume_data=volume_data,
                market_data=market_context_data
            )
            
            # Enhance prediction with additional metadata
            enhanced_prediction = {
                **prediction,
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "prediction_id": f"{symbol}_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}",
                "market_data_available": "error" not in str(technical_data),
                "sentiment_data_available": "error" not in str(sentiment_data),
                "current_price": technical_data.get("current_price", 0),
                "predictor_version": self.predictor.version,
                "cache_age": 0
            }
            
            return enhanced_prediction
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "prediction_generation_critical_error"')
            return {
                "symbol": symbol,
                "action": "HOLD",
                "confidence": 0.5,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "fallback_prediction": True
            }
    
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
            "current_buy_rate": round((self.buy_signal_count / max(1, self.prediction_count)) * 100, 1),
            "predictor_version": self.predictor.version
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
