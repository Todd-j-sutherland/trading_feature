#!/usr/bin/env python3
"""
Simple FastAPI backend to serve trading data to React frontend
Connects to your existing SQLite database and provides REST API endpoints
"""

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from datetime import datetime, timezone
import pytz
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import asyncio
import yfinance as yf
import pandas as pd
import numpy as np
try:
    import joblib
except ImportError:
    joblib = None
import os
from fastapi import APIRouter
from pydantic import BaseModel

# Australian Eastern Time zone
AUSTRALIA_TZ = pytz.timezone('Australia/Sydney')

def convert_to_aest_timestamp(timestamp_str):
    """Convert timestamp to Australian Eastern Time and return Unix timestamp"""
    try:
        # Parse the timestamp (assuming it's in UTC or local time)
        if timestamp_str.endswith('Z'):
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str)
            # If no timezone info, assume UTC
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to Australian Eastern Time
        dt_aest = dt.astimezone(AUSTRALIA_TZ)
        return int(dt_aest.timestamp())
    except Exception as e:
        print(f"Error converting timestamp {timestamp_str}: {e}")
        # Fallback to original parsing
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return int(dt.timestamp())

app = FastAPI(title="ASX Trading API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3000", "http://127.0.0.1:3001", "http://127.0.0.1:3002"],  # React dev server (all common variations)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Database path
DATABASE_PATH = "data/ml_models/training_data.db"

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/banks/{symbol}/ohlcv")
async def get_ohlcv(symbol: str, period: str = "1D", limit: int = 500):
    """Get OHLCV data for a bank symbol"""
    try:
        # Use yfinance to get real price data
        ticker = yf.Ticker(symbol)
        
        # Enhanced period mapping to support hourly data
        period_map = {
            "1H": "7d",   # 7 days for hourly data
            "1D": "1mo",  # 1 month for daily data
            "1W": "6mo",  # 6 months for weekly data
            "1M": "2y"    # 2 years for monthly data
        }
        
        interval_map = {
            "1H": "1h",   # Hourly intervals
            "1D": "1d",   # Daily intervals
            "1W": "1wk",  # Weekly intervals
            "1M": "1mo"   # Monthly intervals
        }
        
        period_str = period_map.get(period, "1mo")
        interval = interval_map.get(period, "1d")
        
        hist = ticker.history(period=period_str, interval=interval)
        
        if hist.empty:
            return {"success": False, "error": "No data found", "data": []}
        
        # Convert to the format expected by TradingView charts (Australian time)
        ohlcv_data = []
        for index, row in hist.iterrows():
            # Convert pandas timestamp to Australian Eastern Time
            aest_dt = index.tz_convert(AUSTRALIA_TZ) if index.tz is not None else index.tz_localize(timezone.utc).tz_convert(AUSTRALIA_TZ)
            
            ohlcv_data.append({
                "timestamp": int(aest_dt.timestamp()),  # Australian Eastern Time timestamp
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        return {
            "success": True,
            "data": ohlcv_data[-limit:],  # Limit results
            "period": period,
            "interval": interval,
            "total_points": len(ohlcv_data),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OHLCV data: {str(e)}")

@app.get("/api/banks/{symbol}/ml-indicators")
async def get_ml_indicators(symbol: str, period: str = "1D"):
    """Get ML indicators for a symbol"""
    try:
        # Determine date range based on period
        if period == "1D":
            days_back = 1
        elif period == "1W":
            days_back = 7
        elif period == "1M":
            days_back = 30
        else:
            days_back = 7
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent data with preference for records with technical_score > 0
        cursor.execute("""
            SELECT symbol, timestamp, sentiment_score, confidence, 
                   technical_score, news_count, reddit_sentiment, event_score
            FROM sentiment_features 
            WHERE symbol = ? 
            AND datetime(timestamp) > datetime('now', '-{} days')
            ORDER BY timestamp DESC
            LIMIT 100
        """.format(days_back), (symbol,))
        
        results = cursor.fetchall()
        conn.close()

        if not results:
            return {
                "success": False,
                "error": f"No data found for {symbol}",
                "data": [],
                "timestamp": datetime.now().isoformat()
            }
        
        ml_data = []
        stats = {
            "total_records": len(results),
            "records_with_technical": 0,
            "records_with_reddit": 0,
            "avg_confidence": 0
        }
        
        confidence_sum = 0
        
        for row in results:
            # Convert timestamp to Australian Eastern Time
            aest_timestamp = convert_to_aest_timestamp(row['timestamp'])
            
            # Track data quality stats
            if row['technical_score'] and row['technical_score'] > 0:
                stats["records_with_technical"] += 1
            if row['reddit_sentiment'] and row['reddit_sentiment'] != 0:
                stats["records_with_reddit"] += 1
            confidence_sum += float(row['confidence'] or 0)
            
            # Generate signal based on sentiment score and confidence
            sentiment = float(row['sentiment_score'] or 0)
            confidence = float(row['confidence'] or 0)
            
            # More lenient thresholds for demo purposes
            if sentiment > 0.03 and confidence > 0.5:
                signal = "BUY"
            elif sentiment < -0.03 and confidence > 0.5:
                signal = "SELL"  
            else:
                signal = "HOLD"
            
            ml_data.append({
                "time": aest_timestamp,
                "sentimentScore": sentiment,
                "confidence": confidence,
                "signal": signal,
                "technicalScore": float(row['technical_score'] or 0),
                "newsCount": int(row['news_count'] or 0),
                "features": {
                    "newsImpact": float(row['news_count'] or 0) * 0.1,
                    "technicalScore": float(row['technical_score'] or 0),
                    "eventImpact": float(row['event_score'] or 0),
                    "redditSentiment": float(row['reddit_sentiment'] or 0)
                }
            })
        
        stats["avg_confidence"] = confidence_sum / len(results) if results else 0
        
        return {
            "success": True,
            "data": ml_data,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ML indicators: {str(e)}")

@app.get("/api/banks/{symbol}/predictions/latest")
async def get_latest_predictions(symbol: str):
    """Get latest prediction for a symbol"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest sentiment data
        cursor.execute("""
            SELECT 
                timestamp,
                sentiment_score,
                confidence,
                technical_score,
                news_count,
                reddit_sentiment,
                event_score
            FROM sentiment_features 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (symbol,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {"success": False, "error": "No data found", "data": None}
        
        # Generate signal based on sentiment score
        sentiment = float(row['sentiment_score'] or 0)
        confidence = float(row['confidence'] or 0)
        
        # More lenient thresholds for demo purposes
        if sentiment > 0.03 and confidence > 0.5:
            signal = "BUY"
        elif sentiment < -0.03 and confidence > 0.5:
            signal = "SELL"  
        else:
            signal = "HOLD"
        
        prediction = {
            "timestamp": row['timestamp'],
            "symbol": symbol,
            "sentimentScore": sentiment,
            "confidence": confidence,
            "signal": signal,
            "technicalScore": float(row['technical_score'] or 0),
            "newsCount": int(row['news_count'] or 0),
            "features": {
                "newsImpact": float(row['news_count'] or 0) * 0.1,
                "technicalScore": float(row['technical_score'] or 0),
                "eventImpact": float(row['event_score'] or 0),
                "redditSentiment": float(row['reddit_sentiment'] or 0)
            }
        }
        
        return {
            "success": True,
            "data": prediction,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching latest predictions: {str(e)}")

@app.get("/api/sentiment/current")
async def get_current_sentiment():
    """Get current sentiment for all banks"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get latest sentiment for each bank
        cursor.execute("""
            SELECT 
                s1.symbol,
                s1.timestamp,
                s1.sentiment_score,
                s1.confidence,
                s1.technical_score,
                s1.news_count,
                CASE 
                    WHEN s1.sentiment_score > 0.05 THEN 'BUY'
                    WHEN s1.sentiment_score < -0.05 THEN 'SELL'
                    ELSE 'HOLD'
                END as signal
            FROM sentiment_features s1
            INNER JOIN (
                SELECT symbol, MAX(timestamp) as max_timestamp
                FROM sentiment_features
                WHERE symbol IN ('CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'SUN.AX', 'QBE.AX')
                GROUP BY symbol
            ) s2 ON s1.symbol = s2.symbol AND s1.timestamp = s2.max_timestamp
            ORDER BY s1.symbol
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        sentiment_data = []
        for row in results:
            sentiment_data.append({
                "symbol": row['symbol'],
                "timestamp": row['timestamp'],
                "sentimentScore": float(row['sentiment_score'] or 0),
                "confidence": float(row['confidence'] or 0),
                "signal": row['signal'],
                "technicalScore": float(row['technical_score'] or 0),
                "newsCount": int(row['news_count'] or 0)
            })
        
        return {
            "success": True,
            "data": sentiment_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current sentiment: {str(e)}")

@app.websocket("/api/stream/predictions")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time predictions"""
    await websocket.accept()
    try:
        while True:
            # Get current sentiment data
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    symbol,
                    timestamp,
                    sentiment_score,
                    confidence,
                    technical_score
                FROM sentiment_features 
                WHERE timestamp >= date('now', '-1 hour')
                ORDER BY timestamp DESC 
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            conn.close()
            
            # Send updates
            for row in results:
                sentiment = float(row['sentiment_score'] or 0)
                confidence = float(row['confidence'] or 0)
                
                if sentiment > 0.05 and confidence > 0.7:
                    signal = "BUY"
                elif sentiment < -0.05 and confidence > 0.7:
                    signal = "SELL"
                else:
                    signal = "HOLD"
                
                update = {
                    "type": "prediction_update",
                    "data": {
                        "symbol": row['symbol'],
                        "timestamp": row['timestamp'],
                        "sentimentScore": sentiment,
                        "confidence": confidence,
                        "signal": signal,
                        "technicalScore": float(row['technical_score'] or 0)
                    }
                }
                
                await websocket.send_text(json.dumps(update))
            
            # Wait 30 seconds before next update
            await asyncio.sleep(30)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Pydantic models for live endpoints
class LivePriceRequest(BaseModel):
    symbol: str
    priceData: Dict[str, float]
    technicalFeatures: Dict[str, float]
    timestamp: int

class LivePredictionResponse(BaseModel):
    success: bool
    prediction: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class LivePriceResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class TechnicalIndicatorsResponse(BaseModel):
    success: bool
    indicators: Optional[Dict[str, float]] = None
    error: Optional[str] = None

# Global cache for ML models and technical data
ml_models_cache = {}
technical_cache = {}

def load_ml_models():
    """Load ML models from disk"""
    global ml_models_cache
    
    if joblib is None:
        print("joblib not available, using fallback prediction only")
        return
    
    try:
        # Try multiple model paths
        model_paths = ["models/", "data/ml_models/models/", "data_v2/ml_models/models/"]
        model_path = None
        
        for path in model_paths:
            if os.path.exists(path):
                model_path = path
                break
        
        if model_path:
            print(f"Loading models from: {model_path}")
            
            # Load symbol-specific models
            loaded_symbols = set()
            for filename in os.listdir(model_path):
                if filename.endswith('.joblib') or filename.endswith('.pkl'):
                    model_file = os.path.join(model_path, filename)
                    
                    # Try to extract symbol from filename
                    if '_' in filename:
                        symbol = filename.split('_')[0]
                    else:
                        symbol = filename.split('.')[0]
                    
                    # Skip current_model and feature_scaler for now
                    if symbol in ['current', 'feature']:
                        continue
                        
                    try:
                        ml_models_cache[symbol] = joblib.load(model_file)
                        loaded_symbols.add(symbol)
                        print(f"Loaded ML model for {symbol}")
                    except Exception as e:
                        print(f"Error loading model {filename}: {e}")
            
            # Load current_model.pkl as fallback for missing symbols
            current_model_path = os.path.join(model_path, "current_model.pkl")
            if os.path.exists(current_model_path):
                try:
                    current_model = joblib.load(current_model_path)
                    # Add current model for common bank symbols if not already loaded
                    bank_symbols = ["CBA.AX", "ANZ.AX", "WBC.AX", "NAB.AX", "CBA", "ANZ", "WBC", "NAB"]
                    for symbol in bank_symbols:
                        if symbol not in loaded_symbols:
                            ml_models_cache[symbol] = current_model
                            print(f"Loaded current model for {symbol} (fallback)")
                except Exception as e:
                    print(f"Error loading current_model.pkl: {e}")
                    
            if not ml_models_cache:
                print("No valid models loaded, using fallback prediction")
        else:
            print("Models directory not found, using fallback prediction")
    except Exception as e:
        print(f"Error loading ML models: {e}")

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI indicator"""
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1]) if not rsi.empty else 50.0
    except:
        return 50.0

def calculate_macd(prices: pd.Series) -> Dict[str, float]:
    """Calculate MACD indicator"""
    try:
        ema12 = prices.ewm(span=12).mean()
        ema26 = prices.ewm(span=26).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9).mean()
        histogram = macd - signal
        
        return {
            'macd': float(macd.iloc[-1]) if not macd.empty else 0.0,
            'signal': float(signal.iloc[-1]) if not signal.empty else 0.0,
            'histogram': float(histogram.iloc[-1]) if not histogram.empty else 0.0
        }
    except:
        return {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0}

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """Calculate Bollinger Bands"""
    try:
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        current_price = float(prices.iloc[-1]) if not prices.empty else 0.0
        upper = float(upper_band.iloc[-1]) if not upper_band.empty else current_price
        lower = float(lower_band.iloc[-1]) if not lower_band.empty else current_price
        
        # Calculate position within bands (0 = lower band, 1 = upper band)
        band_position = (current_price - lower) / (upper - lower) if upper != lower else 0.5
        
        return {
            'upper': upper,
            'lower': lower,
            'middle': float(sma.iloc[-1]) if not sma.empty else current_price,
            'position': band_position
        }
    except:
        return {'upper': 0.0, 'lower': 0.0, 'middle': 0.0, 'position': 0.5}

async def fetch_yahoo_data(symbol: str, period: str = "5d", interval: str = "1m") -> Optional[pd.DataFrame]:
    """Fetch real-time data from Yahoo Finance"""
    try:
        # Convert ASX symbols for Yahoo Finance
        yahoo_symbol = symbol if symbol.endswith('.AX') else f"{symbol}.AX"
        
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            print(f"No data returned for {yahoo_symbol}")
            return None
            
        return data
    except Exception as e:
        print(f"Error fetching Yahoo data for {symbol}: {e}")
        return None

# Live endpoints
@app.get("/api/live/price/{symbol}")
async def get_live_price(symbol: str):
    """Get latest price data for a symbol"""
    try:
        data = await fetch_yahoo_data(symbol, period="1d", interval="1m")
        
        if data is None or data.empty:
            return {
                "success": False, 
                "error": f"No data available for {symbol}"
            }
        
        # Get latest candle
        latest = data.iloc[-1]
        timestamp = int(latest.name.timestamp() * 1000)  # Convert to milliseconds
        
        price_data = {
            "timestamp": timestamp,
            "open": float(latest['Open']),
            "high": float(latest['High']),
            "low": float(latest['Low']),
            "close": float(latest['Close']),
            "volume": int(latest['Volume'])
        }
        
        return {"success": True, "data": price_data}
        
    except Exception as e:
        print(f"Error getting live price for {symbol}: {e}")
        return {
            "success": False, 
            "error": str(e)
        }

@app.get("/api/live/technical/{symbol}")
async def get_technical_indicators(symbol: str):
    """Calculate technical indicators for a symbol"""
    try:
        # Check cache first (cache for 1 minute)
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if cache_key in technical_cache:
            return {
                "success": True, 
                "indicators": technical_cache[cache_key]
            }
        
        # Fetch historical data for indicators
        data = await fetch_yahoo_data(symbol, period="1mo", interval="1d")
        
        if data is None or data.empty:
            return {
                "success": False, 
                "error": f"No data available for {symbol}"
            }
        
        prices = data['Close']
        volumes = data['Volume']
        
        # Calculate indicators
        rsi = calculate_rsi(prices)
        macd_data = calculate_macd(prices)
        bollinger = calculate_bollinger_bands(prices)
        
        # Volume ratio (current vs average)
        avg_volume = volumes.rolling(window=20).mean().iloc[-1]
        current_volume = volumes.iloc[-1]
        volume_ratio = float(current_volume / avg_volume) if avg_volume > 0 else 1.0
        
        # Price momentum (5-day change)
        price_momentum = float((prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5] * 100) if len(prices) >= 5 else 0.0
        
        # Volatility (daily high-low range as percentage of close)
        volatility = float(((data['High'].iloc[-1] - data['Low'].iloc[-1]) / data['Close'].iloc[-1]) * 100)
        
        indicators = {
            # Core technical indicators (matching ML pipeline)
            'rsi': rsi,
            'macd': macd_data['macd'],
            'macd_signal': macd_data['signal'],
            'macd_histogram': macd_data['histogram'],
            'moving_avg_20': float(prices.rolling(20).mean().iloc[-1]),  # ML pipeline uses this name
            'sma_20': float(prices.rolling(20).mean().iloc[-1]),  # Keep for backward compatibility
            'sma_50': float(prices.rolling(50).mean().iloc[-1]) if len(prices) >= 50 else float(prices.mean()),
            
            # Additional indicators
            'bollinger_upper': bollinger['upper'],
            'bollinger_lower': bollinger['lower'],
            'bollinger_position': bollinger['position'],
            'volume_ratio': volume_ratio,
            'price_momentum': price_momentum,
            'volatility': volatility,
            
            # Current market state
            'current_price': float(prices.iloc[-1]),
            'price_change_pct': price_momentum,  # Same calculation
            'volume': float(current_volume),
        }
        
        # Cache the result
        technical_cache[cache_key] = indicators
        
        return {"success": True, "indicators": indicators}
        
    except Exception as e:
        print(f"Error calculating technical indicators for {symbol}: {e}")
        return {
            "success": False, 
            "error": str(e)
        }

@app.post("/api/live/ml-predict")
async def run_ml_prediction(request: LivePriceRequest):
    """Run ML prediction on live data"""
    try:
        symbol = request.symbol
        price_data = request.priceData
        technical_features = request.technicalFeatures
        
        # Prepare features for ML model (matching ML pipeline feature names)
        # Create comprehensive 20-feature set to match model expectations
        ml_features = {
            # Core price features (1-4)
            'current_price': price_data.get('close', 0),
            'price_change_pct': ((price_data.get('close', 0) - price_data.get('open', 0)) / max(price_data.get('open', 1), 0.01)) * 100,
            'volume': price_data.get('volume', 0),
            'volatility': ((price_data.get('high', 0) - price_data.get('low', 0)) / max(price_data.get('close', 1), 0.01)) * 100,
            
            # Technical indicators (5-12)
            'rsi': technical_features.get('rsi', 50),
            'macd': technical_features.get('macd', 0),
            'moving_avg_20': technical_features.get('moving_avg_20', technical_features.get('sma_20', price_data.get('close', 0))),
            'moving_avg_50': technical_features.get('moving_avg_50', technical_features.get('sma_50', price_data.get('close', 0))),
            'bollinger_upper': technical_features.get('bollinger_upper', price_data.get('close', 0) * 1.02),
            'bollinger_lower': technical_features.get('bollinger_lower', price_data.get('close', 0) * 0.98),
            'stochastic_k': technical_features.get('stochastic_k', 50),
            'williams_r': technical_features.get('williams_r', -50),
            
            # Volume and momentum features (13-16)
            'volume_ratio': technical_features.get('volume_ratio', 1.0),
            'price_momentum': technical_features.get('price_momentum', 0),
            'volume_sma_ratio': technical_features.get('volume_sma_ratio', 1.0),
            'price_position': technical_features.get('price_position', 0.5),  # Position within daily range
            
            # Sentiment and news features (17-20)
            'sentiment_score': 0.0,  # Will be calculated
            'confidence': 0.5,       # Will be calculated
            'news_count': 0,         # No live news integration yet
            'impact_score': 0.0,     # Will be calculated
        }
        
        # Use ML model if available, otherwise fallback
        if symbol in ml_models_cache and joblib is not None:
            try:
                model = ml_models_cache[symbol]
                
                # Prepare feature vector in the exact order the model expects (20 features)
                feature_order = [
                    'current_price', 'price_change_pct', 'volume', 'volatility',
                    'rsi', 'macd', 'moving_avg_20', 'moving_avg_50',
                    'bollinger_upper', 'bollinger_lower', 'stochastic_k', 'williams_r',
                    'volume_ratio', 'price_momentum', 'volume_sma_ratio', 'price_position',
                    'sentiment_score', 'confidence', 'news_count', 'impact_score'
                ]
                
                # Create feature vector ensuring we have exactly 20 features
                feature_vector = [ml_features.get(feature, 0.0) for feature in feature_order]
                
                # Ensure we have exactly 20 features
                while len(feature_vector) < 20:
                    feature_vector.append(0.0)
                feature_vector = feature_vector[:20]  # Truncate if too many
                
                # Convert to numpy array for prediction
                feature_array = np.array(feature_vector).reshape(1, -1)
                
                # Make prediction
                prediction = model.predict(feature_array)[0]
                confidence = max(model.predict_proba(feature_array)[0])
                
                # Convert prediction to sentiment score
                sentiment_score = float(prediction) if isinstance(prediction, (int, float)) else 0.0
                confidence = float(confidence)
                
            except Exception as model_error:
                print(f"ML model error for {symbol}: {model_error}, using fallback")
                sentiment_score, confidence = fallback_prediction(ml_features)
        else:
            print(f"No ML model for {symbol}, using fallback prediction")
            sentiment_score, confidence = fallback_prediction(ml_features)
        
        # Generate trading signal
        signal = generate_trading_signal(sentiment_score, confidence, ml_features)
        
        # Calculate technical score
        technical_score = calculate_technical_score(technical_features)
        
        prediction_result = {
            'timestamp': request.timestamp,
            'symbol': symbol,
            'price': price_data.get('close', 0),
            'change': ml_features['price_change_pct'],
            'volume': price_data.get('volume', 0),
            'sentimentScore': float(sentiment_score),
            'confidence': float(confidence),
            'signal': signal,
            'technicalScore': technical_score,
            'features': {
                # Core technical indicators (matching frontend interface)
                'rsi': technical_features.get('rsi', 50),
                'macd': technical_features.get('macd', 0),
                'moving_avg_20': technical_features.get('moving_avg_20', 0),
                'volume_ratio': technical_features.get('volume_ratio', 1.0),
                'price_momentum': technical_features.get('price_momentum', 0),
                'volatility': ml_features['volatility'],
                # Extended features for ML compatibility
                'current_price': ml_features['current_price'],
                'price_change_pct': ml_features['price_change_pct'],
                'news_count': ml_features['news_count'],
                'impact_score': abs(sentiment_score) * confidence,
            }
        }
        
        return {"success": True, "prediction": prediction_result}
        
    except Exception as e:
        print(f"Error running ML prediction: {e}")
        return {
            "success": False, 
            "error": str(e)
        }

def fallback_prediction(ml_features: Dict[str, float]) -> tuple[float, float]:
    """Fallback prediction when ML model is not available"""
    rsi = ml_features.get('rsi', 50)
    macd = ml_features.get('macd', 0)
    price_momentum = ml_features.get('price_momentum', 0)
    moving_avg_20 = ml_features.get('moving_avg_20', 0)
    current_price = ml_features.get('current_price', 0)
    
    # Simple rule-based prediction (matching morning analyzer logic)
    sentiment_score = 0.0
    
    # RSI contribution (matching morning analyzer)
    if rsi > 70:
        sentiment_score -= 0.3  # Overbought
    elif rsi < 30:
        sentiment_score += 0.3  # Oversold
    
    # MACD contribution
    if macd > 0:
        sentiment_score += 0.2
    else:
        sentiment_score -= 0.2
    
    # Price momentum contribution
    sentiment_score += price_momentum * 0.01
    
    # Moving average comparison (like morning analyzer's SMA logic)
    if moving_avg_20 > 0 and current_price > 0:
        if current_price > moving_avg_20 * 1.02:  # 2% above MA
            sentiment_score += 0.2
        elif current_price < moving_avg_20 * 0.98:  # 2% below MA
            sentiment_score -= 0.2
    
    # Clamp to [-1, 1]
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    
    # Calculate confidence based on signal strength
    confidence = min(0.8, abs(sentiment_score) + 0.2)
    
    return sentiment_score, confidence

def generate_trading_signal(sentiment_score: float, confidence: float, ml_features: Dict[str, float]) -> str:
    """Generate BUY/SELL/HOLD signal (matching morning analyzer logic)"""
    # Only generate strong signals when confidence is high
    if confidence < 0.6:
        return 'HOLD'
    
    # Use more conservative thresholds like the morning analyzer
    if sentiment_score > 0.3 and confidence > 0.7:
        return 'BUY'
    elif sentiment_score < -0.3 and confidence > 0.7:
        return 'SELL'
    else:
        return 'HOLD'

def calculate_technical_score(technical_features: Dict[str, float]) -> float:
    """Calculate composite technical analysis score"""
    rsi = technical_features.get('rsi', 50)
    macd = technical_features.get('macd', 0)
    bollinger_pos = technical_features.get('bollinger_position', 0.5)
    volume_ratio = technical_features.get('volume_ratio', 1.0)
    
    # Normalize and combine indicators
    rsi_norm = (rsi - 50) / 50  # -1 to 1
    macd_norm = max(-1, min(1, macd * 10))  # Rough normalization
    bollinger_norm = (bollinger_pos - 0.5) * 2  # -1 to 1
    volume_norm = max(-1, min(1, (volume_ratio - 1) * 2))  # Normalize around 1
    
    # Weighted average
    technical_score = (rsi_norm * 0.3 + macd_norm * 0.3 + bollinger_norm * 0.25 + volume_norm * 0.15)
    
    return float(max(-1, min(1, technical_score)))

# Load models on startup
load_ml_models()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "ASX Trading API is running",
        "timestamp": datetime.now().isoformat(),
        "database": DATABASE_PATH
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000, reload=True)
