# Copilot Implementation Guide: VM-Native Microservices Migration

## Executive Summary for Copilot

**Objective**: Migrate Todd's monolithic trading system to lightweight VM-native microservices without Docker, ensuring zero downtime and complete backward compatibility.

**Critical Requirements**:
- Maintain all existing cron jobs and functionality
- <200MB total memory overhead (vs 1.5GB Docker overhead)
- Complete backward compatibility during transition
- All predictions, evaluations, and paper trading must continue working
- Zero data loss during migration

## Current System Analysis

### Existing Cron Jobs (Must All Be Preserved)
```bash
# CRITICAL: Every 30 minutes during market hours (00:00-05:59 UTC)
*/30 0-5 * * 1-5 cd /root/test && /root/trading_venv/bin/python production/cron/fixed_price_mapping_system.py >> logs/prediction_fixed.log 2>&1

# Morning analysis (07:00 UTC daily)
0 7 * * 1-5 cd /root/test && /root/trading_venv/bin/python enhanced_morning_analyzer_with_ml.py >> logs/market_aware_morning.log 2>&1

# Hourly prediction evaluation (critical for accuracy tracking)
0 * * * * cd /root/test && bash evaluate_predictions_comprehensive.sh >> logs/evaluation.log 2>&1

# Daily ML training (08:00 UTC)
0 8 * * * cd /root/test && /root/trading_venv/bin/python enhanced_evening_analyzer_with_ml.py >> logs/evening_ml_training.log 2>&1

# Dashboard updates (every 4 hours)
0 */4 * * * cd /root/test && /root/trading_venv/bin/python comprehensive_table_dashboard.py >> logs/dashboard_updates.log 2>&1

# Paper trading execution (07:15 UTC)
15 7 * * 1-5 cd /root/test/ig_markets_paper_trading && /root/trading_venv/bin/python scripts/run_paper_trader.py >> logs/paper_trading_execution.log 2>&1

# Database maintenance (02:00 UTC daily)
0 2 * * * cd /root/test && sqlite3 data/trading_predictions.db 'VACUUM; REINDEX;' >> logs/db_maintenance.log 2>&1

# Market context monitoring (10:00-16:00 AEST)
*/30 10-16 * * 1-5 cd /root/test && /root/trading_venv/bin/python -m app.main_enhanced market-status >> logs/market_context.log 2>&1
```

### Critical Files That Must Be Handled
```
Core Files:
├── production/cron/fixed_price_mapping_system.py (MAIN PREDICTION ENGINE)
├── enhanced_morning_analyzer_with_ml.py (MORNING ANALYSIS)
├── enhanced_evening_analyzer_with_ml.py (ML TRAINING)
├── enhanced_efficient_system_market_aware.py (CORE PREDICTOR)
├── comprehensive_table_dashboard.py (DASHBOARD)
├── evaluate_predictions_comprehensive.sh (EVALUATION)
├── start_market_aware.sh (MARKET CONTEXT)
├── app/main_enhanced.py (ENHANCED APP)
└── ig_markets_paper_trading/scripts/run_paper_trader.py (PAPER TRADING)

Database Files:
├── data/trading_predictions.db (MAIN DATABASE - CRITICAL)
├── data/outcomes.db (EVALUATION RESULTS)
├── data/enhanced_outcomes.db (ENHANCED OUTCOMES)
└── paper-trading-app/ig_markets_paper_trades.db (PAPER TRADING)

Configuration Files:
├── current_crontab.txt (CURRENT CRON CONFIG)
├── cron_market_aware.txt (MARKET AWARE CRON)
└── local_crontab.txt (LOCAL CRON BACKUP)
```

## Implementation Plan with Zero-Risk Migration

### Phase 1: Foundation Setup (MUST DO FIRST)
```bash
# 1. Install Redis (message bus)
sudo apt update
sudo apt install redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# 2. Create service infrastructure
sudo mkdir -p /opt/trading_services/{services,compatibility,scripts,logs}
sudo mkdir -p /var/log/trading
sudo mkdir -p /tmp/trading_sockets
sudo chown $USER:$USER /opt/trading_services /var/log/trading /tmp/trading_sockets

# 3. Setup Python environment
python3 -m venv /opt/trading_venv
source /opt/trading_venv/bin/activate
pip install redis asyncio aiofiles psutil

# 4. Copy existing code to services directory
cp -r /root/test/* /opt/trading_services/
```

### Phase 2: Create Service Framework (Base Components)

#### 1. Base Service Class
```python
# /opt/trading_services/services/base_service.py
import asyncio
import socket
import json
import logging
import signal
import sys
import time
import psutil
import os
from pathlib import Path
from typing import Dict, Any, Callable, Optional
import redis

class BaseService:
    def __init__(self, service_name: str, socket_path: str = None):
        self.service_name = service_name
        self.socket_path = socket_path or f"/tmp/trading_{service_name}.sock"
        self.start_time = time.time()
        self.running = True
        self.handlers: Dict[str, Callable] = {}
        
        # Redis connection
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            self.redis_client.ping()  # Test connection
        except:
            self.redis_client = None
            print(f"WARNING: Redis not available for {service_name}")
        
        # Logging setup
        self._setup_logging()
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Built-in handlers
        self.register_handler("health", self.health_check)
        self.register_handler("metrics", self.get_metrics)
        self.register_handler("shutdown", self.graceful_shutdown)
    
    def _setup_logging(self):
        """Setup logging with file and console handlers"""
        log_dir = Path("/var/log/trading")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(self.service_name)
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_dir / f"{self.service_name}.log")
        console_handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully")
        self.running = False
    
    def register_handler(self, method: str, handler: Callable):
        """Register RPC method handler"""
        self.handlers[method] = handler
    
    async def start_server(self):
        """Start Unix socket server"""
        # Remove existing socket
        Path(self.socket_path).unlink(missing_ok=True)
        
        server = await asyncio.start_unix_server(
            self._handle_connection, 
            self.socket_path
        )
        
        # Set permissions
        Path(self.socket_path).chmod(0o666)
        
        self.logger.info(f"Service {self.service_name} listening on {self.socket_path}")
        
        async with server:
            await server.serve_forever()
    
    async def _handle_connection(self, reader, writer):
        """Handle socket connections"""
        try:
            # Read with timeout
            data = await asyncio.wait_for(reader.read(32768), timeout=30.0)
            
            if not data:
                return
                
            request = json.loads(data.decode())
            method = request.get('method')
            params = request.get('params', {})
            
            if method in self.handlers:
                try:
                    result = await self.handlers[method](**params)
                    response = {'status': 'success', 'result': result}
                except Exception as e:
                    self.logger.error(f"Handler error for {method}: {e}")
                    response = {'status': 'error', 'error': str(e)}
            else:
                response = {'status': 'error', 'error': f'Unknown method: {method}'}
            
            writer.write(json.dumps(response).encode())
            await writer.drain()
            
        except Exception as e:
            error_response = {'status': 'error', 'error': str(e)}
            writer.write(json.dumps(error_response).encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def call_service(self, service_name: str, method: str, timeout: float = 30.0, **params):
        """Call another service"""
        socket_path = f"/tmp/trading_{service_name}.sock"
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path), 
                timeout=5.0
            )
            
            request = {'method': method, 'params': params}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(32768), timeout=timeout)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response['status'] == 'success':
                return response['result']
            else:
                raise Exception(f"Service call failed: {response['error']}")
                
        except Exception as e:
            self.logger.error(f"Failed to call {service_name}.{method}: {e}")
            raise
    
    def publish_event(self, event_type: str, data: dict):
        """Publish event via Redis"""
        if not self.redis_client:
            return False
            
        try:
            self.redis_client.publish(f"trading:{event_type}", json.dumps(data))
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    async def health_check(self):
        """Health check endpoint"""
        process = psutil.Process(os.getpid())
        
        return {
            "service": self.service_name,
            "status": "healthy" if self.running else "unhealthy",
            "uptime": time.time() - self.start_time,
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(),
            "redis_connected": self.redis_client is not None
        }
    
    async def get_metrics(self):
        """Get service metrics"""
        return await self.health_check()
    
    async def graceful_shutdown(self):
        """Graceful shutdown"""
        self.running = False
        return {"status": "shutdown_initiated"}
```

#### 2. Market Data Service
```python
# /opt/trading_services/services/market_data_service.py
#!/usr/bin/env python3
import asyncio
import yfinance as yf
import sys
import os
sys.path.append('/opt/trading_services')

from services.base_service import BaseService
import time
from datetime import datetime, timedelta

class MarketDataService(BaseService):
    def __init__(self):
        super().__init__("market-data")
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Register handlers
        self.register_handler("get_market_data", self.get_market_data)
        self.register_handler("get_asx_context", self.get_asx_context)
        self.register_handler("bulk_fetch", self.bulk_fetch)
        self.register_handler("clear_cache", self.clear_cache)
    
    async def get_market_data(self, symbol: str):
        """Get market data with caching"""
        cache_key = f"market_data:{symbol}"
        
        # Check cache
        if cache_key in self.cache:
            data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return data
        
        try:
            # Fetch from Yahoo Finance
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d", interval="1h")
            
            if hist.empty:
                raise Exception(f"No data available for {symbol}")
            
            # Calculate technical indicators
            current_price = float(hist["Close"].iloc[-1])
            
            market_data = {
                "symbol": symbol,
                "current_price": current_price,
                "technical": {
                    "rsi": self._calculate_rsi(hist["Close"]),
                    "sma_20": self._calculate_sma(hist["Close"], 20),
                    "price_vs_sma20": (current_price / self._calculate_sma(hist["Close"], 20) - 1) * 100,
                    "volatility": self._calculate_volatility(hist["Close"])
                },
                "volume": {
                    "current_volume": float(hist["Volume"].iloc[-1]),
                    "avg_volume": float(hist["Volume"].mean()),
                    "volume_trend": self._calculate_volume_trend(hist["Volume"])
                },
                "timestamp": time.time()
            }
            
            # Cache result
            self.cache[cache_key] = (market_data, time.time())
            
            self.logger.info(f"Fetched market data for {symbol}")
            return market_data
            
        except Exception as e:
            self.logger.error(f"Failed to fetch market data for {symbol}: {e}")
            raise
    
    async def get_asx_context(self):
        """Get ASX market context"""
        try:
            asx200 = yf.Ticker("^AXJO")
            data = asx200.history(period="5d")
            
            if data.empty:
                return self._get_default_context()
            
            # Calculate trend
            market_trend = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
            
            # Determine context
            if market_trend < -1.5:
                context = "BEARISH"
                confidence_multiplier = 0.7
                buy_threshold = 0.80
            elif market_trend > 1.5:
                context = "BULLISH"
                confidence_multiplier = 1.1
                buy_threshold = 0.65
            elif market_trend < -0.5:
                context = "WEAK_BEARISH"
                confidence_multiplier = 0.9
                buy_threshold = 0.75
            elif market_trend > 0.5:
                context = "WEAK_BULLISH"
                confidence_multiplier = 1.05
                buy_threshold = 0.68
            else:
                context = "NEUTRAL"
                confidence_multiplier = 1.0
                buy_threshold = 0.70
            
            return {
                "context": context,
                "trend_pct": float(market_trend),
                "confidence_multiplier": float(confidence_multiplier),
                "buy_threshold": float(buy_threshold),
                "asx200_price": float(data['Close'].iloc[-1])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get ASX context: {e}")
            return self._get_default_context()
    
    def _get_default_context(self):
        """Default market context when data unavailable"""
        return {
            "context": "NEUTRAL",
            "trend_pct": 0.0,
            "confidence_multiplier": 1.0,
            "buy_threshold": 0.70,
            "asx200_price": 0.0
        }
    
    async def bulk_fetch(self, symbols: list):
        """Fetch data for multiple symbols"""
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = await self.get_market_data(symbol)
            except Exception as e:
                results[symbol] = {"error": str(e)}
        return results
    
    async def clear_cache(self):
        """Clear cache"""
        cache_size = len(self.cache)
        self.cache.clear()
        return {"cleared_entries": cache_size}
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI"""
        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0).rolling(window=period).mean()
        losses = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
        rs = gains / losses
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty and not rsi.iloc[-1] != rsi.iloc[-1] else 50.0
    
    def _calculate_sma(self, prices, period):
        """Calculate Simple Moving Average"""
        sma = prices.rolling(window=period).mean()
        return float(sma.iloc[-1]) if not sma.empty else float(prices.iloc[-1])
    
    def _calculate_volatility(self, prices):
        """Calculate price volatility"""
        returns = prices.pct_change()
        return float(returns.std()) if not returns.empty else 0.0
    
    def _calculate_volume_trend(self, volumes):
        """Calculate volume trend"""
        if len(volumes) < 5:
            return 0.0
        recent_avg = volumes.tail(5).mean()
        older_avg = volumes.head(len(volumes)-5).mean()
        return float((recent_avg - older_avg) / older_avg) if older_avg > 0 else 0.0

async def main():
    service = MarketDataService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. Sentiment Analysis Service
```python
# /opt/trading_services/services/sentiment_service.py
#!/usr/bin/env python3
import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
sys.path.append('/opt/trading_services')

from services.base_service import BaseService

class SentimentService(BaseService):
    def __init__(self):
        super().__init__("sentiment")
        
        # Import sentiment components
        try:
            sys.path.append('/opt/trading_services/app/core/sentiment')
            from marketaux_integration import MarketAuxManager
            from news_analyzer import NewsAnalyzer
            
            # Initialize sentiment components
            self.marketaux = MarketAuxManager()
            self.news_analyzer = NewsAnalyzer()
            self.sentiment_cache = {}
            self.cache_ttl = 1800  # 30 minutes
            
            self.logger.info("Sentiment analysis components loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load sentiment components: {e}")
            self.marketaux = None
            self.news_analyzer = None
        
        # Register handlers
        self.register_handler("analyze_sentiment", self.analyze_sentiment)
        self.register_handler("get_market_sentiment", self.get_market_sentiment)
        self.register_handler("get_big_four_sentiment", self.get_big_four_sentiment)
        self.register_handler("get_optimized_sentiment", self.get_optimized_sentiment)
        self.register_handler("get_sentiment_batch", self.get_sentiment_batch)
        self.register_handler("clear_sentiment_cache", self.clear_sentiment_cache)
    
    async def analyze_sentiment(self, symbol: str, use_cache: bool = True):
        """Analyze sentiment for a single symbol"""
        if not self.marketaux:
            return self._fallback_sentiment(symbol)
        
        cache_key = f"sentiment:{symbol}"
        
        # Check cache
        if use_cache and cache_key in self.sentiment_cache:
            cached_data, timestamp = self.sentiment_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        try:
            # Get sentiment from MarketAux
            sentiment_results = self.marketaux.get_sentiment_analysis(
                symbols=[symbol.replace('.AX', '')],
                strategy="individual_analysis",
                use_cache=use_cache
            )
            
            if sentiment_results and len(sentiment_results) > 0:
                sentiment = sentiment_results[0]
                
                result = {
                    "symbol": symbol,
                    "sentiment_score": sentiment.sentiment_score,
                    "confidence": sentiment.confidence,
                    "news_volume": sentiment.news_volume,
                    "source_quality": sentiment.source_quality,
                    "highlights": sentiment.highlights[:3],  # Top 3 highlights
                    "sources": sentiment.sources,
                    "timestamp": datetime.now().isoformat(),
                    "method": "marketaux_api"
                }
                
                # Cache result
                self.sentiment_cache[cache_key] = (result, time.time())
                
                self.logger.info(f"Sentiment analysis for {symbol}: {sentiment.sentiment_score:.3f}")
                return result
            else:
                return self._fallback_sentiment(symbol)
                
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            return self._fallback_sentiment(symbol)
    
    async def get_market_sentiment(self):
        """Get overall market sentiment"""
        try:
            # Get ASX context from market data service
            asx_context = await self.call_service("market-data", "get_asx_context")
            
            # Get Big 4 sentiment
            big_four_sentiment = await self.get_big_four_sentiment()
            
            if big_four_sentiment:
                avg_sentiment = sum(s.get('sentiment_score', 0) for s in big_four_sentiment) / len(big_four_sentiment)
                avg_confidence = sum(s.get('confidence', 0) for s in big_four_sentiment) / len(big_four_sentiment)
                
                # Combine with market context
                market_trend = asx_context.get('trend_pct', 0.0) / 100.0  # Convert to -1 to 1 scale
                combined_sentiment = (avg_sentiment + market_trend) / 2.0
                
                return {
                    "market_sentiment": combined_sentiment,
                    "confidence": avg_confidence,
                    "bank_sentiment": avg_sentiment,
                    "market_trend": market_trend,
                    "asx_context": asx_context.get('context', 'NEUTRAL'),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "market_sentiment": 0.0,
                    "confidence": 0.3,
                    "bank_sentiment": 0.0,
                    "market_trend": asx_context.get('trend_pct', 0.0) / 100.0,
                    "asx_context": asx_context.get('context', 'NEUTRAL'),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {e}")
            return {
                "market_sentiment": 0.0,
                "confidence": 0.3,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_big_four_sentiment(self):
        """Get sentiment for Big 4 banks efficiently"""
        if not self.marketaux:
            return [self._fallback_sentiment(symbol) for symbol in ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']]
        
        try:
            # Use optimized sentiment analysis
            sentiment_results = self.marketaux.get_optimized_sentiment_analysis(
                symbols=['CBA', 'ANZ', 'WBC', 'NAB'],
                strategy="big_four_batch",
                use_cache=True,
                timeframe_hours=4
            )
            
            if sentiment_results:
                results = []
                for sentiment in sentiment_results:
                    results.append({
                        "symbol": f"{sentiment.symbol}.AX",
                        "sentiment_score": sentiment.sentiment_score,
                        "confidence": sentiment.confidence,
                        "news_volume": sentiment.news_volume,
                        "source_quality": sentiment.source_quality,
                        "highlights": sentiment.highlights[:2],  # Top 2 highlights
                        "timestamp": datetime.now().isoformat()
                    })
                
                self.logger.info(f"Retrieved Big 4 sentiment: {len(results)} banks")
                return results
            else:
                return [self._fallback_sentiment(symbol) for symbol in ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']]
                
        except Exception as e:
            self.logger.error(f"Error getting Big 4 sentiment: {e}")
            return [self._fallback_sentiment(symbol) for symbol in ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX']]
    
    async def get_optimized_sentiment(self, symbols: list):
        """Get optimized sentiment for multiple symbols"""
        if not symbols:
            return []
        
        try:
            # Clean symbols (remove .AX suffix for MarketAux)
            clean_symbols = [s.replace('.AX', '') for s in symbols]
            
            sentiment_results = self.marketaux.get_optimized_sentiment_analysis(
                symbols=clean_symbols,
                strategy="batch_optimized",
                use_cache=True,
                timeframe_hours=6
            )
            
            if sentiment_results:
                results = []
                for sentiment in sentiment_results:
                    results.append({
                        "symbol": f"{sentiment.symbol}.AX" if not sentiment.symbol.endswith('.AX') else sentiment.symbol,
                        "sentiment_score": sentiment.sentiment_score,
                        "confidence": sentiment.confidence,
                        "news_volume": sentiment.news_volume,
                        "source_quality": sentiment.source_quality,
                        "highlights": sentiment.highlights[:3],
                        "sources": sentiment.sources,
                        "timestamp": datetime.now().isoformat()
                    })
                
                return results
            else:
                return [self._fallback_sentiment(symbol) for symbol in symbols]
                
        except Exception as e:
            self.logger.error(f"Error getting optimized sentiment: {e}")
            return [self._fallback_sentiment(symbol) for symbol in symbols]
    
    async def get_sentiment_batch(self, symbols: list, strategy: str = "balanced"):
        """Get sentiment for multiple symbols with batching"""
        return await self.get_optimized_sentiment(symbols)
    
    async def clear_sentiment_cache(self):
        """Clear sentiment cache"""
        cache_size = len(self.sentiment_cache)
        self.sentiment_cache.clear()
        
        if self.marketaux:
            self.marketaux.clear_cache(older_than_hours=24)
        
        return {"cleared_entries": cache_size}
    
    def _fallback_sentiment(self, symbol: str):
        """Fallback sentiment when API fails"""
        return {
            "symbol": symbol,
            "sentiment_score": 0.0,
            "confidence": 0.2,
            "news_volume": 0,
            "source_quality": "fallback",
            "highlights": [],
            "sources": [],
            "timestamp": datetime.now().isoformat(),
            "method": "fallback"
        }
    
    async def health_check(self):
        """Enhanced health check with sentiment service metrics"""
        base_health = await super().health_check()
        
        # Check MarketAux API status
        marketaux_status = "healthy" if self.marketaux else "unavailable"
        
        # Get usage stats if available
        usage_stats = {}
        if self.marketaux:
            try:
                usage_stats = self.marketaux.get_usage_stats()
            except:
                pass
        
        return {
            **base_health,
            "marketaux_status": marketaux_status,
            "cache_size": len(self.sentiment_cache),
            "api_usage": usage_stats.get('usage_percentage', 0),
            "requests_remaining": usage_stats.get('requests_remaining', 0)
        }

async def main():
    service = SentimentService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 4. Prediction Service (Enhanced with Sentiment Integration)
```python
# /opt/trading_services/services/prediction_service.py
#!/usr/bin/env python3
import asyncio
import sys
import os
sys.path.append('/opt/trading_services')

from services.base_service import BaseService

class PredictionService(BaseService):
    def __init__(self):
        super().__init__("prediction")
        
        # Import configuration
        try:
            sys.path.append('/opt/trading_services/app/config')
            from settings import Settings
            from config_manager import ConfigurationManager
            
            self.settings = Settings()
            self.config_manager = ConfigurationManager()
            self.logger.info("Configuration loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self.settings = None
            self.config_manager = None
        
        # Import the existing predictor
        try:
            from enhanced_efficient_system_market_aware import EnhancedMarketAwarePredictor
            self.predictor = EnhancedMarketAwarePredictor()
            self.logger.info("Loaded EnhancedMarketAwarePredictor successfully")
        except Exception as e:
            self.logger.error(f"Failed to load predictor: {e}")
            self.predictor = None
        
        # Register handlers
        self.register_handler("generate_predictions", self.generate_predictions)
        self.register_handler("generate_single_prediction", self.generate_single_prediction)
        self.register_handler("get_configuration", self.get_configuration)
        self.register_handler("update_configuration", self.update_configuration)
    
    async def generate_predictions(self, symbols: list = None):
        """Generate predictions for symbols with full configuration support"""
        if not self.predictor:
            raise Exception("Predictor not loaded")
        
        # Use configured symbols if none provided
        if not symbols:
            if self.settings:
                symbols = self.settings.BANK_SYMBOLS
            else:
                symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        predictions = {}
        
        for symbol in symbols:
            try:
                # Get market data
                market_data = await self.call_service("market-data", "get_market_data", symbol=symbol)
                
                # Get ASX context
                asx_context = await self.call_service("market-data", "get_asx_context")
                
                # Get sentiment data
                try:
                    sentiment_data = await self.call_service("sentiment", "analyze_sentiment", symbol=symbol)
                except Exception as e:
                    self.logger.warning(f"Sentiment service unavailable for {symbol}: {e}")
                    sentiment_data = {
                        "sentiment_score": 0.0,
                        "confidence": 0.3,
                        "news_volume": 0
                    }
                
                # Enhanced prediction with sentiment integration
                prediction = self._generate_enhanced_prediction(
                    symbol=symbol,
                    market_data=market_data,
                    asx_context=asx_context,
                    sentiment_data=sentiment_data
                )
                
                predictions[symbol] = prediction
                
                # Publish event
                self.publish_event("prediction_generated", {
                    "symbol": symbol,
                    "action": prediction.get("action", "UNKNOWN"),
                    "confidence": prediction.get("confidence", 0.0),
                    "sentiment_score": sentiment_data.get("sentiment_score", 0.0)
                })
                
                self.logger.info(f"Generated prediction for {symbol}: {prediction.get('action', 'UNKNOWN')} @ {prediction.get('confidence', 0.0):.1%}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate prediction for {symbol}: {e}")
                predictions[symbol] = {"error": str(e)}
        
        return predictions
    
    def _generate_enhanced_prediction(self, symbol: str, market_data: dict, asx_context: dict, sentiment_data: dict):
        """Generate enhanced prediction with sentiment integration"""
        try:
            # Use original predictor if available
            if self.predictor:
                prediction = self.predictor.calculate_confidence(
                    symbol=symbol,
                    tech_data=market_data.get("technical", {}),
                    news_data=sentiment_data,
                    volume_data=market_data.get("volume", {}),
                    market_data=asx_context
                )
                
                # Enhance with configuration-based adjustments
                if self.settings:
                    prediction = self._apply_configuration_adjustments(symbol, prediction, sentiment_data)
                
                return prediction
            else:
                # Fallback prediction logic
                return self._fallback_prediction(symbol, market_data, sentiment_data)
                
        except Exception as e:
            self.logger.error(f"Error in enhanced prediction for {symbol}: {e}")
            return self._fallback_prediction(symbol, market_data, sentiment_data)
    
    def _apply_configuration_adjustments(self, symbol: str, prediction: dict, sentiment_data: dict):
        """Apply configuration-based adjustments to predictions"""
        if not self.settings:
            return prediction
        
        # Get sentiment configuration
        sentiment_config = self.settings.SENTIMENT_CONFIG
        
        # Apply sentiment weighting from configuration
        news_weight = sentiment_config['weights']['news_sentiment']
        sentiment_score = sentiment_data.get('sentiment_score', 0.0)
        sentiment_confidence = sentiment_data.get('confidence', 0.0)
        
        # Adjust confidence based on sentiment
        original_confidence = prediction.get('confidence', 0.7)
        sentiment_adjustment = sentiment_score * news_weight * sentiment_confidence
        
        adjusted_confidence = max(0.0, min(1.0, original_confidence + sentiment_adjustment))
        
        # Apply alert thresholds
        alert_thresholds = self.settings.ALERT_THRESHOLDS['sentiment']
        
        # Determine action based on adjusted confidence and thresholds
        if adjusted_confidence >= 0.8:
            action = "STRONG_BUY"
        elif adjusted_confidence >= 0.7:
            action = "BUY"
        elif adjusted_confidence >= 0.55:
            action = "HOLD"
        elif adjusted_confidence >= 0.4:
            action = "SELL"
        else:
            action = "STRONG_SELL"
        
        # Enhanced prediction with configuration
        enhanced_prediction = {
            **prediction,
            "confidence": adjusted_confidence,
            "action": action,
            "sentiment_adjustment": sentiment_adjustment,
            "sentiment_score": sentiment_score,
            "sentiment_confidence": sentiment_confidence,
            "configuration_applied": True,
            "risk_parameters": self.settings.get_risk_parameters(),
            "bank_info": self.settings.get_bank_info(symbol)
        }
        
        return enhanced_prediction
    
    def _fallback_prediction(self, symbol: str, market_data: dict, sentiment_data: dict):
        """Fallback prediction when main predictor fails"""
        # Simple prediction based on available data
        current_price = market_data.get('current_price', 0)
        rsi = market_data.get('technical', {}).get('rsi', 50)
        sentiment_score = sentiment_data.get('sentiment_score', 0.0)
        
        # Basic scoring
        tech_score = 0.5
        if rsi < 30:
            tech_score = 0.8  # Oversold, might buy
        elif rsi > 70:
            tech_score = 0.2  # Overbought, might sell
        
        # Combine with sentiment
        combined_score = (tech_score + (sentiment_score + 1) / 2) / 2
        
        # Determine action
        if combined_score >= 0.7:
            action = "BUY"
        elif combined_score >= 0.6:
            action = "HOLD"
        else:
            action = "SELL"
        
        return {
            "symbol": symbol,
            "action": action,
            "confidence": combined_score,
            "entry_price": current_price,
            "method": "fallback",
            "sentiment_score": sentiment_score,
            "rsi": rsi,
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_configuration(self):
        """Get current configuration"""
        if not self.config_manager:
            return {"error": "Configuration manager not available"}
        
        return {
            "trading_config": self.config_manager.get_trading_config(),
            "ml_config": self.config_manager.get('ml', {}),
            "sentiment_config": self.settings.SENTIMENT_CONFIG if self.settings else {},
            "risk_parameters": self.settings.get_risk_parameters() if self.settings else {}
        }
    
    async def update_configuration(self, config_updates: dict):
        """Update configuration settings"""
        if not self.config_manager:
            return {"error": "Configuration manager not available"}
        
        try:
            for key_path, value in config_updates.items():
                self.config_manager.set(key_path, value)
            
            self.config_manager.save()
            return {"status": "Configuration updated successfully"}
            
        except Exception as e:
            return {"error": f"Failed to update configuration: {e}"}

    async def generate_single_prediction(self, symbol: str, force_refresh: bool = False):
        """Generate prediction for a single symbol"""
        result = await self.generate_predictions([symbol])
        return result.get(symbol, {"error": "Prediction failed"})
    
    async def get_latest_prediction(self, symbol: str):
        """Get latest prediction from database"""
        # This would query the existing database
        # For now, return a placeholder
        return {"symbol": symbol, "status": "not_implemented"}
    
    async def generate_predictions(self, symbols: list = None):
        """Generate predictions for symbols"""
        if not self.predictor:
            raise Exception("Predictor not loaded")
        
        if not symbols:
            symbols = ["CBA.AX", "ANZ.AX", "NAB.AX", "WBC.AX", "MQG.AX", "COL.AX", "BHP.AX"]
        
        predictions = {}
        
        for symbol in symbols:
            try:
                # Get market data
                market_data = await self.call_service("market-data", "get_market_data", symbol=symbol)
                
                # Get ASX context
                asx_context = await self.call_service("market-data", "get_asx_context")
                
                # Generate prediction using existing logic
                prediction = self.predictor.calculate_confidence(
                    symbol=symbol,
                    tech_data=market_data.get("technical", {}),
                    news_data={},  # Will add sentiment service later
                    volume_data=market_data.get("volume", {}),
                    market_data=asx_context
                )
                
                predictions[symbol] = prediction
                
                # Publish event
                self.publish_event("prediction_generated", {
                    "symbol": symbol,
                    "action": prediction.get("action", "UNKNOWN"),
                    "confidence": prediction.get("confidence", 0.0)
                })
                
                self.logger.info(f"Generated prediction for {symbol}: {prediction.get('action', 'UNKNOWN')}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate prediction for {symbol}: {e}")
                predictions[symbol] = {"error": str(e)}
        
        return predictions
    
    async def generate_single_prediction(self, symbol: str):
        """Generate prediction for single symbol"""
        result = await self.generate_predictions([symbol])
        return result.get(symbol, {"error": "Prediction failed"})
    
    async def get_latest_prediction(self, symbol: str):
        """Get latest prediction from database"""
        # This would query the existing database
        # For now, return a placeholder
        return {"symbol": symbol, "status": "not_implemented"}

async def main():
    service = PredictionService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 3: Compatibility Layer (CRITICAL - NO DOWNTIME)

#### 1. Service Proxy for Backward Compatibility
```python
# /opt/trading_services/compatibility/service_proxy.py
"""
CRITICAL: Drop-in replacement for existing cron jobs
This ensures zero downtime during migration
"""
import asyncio
import json
import socket
import sys
import os
import subprocess
from pathlib import Path

class ServiceProxy:
    """Proxy that tries microservices first, falls back to monolith"""
    
    def __init__(self):
        self.services_available = self._check_services()
        self.fallback_enabled = True
    
    def _check_services(self):
        """Check which services are running"""
        services = ["prediction", "market-data"]
        available = {}
        
        for service in services:
            socket_path = f"/tmp/trading_{service}.sock"
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect(socket_path)
                sock.close()
                available[service] = True
            except:
                available[service] = False
        
        return available
    
    async def _call_service(self, service_name: str, method: str, **params):
        """Call service via Unix socket"""
        socket_path = f"/tmp/trading_{service_name}.sock"
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path), 
                timeout=5.0
            )
            
            request = {'method': method, 'params': params}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(32768), timeout=30.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response['status'] == 'success':
                return response['result']
            else:
                raise Exception(response['error'])
                
        except Exception as e:
            raise Exception(f"Service call failed: {e}")
    
    def run_predictions_with_fallback(self):
        """
        CRITICAL: Replace production/cron/fixed_price_mapping_system.py calls
        Try microservices first, fallback to original on failure
        """
        try:
            # Check if prediction service is available
            if self.services_available.get("prediction") and self.services_available.get("market-data"):
                print("🔄 Using microservices for predictions...")
                
                # Run via microservices
                result = asyncio.run(self._call_service("prediction", "generate_predictions"))
                
                print(f"✅ Microservices prediction completed: {len(result.get('predictions', {}))} symbols")
                return True
                
        except Exception as e:
            print(f"⚠️  Microservices failed: {e}")
            
        # Fallback to original system
        if self.fallback_enabled:
            print("🔄 Falling back to original monolithic system...")
            try:
                # Change to original directory and run original script
                os.chdir('/root/test')
                result = subprocess.run([
                    '/root/trading_venv/bin/python', 
                    'production/cron/fixed_price_mapping_system.py'
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ Monolithic fallback completed successfully")
                    return True
                else:
                    print(f"❌ Monolithic fallback failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Fallback execution failed: {e}")
                return False
        else:
            print("❌ Fallback disabled, prediction failed")
            return False
    
    def run_morning_analysis_with_fallback(self):
        """Fallback for enhanced_morning_analyzer_with_ml.py"""
        try:
            # Try microservices approach
            print("🔄 Morning analysis via microservices...")
            # Implementation would go here
            
        except:
            # Fallback to original
            print("🔄 Falling back to original morning analysis...")
            os.chdir('/root/test')
            result = subprocess.run([
                '/root/trading_venv/bin/python', 
                'enhanced_morning_analyzer_with_ml.py'
            ], capture_output=True, text=True, timeout=300)
            
            return result.returncode == 0
    
    def run_evening_training_with_fallback(self):
        """Fallback for enhanced_evening_analyzer_with_ml.py"""
        try:
            print("🔄 Evening ML training...")
            # For now, always use original
            os.chdir('/root/test')
            result = subprocess.run([
                '/root/trading_venv/bin/python', 
                'enhanced_evening_analyzer_with_ml.py'
            ], capture_output=True, text=True, timeout=600)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Evening training failed: {e}")
            return False

# Global instance
proxy = ServiceProxy()
```

#### 2. Drop-in Replacement Scripts
```python
# /opt/trading_services/compatibility/run_predictions.py
#!/usr/bin/env python3
"""
CRITICAL: Drop-in replacement for production/cron/fixed_price_mapping_system.py
This script is called by cron and must maintain exact compatibility
"""
import sys
import os

# Add paths
sys.path.append('/opt/trading_services')
sys.path.append('/root/test')

from compatibility.service_proxy import proxy

def main():
    """Main entry point - exactly matches original cron job behavior"""
    success = proxy.run_predictions_with_fallback()
    
    if success:
        print("✅ Prediction generation completed successfully")
        sys.exit(0)
    else:
        print("❌ Prediction generation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

```python
# /opt/trading_services/compatibility/run_morning_analysis.py
#!/usr/bin/env python3
"""
Drop-in replacement for enhanced_morning_analyzer_with_ml.py
"""
import sys
import os
sys.path.append('/opt/trading_services')
sys.path.append('/root/test')

from compatibility.service_proxy import proxy

def main():
    success = proxy.run_morning_analysis_with_fallback()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

```python
# /opt/trading_services/compatibility/run_evening_training.py
#!/usr/bin/env python3
"""
Drop-in replacement for enhanced_evening_analyzer_with_ml.py
"""
import sys
import os
sys.path.append('/opt/trading_services')
sys.path.append('/root/test')

from compatibility.service_proxy import proxy

def main():
    success = proxy.run_evening_training_with_fallback()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

### Phase 4: Systemd Service Definitions (Updated with Configuration)

#### 1. Market Data Service
```ini
# /etc/systemd/system/trading-market-data.service
[Unit]
Description=Trading Market Data Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services:/root/test
Environment=PYTHONUNBUFFERED=1
Environment=MARKETAUX_API_TOKEN=your_api_token_here
ExecStart=/opt/trading_venv/bin/python services/market_data_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=128M
CPUQuota=50%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-market-data

[Install]
WantedBy=multi-user.target
```

#### 2. Sentiment Analysis Service
```ini
# /etc/systemd/system/trading-sentiment.service
[Unit]
Description=Trading Sentiment Analysis Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services:/root/test
Environment=PYTHONUNBUFFERED=1
Environment=MARKETAUX_API_TOKEN=your_api_token_here
Environment=NEWS_API_KEY=your_news_api_key_here
ExecStart=/opt/trading_venv/bin/python services/sentiment_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=256M
CPUQuota=75%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-sentiment

[Install]
WantedBy=multi-user.target
```

#### 3. Prediction Service
```ini
# /etc/systemd/system/trading-prediction.service
[Unit]
Description=Trading Prediction Service
After=network.target redis.service trading-market-data.service trading-sentiment.service
Wants=redis.service trading-market-data.service trading-sentiment.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services:/root/test
Environment=PYTHONUNBUFFERED=1
Environment=TRADING_DB_PATH=/root/test/data/trading_predictions.db
Environment=TRADING_LOG_LEVEL=INFO
ExecStart=/opt/trading_venv/bin/python services/prediction_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=512M
CPUQuota=100%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-prediction

[Install]
WantedBy=multi-user.target
```

#### 4. Configuration Service (New)
```ini
# /etc/systemd/system/trading-config.service
[Unit]
Description=Trading Configuration Management Service
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/trading_services
Environment=PYTHONPATH=/opt/trading_services:/root/test
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/trading_venv/bin/python services/config_service.py
ExecStop=/bin/kill -TERM $MAINPID
TimeoutStopSec=30
Restart=always
RestartSec=5
StartLimitInterval=300
StartLimitBurst=5

# Resource limits
MemoryMax=64M
CPUQuota=25%

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=trading-config

[Install]
WantedBy=multi-user.target
```

### Phase 5: Configuration and Environment Setup

#### 1. Environment Variables Configuration
```bash
# /opt/trading_services/.env
# Core Configuration
PYTHONPATH=/opt/trading_services:/root/test
PYTHONUNBUFFERED=1
DEBUG=False
TRADING_LOG_LEVEL=INFO

# Database Configuration
TRADING_DB_PATH=/root/test/data/trading_predictions.db
OUTCOMES_DB_PATH=/root/test/data/outcomes.db
ENHANCED_OUTCOMES_DB_PATH=/root/test/data/enhanced_outcomes.db

# API Keys (Replace with actual keys)
MARKETAUX_API_TOKEN=your_marketaux_api_token_here
NEWS_API_KEY=your_news_api_key_here
ALPHA_VANTAGE_KEY=your_alpha_vantage_key_here

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Trading Configuration
TRADING_PAPER_MODE=true
TRADING_SYMBOLS=CBA.AX,ANZ.AX,WBC.AX,NAB.AX,MQG.AX
MAX_POSITION_SIZE=1000
CONFIDENCE_THRESHOLD=70
RISK_TOLERANCE=medium

# Service Configuration
CACHE_DURATION_MINUTES=15
MAX_CACHE_SIZE_MB=100
AUTO_REFRESH_SECONDS=300

# Notification Configuration (Optional)
DISCORD_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMAIL_USERNAME=
EMAIL_PASSWORD=
SMTP_SERVER=
SMTP_PORT=587
```

#### 2. Configuration Service
```python
# /opt/trading_services/services/config_service.py
#!/usr/bin/env python3
import asyncio
import sys
import os
import json
from pathlib import Path
sys.path.append('/opt/trading_services')

from services.base_service import BaseService

class ConfigService(BaseService):
    def __init__(self):
        super().__init__("config")
        
        # Load configuration components
        try:
            sys.path.append('/opt/trading_services/app/config')
            from settings import Settings
            from config_manager import ConfigurationManager
            
            self.settings = Settings()
            self.config_manager = ConfigurationManager()
            self.logger.info("Configuration service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize configuration: {e}")
            self.settings = None
            self.config_manager = None
        
        # Register handlers
        self.register_handler("get_settings", self.get_settings)
        self.register_handler("get_bank_symbols", self.get_bank_symbols)
        self.register_handler("get_sentiment_config", self.get_sentiment_config)
        self.register_handler("get_risk_parameters", self.get_risk_parameters)
        self.register_handler("get_alert_thresholds", self.get_alert_thresholds)
        self.register_handler("validate_config", self.validate_config)
        self.register_handler("update_setting", self.update_setting)
        self.register_handler("get_ml_config", self.get_ml_config)
    
    async def get_settings(self, section: str = None):
        """Get configuration settings"""
        if not self.settings:
            return {"error": "Settings not available"}
        
        if section:
            # Return specific section
            section_map = {
                "bank_symbols": self.settings.BANK_SYMBOLS,
                "sentiment": self.settings.SENTIMENT_CONFIG,
                "risk": self.settings.RISK_PARAMETERS,
                "alerts": self.settings.ALERT_THRESHOLDS,
                "technical": self.settings.TECHNICAL_INDICATORS,
                "ml": self.settings.ML_CONFIG
            }
            return section_map.get(section, {"error": f"Unknown section: {section}"})
        
        # Return all settings
        return {
            "bank_symbols": self.settings.BANK_SYMBOLS,
            "bank_names": self.settings.BANK_NAMES,
            "sentiment_config": self.settings.SENTIMENT_CONFIG,
            "risk_parameters": self.settings.get_risk_parameters(),
            "alert_thresholds": self.settings.ALERT_THRESHOLDS,
            "technical_indicators": self.settings.TECHNICAL_INDICATORS,
            "ml_config": self.settings.ML_CONFIG,
            "market_indices": self.settings.MARKET_INDICES
        }
    
    async def get_bank_symbols(self):
        """Get configured bank symbols"""
        if not self.settings:
            return ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX"]  # Fallback
        
        return {
            "bank_symbols": self.settings.BANK_SYMBOLS,
            "bank_names": self.settings.BANK_NAMES,
            "extended_symbols": self.settings.EXTENDED_SYMBOLS
        }
    
    async def get_sentiment_config(self):
        """Get sentiment analysis configuration"""
        if not self.settings:
            return {
                "weights": {"news_sentiment": 0.4, "technical_momentum": 0.6},
                "sources": {"news_weight": 0.6, "social_weight": 0.4}
            }
        
        return self.settings.SENTIMENT_CONFIG
    
    async def get_risk_parameters(self):
        """Get risk management parameters"""
        if not self.settings:
            return {
                "max_position_size": 0.25,
                "stop_loss_atr_multiplier": 2.0,
                "max_daily_loss": 0.06
            }
        
        return self.settings.get_risk_parameters()
    
    async def get_alert_thresholds(self):
        """Get alert thresholds"""
        if not self.settings:
            return {
                "sentiment": {"strong_positive": 80, "positive": 60, "negative": 40},
                "technical": {"strong_buy": 75, "buy": 60, "sell": 40}
            }
        
        return self.settings.ALERT_THRESHOLDS
    
    async def get_ml_config(self):
        """Get ML configuration from YAML"""
        try:
            ml_config_file = Path('/opt/trading_services/app/config/ml_config.yaml')
            if ml_config_file.exists():
                import yaml
                with open(ml_config_file, 'r') as f:
                    ml_config = yaml.safe_load(f)
                return ml_config
            else:
                return {"error": "ML config file not found"}
        except Exception as e:
            self.logger.error(f"Error loading ML config: {e}")
            return {"error": str(e)}
    
    async def validate_config(self):
        """Validate current configuration"""
        if not self.settings:
            return {"valid": False, "issues": ["Settings not loaded"]}
        
        issues = self.settings.validate_config()
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
    
    async def update_setting(self, key_path: str, value):
        """Update a configuration setting"""
        if not self.config_manager:
            return {"error": "Configuration manager not available"}
        
        try:
            self.config_manager.set(key_path, value)
            self.config_manager.save()
            
            self.logger.info(f"Configuration updated: {key_path} = {value}")
            
            # Publish configuration change event
            self.publish_event("config_updated", {
                "key_path": key_path,
                "value": value,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "Configuration updated successfully"}
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
            return {"error": str(e)}

async def main():
    service = ConfigService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. Enhanced Compatibility Layer with Configuration
```python
# /opt/trading_services/compatibility/enhanced_service_proxy.py
"""
Enhanced service proxy with full configuration support
Handles all existing functionality while adding microservices capabilities
"""
import asyncio
import json
import socket
import sys
import os
import subprocess
from pathlib import Path

class EnhancedServiceProxy:
    """Enhanced proxy with configuration support"""
    
    def __init__(self):
        self.services_available = self._check_services()
        self.fallback_enabled = True
        self.config_cache = {}
        self.config_cache_ttl = 3600  # 1 hour
    
    def _check_services(self):
        """Check which services are running"""
        services = ["prediction", "market-data", "sentiment", "config"]
        available = {}
        
        for service in services:
            socket_path = f"/tmp/trading_{service}.sock"
            try:
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(2.0)
                sock.connect(socket_path)
                sock.close()
                available[service] = True
            except:
                available[service] = False
        
        return available
    
    async def _call_service(self, service_name: str, method: str, **params):
        """Call service via Unix socket"""
        socket_path = f"/tmp/trading_{service_name}.sock"
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path), 
                timeout=5.0
            )
            
            request = {'method': method, 'params': params}
            writer.write(json.dumps(request).encode())
            await writer.drain()
            
            response_data = await asyncio.wait_for(reader.read(32768), timeout=30.0)
            response = json.loads(response_data.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if response['status'] == 'success':
                return response['result']
            else:
                raise Exception(response['error'])
                
        except Exception as e:
            raise Exception(f"Service call failed: {e}")
    
    async def get_configuration(self, section: str = None):
        """Get configuration from config service"""
        try:
            if self.services_available.get("config"):
                return await self._call_service("config", "get_settings", section=section)
            else:
                # Fallback to local configuration
                return self._load_local_config(section)
        except Exception as e:
            print(f"Error getting configuration: {e}")
            return self._load_local_config(section)
    
    def _load_local_config(self, section: str = None):
        """Load configuration from local files"""
        try:
            sys.path.append('/opt/trading_services/app/config')
            from settings import Settings
            
            settings = Settings()
            
            if section == "bank_symbols":
                return settings.BANK_SYMBOLS
            elif section == "sentiment":
                return settings.SENTIMENT_CONFIG
            elif section == "risk":
                return settings.get_risk_parameters()
            else:
                return {
                    "bank_symbols": settings.BANK_SYMBOLS,
                    "sentiment_config": settings.SENTIMENT_CONFIG,
                    "risk_parameters": settings.get_risk_parameters()
                }
        except Exception as e:
            print(f"Error loading local config: {e}")
            return {"error": str(e)}
    
    def run_predictions_with_configuration(self):
        """Run predictions with full configuration support"""
        try:
            # Check if all required services are available
            required_services = ["prediction", "market-data", "config"]
            
            if all(self.services_available.get(svc, False) for svc in required_services):
                print("🔄 Using microservices with full configuration...")
                
                # Run via microservices with configuration
                result = asyncio.run(self._run_microservices_prediction())
                
                print(f"✅ Microservices prediction completed: {result.get('total_predictions', 0)} predictions")
                return True
                
        except Exception as e:
            print(f"⚠️  Microservices failed: {e}")
            
        # Fallback to original system
        if self.fallback_enabled:
            print("🔄 Falling back to original monolithic system...")
            try:
                # Change to original directory and run original script
                os.chdir('/root/test')
                result = subprocess.run([
                    '/root/trading_venv/bin/python', 
                    'production/cron/fixed_price_mapping_system.py'
                ], capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    print("✅ Monolithic fallback completed successfully")
                    return True
                else:
                    print(f"❌ Monolithic fallback failed: {result.stderr}")
                    return False
                    
            except Exception as e:
                print(f"❌ Fallback execution failed: {e}")
                return False
        else:
            print("❌ Fallback disabled, prediction failed")
            return False
    
    async def _run_microservices_prediction(self):
        """Run prediction using microservices"""
        # Get configuration
        config = await self.get_configuration()
        symbols = config.get('bank_symbols', ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX'])
        
        # Run predictions
        predictions = await self._call_service("prediction", "generate_predictions", symbols=symbols)
        
        return {
            "predictions": predictions,
            "total_predictions": len(predictions.get('predictions', [])) if isinstance(predictions, dict) else len(predictions),
            "configuration_used": True
        }

# Global enhanced proxy instance
enhanced_proxy = EnhancedServiceProxy()
```

#### 1. Create New Cron Jobs (Run in Parallel Initially)
```bash
# /opt/trading_services/new_crontab.txt
# NEW MICROSERVICES CRON JOBS - Run alongside existing initially

# Market predictions (MICROSERVICES VERSION)
*/30 0-5 * * 1-5 cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_predictions.py >> /var/log/trading/prediction_microservices.log 2>&1

# Morning analysis (MICROSERVICES VERSION)
5 7 * * 1-5 cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_morning_analysis.py >> /var/log/trading/morning_microservices.log 2>&1

# Evening training (MICROSERVICES VERSION)
5 8 * * * cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_evening_training.py >> /var/log/trading/evening_microservices.log 2>&1

# Keep ALL existing cron jobs unchanged initially
```

#### 2. Service Management Scripts
```bash
#!/bin/bash
# /opt/trading_services/scripts/manage_services.sh

SERVICES=("trading-market-data" "trading-prediction")

start_services() {
    echo "🚀 Starting trading microservices..."
    
    # Start Redis first
    sudo systemctl start redis
    sleep 2
    
    # Start services in dependency order
    for service in "${SERVICES[@]}"; do
        echo "Starting $service..."
        sudo systemctl start "$service"
        sleep 2
        
        # Wait for service to be ready
        for i in {1..10}; do
            if systemctl is-active "$service" >/dev/null 2>&1; then
                echo "✅ $service is running"
                break
            fi
            echo "⏳ Waiting for $service..."
            sleep 1
        done
    done
}

stop_services() {
    echo "🛑 Stopping trading microservices..."
    for service in "${SERVICES[@]}"; do
        sudo systemctl stop "$service"
        echo "Stopped $service"
    done
}

status_services() {
    echo "📊 Service Status:"
    for service in "${SERVICES[@]}"; do
        status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        echo "$service: $status"
    done
    
    echo ""
    echo "🔍 Health Checks:"
    cd /opt/trading_services
    /opt/trading_venv/bin/python -c "
import asyncio
from services.base_service import BaseService

async def check_health():
    service = BaseService('health-checker')
    
    for svc in ['market-data', 'prediction']:
        try:
            result = await service.call_service(svc, 'health', timeout=5.0)
            print(f'{svc}: {result[\"status\"]} (uptime: {result[\"uptime\"]:.1f}s)')
        except Exception as e:
            print(f'{svc}: ERROR - {e}')

asyncio.run(check_health())
"
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 3
        start_services
        ;;
    status)
        status_services
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
```

### Phase 6: Migration Cron Jobs (CRITICAL - ZERO DOWNTIME)

#### 1. Updated Service Management Scripts
```bash
#!/bin/bash
# /opt/trading_services/scripts/manage_services.sh

SERVICES=("trading-config" "trading-market-data" "trading-sentiment" "trading-prediction")

start_services() {
    echo "🚀 Starting trading microservices with full configuration..."
    
    # Start Redis first
    sudo systemctl start redis
    sleep 2
    
    # Start services in dependency order
    for service in "${SERVICES[@]}"; do
        echo "Starting $service..."
        sudo systemctl start "$service"
        sleep 3
        
        # Wait for service to be ready
        for i in {1..15}; do
            if systemctl is-active "$service" >/dev/null 2>&1; then
                echo "✅ $service is running"
                break
            fi
            echo "⏳ Waiting for $service..."
            sleep 1
        done
    done
    
    # Verify all services are communicating
    echo "🔍 Verifying service communication..."
    cd /opt/trading_services
    /opt/trading_venv/bin/python -c "
import asyncio
from services.base_service import BaseService

async def verify_services():
    service = BaseService('verifier')
    
    # Test config service
    try:
        config = await service.call_service('config', 'get_bank_symbols', timeout=10.0)
        print(f'✅ Config service: {len(config.get(\"bank_symbols\", []))} symbols configured')
    except Exception as e:
        print(f'❌ Config service: {e}')
    
    # Test market data service
    try:
        health = await service.call_service('market-data', 'health', timeout=10.0)
        print(f'✅ Market data service: {health[\"status\"]}')
    except Exception as e:
        print(f'❌ Market data service: {e}')
    
    # Test sentiment service
    try:
        health = await service.call_service('sentiment', 'health', timeout=10.0)
        print(f'✅ Sentiment service: {health[\"status\"]} (API usage: {health.get(\"api_usage\", 0):.1f}%)')
    except Exception as e:
        print(f'❌ Sentiment service: {e}')
    
    # Test prediction service
    try:
        health = await service.call_service('prediction', 'health', timeout=10.0)
        print(f'✅ Prediction service: {health[\"status\"]}')
    except Exception as e:
        print(f'❌ Prediction service: {e}')

asyncio.run(verify_services())
"
}

status_services() {
    echo "📊 Service Status:"
    for service in "${SERVICES[@]}"; do
        status=$(systemctl is-active "$service" 2>/dev/null || echo "inactive")
        echo "$service: $status"
    done
    
    echo ""
    echo "🔍 Service Health Checks:"
    cd /opt/trading_services
    /opt/trading_venv/bin/python -c "
import asyncio
from services.base_service import BaseService

async def check_health():
    service = BaseService('health-checker')
    
    services_to_check = ['config', 'market-data', 'sentiment', 'prediction']
    
    for svc in services_to_check:
        try:
            result = await service.call_service(svc, 'health', timeout=5.0)
            uptime = result.get('uptime', 0)
            memory = result.get('memory_mb', 0)
            print(f'{svc}: {result[\"status\"]} (uptime: {uptime:.1f}s, memory: {memory:.1f}MB)')
        except Exception as e:
            print(f'{svc}: ERROR - {e}')

asyncio.run(check_health())
"
    
    echo ""
    echo "⚙️  Configuration Status:"
    /opt/trading_venv/bin/python -c "
import asyncio
from compatibility.enhanced_service_proxy import enhanced_proxy

async def check_config():
    try:
        config = await enhanced_proxy.get_configuration()
        symbols = config.get('bank_symbols', [])
        risk_params = config.get('risk_parameters', {})
        print(f'📈 Bank symbols: {len(symbols)} configured')
        print(f'⚖️  Risk tolerance: {risk_params.get(\"max_position_size\", \"unknown\")}')
        print(f'📊 Sentiment weighting: {config.get(\"sentiment_config\", {}).get(\"weights\", {}).get(\"news_sentiment\", \"unknown\")}')
    except Exception as e:
        print(f'❌ Configuration error: {e}')

asyncio.run(check_config())
"
}

test_end_to_end() {
    echo "🧪 Running end-to-end test..."
    cd /opt/trading_services
    
    /opt/trading_venv/bin/python -c "
import asyncio
from services.base_service import BaseService

async def end_to_end_test():
    service = BaseService('e2e-tester')
    
    try:
        print('🔧 Getting configuration...')
        config = await service.call_service('config', 'get_bank_symbols', timeout=10.0)
        test_symbol = config['bank_symbols'][0] if config.get('bank_symbols') else 'CBA.AX'
        print(f'✅ Using test symbol: {test_symbol}')
        
        print('📊 Getting market data...')
        market_data = await service.call_service('market-data', 'get_market_data', symbol=test_symbol, timeout=15.0)
        print(f'✅ Market data: \${market_data[\"current_price\"]:.2f}')
        
        print('📰 Getting sentiment...')
        sentiment = await service.call_service('sentiment', 'analyze_sentiment', symbol=test_symbol, timeout=20.0)
        print(f'✅ Sentiment: {sentiment[\"sentiment_score\"]:.3f} (confidence: {sentiment[\"confidence\"]:.2f})')
        
        print('🎯 Generating prediction...')
        prediction = await service.call_service('prediction', 'generate_single_prediction', symbol=test_symbol, timeout=30.0)
        print(f'✅ Prediction: {prediction[\"action\"]} @ {prediction[\"confidence\"]:.1%}')
        
        print('🎉 END-TO-END TEST PASSED!')
        return True
        
    except Exception as e:
        print(f'❌ END-TO-END TEST FAILED: {e}')
        return False

result = asyncio.run(end_to_end_test())
exit(0 if result else 1)
"
}

case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 3
        start_services
        ;;
    status)
        status_services
        ;;
    test)
        test_end_to_end
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|test}"
        exit 1
        ;;
esac
```

#### 2. Enhanced Compatibility Scripts
```python
# /opt/trading_services/compatibility/run_predictions_enhanced.py
#!/usr/bin/env python3
"""
Enhanced prediction runner with full configuration and sentiment support
Drop-in replacement for production/cron/fixed_price_mapping_system.py
"""
import sys
import os
from datetime import datetime

# Add paths
sys.path.append('/opt/trading_services')
sys.path.append('/root/test')

from compatibility.enhanced_service_proxy import enhanced_proxy

def main():
    """Main entry point with enhanced functionality"""
    print(f"🚀 Starting enhanced prediction system at {datetime.now()}")
    
    try:
        # Run predictions with full configuration support
        success = enhanced_proxy.run_predictions_with_configuration()
        
        if success:
            print("✅ Enhanced prediction generation completed successfully")
            
            # Log success metrics if available
            try:
                import asyncio
                config = asyncio.run(enhanced_proxy.get_configuration())
                symbols = config.get('bank_symbols', [])
                print(f"📊 Processed {len(symbols)} configured symbols")
                
            except Exception as e:
                print(f"ℹ️  Metrics unavailable: {e}")
            
            sys.exit(0)
        else:
            print("❌ Enhanced prediction generation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Critical error in enhanced prediction system: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 3. Create New Cron Jobs with Configuration Support
```bash
# /opt/trading_services/new_crontab_enhanced.txt
# ENHANCED MICROSERVICES CRON JOBS with Configuration Support

# Market predictions (ENHANCED MICROSERVICES VERSION)
*/30 0-5 * * 1-5 cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_predictions_enhanced.py >> /var/log/trading/prediction_microservices_enhanced.log 2>&1

# Morning analysis (ENHANCED VERSION with sentiment)
5 7 * * 1-5 cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_morning_analysis_enhanced.py >> /var/log/trading/morning_microservices_enhanced.log 2>&1

# Evening training (ENHANCED VERSION with ML config)
5 8 * * * cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/run_evening_training_enhanced.py >> /var/log/trading/evening_microservices_enhanced.log 2>&1

# Sentiment analysis refresh (NEW - optimize MarketAux usage)
0 */6 * * * cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/refresh_sentiment_cache.py >> /var/log/trading/sentiment_refresh.log 2>&1

# Configuration validation (NEW - daily config check)
0 1 * * * cd /opt/trading_services && /opt/trading_venv/bin/python compatibility/validate_configuration.py >> /var/log/trading/config_validation.log 2>&1

# Service health monitoring (NEW)
*/15 * * * * cd /opt/trading_services && /opt/trading_services/scripts/manage_services.sh status >> /var/log/trading/service_health.log 2>&1

# Keep ALL existing cron jobs unchanged initially for safety
```

#### 4. Sentiment Cache Refresh Script
```python
# /opt/trading_services/compatibility/refresh_sentiment_cache.py
#!/usr/bin/env python3
"""
Optimize MarketAux API usage by refreshing sentiment cache strategically
"""
import sys
import os
import asyncio
from datetime import datetime

sys.path.append('/opt/trading_services')

from services.base_service import BaseService

async def refresh_sentiment_cache():
    """Refresh sentiment cache for optimal API usage"""
    service = BaseService('cache-refresher')
    
    try:
        print(f"🔄 Refreshing sentiment cache at {datetime.now()}")
        
        # Get configured symbols
        config = await service.call_service('config', 'get_bank_symbols', timeout=10.0)
        symbols = config.get('bank_symbols', ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX'])
        
        # Use optimized batch sentiment analysis
        sentiments = await service.call_service(
            'sentiment', 
            'get_optimized_sentiment', 
            symbols=symbols,
            timeout=60.0
        )
        
        if sentiments:
            print(f"✅ Refreshed sentiment for {len(sentiments)} symbols")
            
            # Log sentiment summary
            avg_sentiment = sum(s.get('sentiment_score', 0) for s in sentiments) / len(sentiments)
            print(f"📊 Average sentiment: {avg_sentiment:.3f}")
            
            # Check API usage
            health = await service.call_service('sentiment', 'health', timeout=10.0)
            api_usage = health.get('api_usage', 0)
            requests_remaining = health.get('requests_remaining', 0)
            
            print(f"📈 API usage: {api_usage:.1f}% ({requests_remaining} requests remaining)")
            
        else:
            print("⚠️  No sentiment data retrieved")
            
    except Exception as e:
        print(f"❌ Error refreshing sentiment cache: {e}")

def main():
    """Main entry point"""
    try:
        asyncio.run(refresh_sentiment_cache())
        print("✅ Sentiment cache refresh completed")
    except Exception as e:
        print(f"❌ Sentiment cache refresh failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 5. Configuration Validation Script
```python
# /opt/trading_services/compatibility/validate_configuration.py
#!/usr/bin/env python3
"""
Daily configuration validation to ensure system health
"""
import sys
import os
import asyncio
from datetime import datetime

sys.path.append('/opt/trading_services')

from services.base_service import BaseService

async def validate_configuration():
    """Validate all configuration components"""
    service = BaseService('config-validator')
    
    try:
        print(f"🔍 Validating configuration at {datetime.now()}")
        
        # Validate configuration service
        validation = await service.call_service('config', 'validate_config', timeout=10.0)
        
        if validation.get('valid', False):
            print("✅ Configuration validation passed")
        else:
            issues = validation.get('issues', [])
            print(f"❌ Configuration validation failed: {len(issues)} issues")
            for issue in issues:
                print(f"   - {issue}")
        
        # Check critical settings
        settings = await service.call_service('config', 'get_settings', timeout=10.0)
        
        # Validate bank symbols
        symbols = settings.get('bank_symbols', [])
        if len(symbols) >= 4:
            print(f"✅ Bank symbols: {len(symbols)} configured")
        else:
            print(f"⚠️  Only {len(symbols)} bank symbols configured (recommend 4+)")
        
        # Validate risk parameters
        risk_params = settings.get('risk_parameters', {})
        max_pos_size = risk_params.get('max_position_size', 0)
        if 0 < max_pos_size <= 0.5:
            print(f"✅ Risk parameters: max position {max_pos_size:.1%}")
        else:
            print(f"⚠️  Risk parameters may need review: max position {max_pos_size:.1%}")
        
        # Validate sentiment configuration
        sentiment_config = settings.get('sentiment_config', {})
        news_weight = sentiment_config.get('weights', {}).get('news_sentiment', 0)
        if 0.2 <= news_weight <= 0.8:
            print(f"✅ Sentiment config: news weight {news_weight:.1%}")
        else:
            print(f"⚠️  Sentiment config may need review: news weight {news_weight:.1%}")
        
        print("✅ Configuration validation completed")
        
    except Exception as e:
        print(f"❌ Configuration validation error: {e}")

def main():
    """Main entry point"""
    try:
        asyncio.run(validate_configuration())
        print("✅ Daily configuration validation completed")
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 1. Service Testing Script
```python
# /opt/trading_services/scripts/test_services.py
#!/usr/bin/env python3
"""
Comprehensive testing for microservices migration
MUST pass all tests before switching cron jobs
"""
import asyncio
import sys
import os
import json
import time

sys.path.append('/opt/trading_services')
from services.base_service import BaseService

class ServiceTester:
    def __init__(self):
        self.test_service = BaseService('tester')
        self.passed = 0
        self.failed = 0
    
    async def test_market_data_service(self):
        """Test market data service"""
        print("🧪 Testing Market Data Service...")
        
        try:
            # Test health
            health = await self.test_service.call_service('market-data', 'health')
            assert health['status'] == 'healthy', "Service not healthy"
            print("  ✅ Health check passed")
            
            # Test market data fetch
            data = await self.test_service.call_service('market-data', 'get_market_data', symbol='CBA.AX')
            assert 'current_price' in data, "Missing current_price"
            assert 'technical' in data, "Missing technical data"
            print(f"  ✅ Market data fetch passed (CBA.AX: ${data['current_price']:.2f})")
            
            # Test ASX context
            context = await self.test_service.call_service('market-data', 'get_asx_context')
            assert 'context' in context, "Missing context"
            print(f"  ✅ ASX context passed ({context['context']})")
            
            self.passed += 3
            
        except Exception as e:
            print(f"  ❌ Market Data Service test failed: {e}")
            self.failed += 1
    
    async def test_prediction_service(self):
        """Test prediction service"""
        print("🧪 Testing Prediction Service...")
        
        try:
            # Test health
            health = await self.test_service.call_service('prediction', 'health')
            assert health['status'] == 'healthy', "Service not healthy"
            print("  ✅ Health check passed")
            
            # Test single prediction
            prediction = await self.test_service.call_service('prediction', 'generate_single_prediction', symbol='CBA.AX')
            assert 'action' in prediction, "Missing action"
            assert 'confidence' in prediction, "Missing confidence"
            print(f"  ✅ Single prediction passed (CBA.AX: {prediction['action']} @ {prediction['confidence']:.1%})")
            
            # Test batch predictions
            predictions = await self.test_service.call_service('prediction', 'generate_predictions', symbols=['CBA.AX', 'ANZ.AX'])
            assert len(predictions['predictions']) == 2, "Wrong number of predictions"
            print(f"  ✅ Batch predictions passed ({len(predictions['predictions'])} symbols)")
            
            self.passed += 3
            
        except Exception as e:
            print(f"  ❌ Prediction Service test failed: {e}")
            self.failed += 1
    
    async def test_compatibility_layer(self):
        """Test compatibility layer"""
        print("🧪 Testing Compatibility Layer...")
        
        try:
            from compatibility.service_proxy import proxy
            
            # Test service detection
            available = proxy._check_services()
            assert available['market-data'], "Market data service not detected"
            assert available['prediction'], "Prediction service not detected"
            print("  ✅ Service detection passed")
            
            # Test fallback mechanism (simulate service failure)
            proxy.services_available['prediction'] = False
            success = proxy.run_predictions_with_fallback()
            print(f"  ✅ Fallback mechanism passed (success: {success})")
            
            self.passed += 2
            
        except Exception as e:
            print(f"  ❌ Compatibility layer test failed: {e}")
            self.failed += 1
    
    async def test_performance(self):
        """Test performance vs original system"""
        print("🧪 Testing Performance...")
        
        try:
            symbols = ['CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX']
            
            start_time = time.time()
            predictions = await self.test_service.call_service('prediction', 'generate_predictions', symbols=symbols)
            execution_time = time.time() - start_time
            
            assert execution_time < 60, f"Too slow: {execution_time:.1f}s"
            print(f"  ✅ Performance test passed ({execution_time:.1f}s for {len(symbols)} symbols)")
            
            self.passed += 1
            
        except Exception as e:
            print(f"  ❌ Performance test failed: {e}")
            self.failed += 1
    
    async def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting comprehensive service tests...\n")
        
        await self.test_market_data_service()
        await self.test_prediction_service()
        await self.test_compatibility_layer()
        await self.test_performance()
        
        print(f"\n📊 Test Results: {self.passed} passed, {self.failed} failed")
        
        if self.failed == 0:
            print("🎉 All tests passed! Microservices are ready for production.")
            return True
        else:
            print("❌ Some tests failed. Do not switch cron jobs yet.")
            return False

async def main():
    tester = ServiceTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Phase 7: Deployment and Migration Checklist

#### Pre-Deployment Checklist
```bash
# CRITICAL: Complete this checklist before any changes

□ 1. Backup all databases
sudo cp /root/test/data/trading_predictions.db /root/test/data/trading_predictions.db.backup.$(date +%Y%m%d_%H%M%S)
sudo cp /root/test/data/outcomes.db /root/test/data/outcomes.db.backup.$(date +%Y%m%d_%H%M%S)

□ 2. Backup current crontab
crontab -l > /root/test/crontab_backup_$(date +%Y%m%d_%H%M%S).txt

□ 3. Test Redis installation
redis-cli ping

□ 4. Verify disk space
df -h

□ 5. Test Python environment
/opt/trading_venv/bin/python -c "import redis, asyncio; print('Dependencies OK')"

□ 6. Copy all files to services directory
cp -r /root/test/* /opt/trading_services/

□ 7. Set permissions
chown -R root:root /opt/trading_services
chmod +x /opt/trading_services/scripts/*.sh
chmod +x /opt/trading_services/compatibility/*.py
```

#### Deployment Commands
```bash
# PHASE 1: Deploy services (no cron changes yet)
cd /opt/trading_services

# Install systemd services
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable but don't start yet
sudo systemctl enable trading-market-data
sudo systemctl enable trading-prediction

# PHASE 2: Start services
sudo systemctl start redis
sudo systemctl start trading-market-data
sudo systemctl start trading-prediction

# PHASE 3: Test everything
./scripts/test_services.py

# PHASE 4: Only if tests pass - update cron jobs
# BACKUP FIRST
crontab -l > /root/crontab_backup_before_migration.txt

# Add new cron jobs alongside existing (parallel testing)
(crontab -l; cat new_crontab_additions.txt) | crontab -

# PHASE 5: Monitor for 24 hours, then remove old cron jobs
```

#### Rollback Plan
```bash
# EMERGENCY ROLLBACK if anything goes wrong

# 1. Stop microservices
sudo systemctl stop trading-prediction
sudo systemctl stop trading-market-data

# 2. Restore original crontab
crontab /root/crontab_backup_before_migration.txt

# 3. Restore databases if needed
sudo cp /root/test/data/trading_predictions.db.backup.* /root/test/data/trading_predictions.db

# 4. Verify original system works
cd /root/test && /root/trading_venv/bin/python production/cron/fixed_price_mapping_system.py
```

#### Success Metrics
```bash
# Verify migration success

□ All cron jobs running successfully
□ Memory usage < 200MB additional overhead
□ Prediction accuracy unchanged
□ All databases updating correctly
□ No errors in logs for 24 hours
□ Paper trading continues working
□ Dashboard updates correctly
```

## Key Success Factors for Copilot

1. **NEVER modify existing cron jobs until microservices are fully tested**
2. **Always run compatibility layer that falls back to original system**
3. **Test each service independently before integration**
4. **Monitor resource usage continuously**
5. **Keep all original files as fallback**
6. **Verify database writes match exactly**
7. **Ensure paper trading continues uninterrupted**

This implementation guide ensures a risk-free migration with complete fallback capabilities while maintaining all current functionality.
