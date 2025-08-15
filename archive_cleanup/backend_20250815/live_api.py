"""
Live trading data API endpoints
Fetches real-time data from Yahoo Finance and runs ML predictions
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yfinance as yf
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import sqlite3
import joblib
import os
from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize router
live_router = APIRouter(prefix="/api/live", tags=["live"])

# Pydantic models
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

# Global cache for ML models
ml_models_cache = {}
technical_cache = {}

def load_ml_models():
    """Load ML models from disk"""
    global ml_models_cache
    
    try:
        model_path = "models/"
        if os.path.exists(model_path):
            for filename in os.listdir(model_path):
                if filename.endswith('.joblib') or filename.endswith('.pkl'):
                    symbol = filename.split('_')[0] if '_' in filename else filename.split('.')[0]
                    model_file = os.path.join(model_path, filename)
                    ml_models_cache[symbol] = joblib.load(model_file)
                    logger.info(f"Loaded ML model for {symbol}")
        else:
            logger.warning("Models directory not found, using fallback prediction")
    except Exception as e:
        logger.error(f"Error loading ML models: {e}")

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not rsi.empty else 50.0

def calculate_macd(prices: pd.Series) -> Dict[str, float]:
    """Calculate MACD indicator"""
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

def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: int = 2) -> Dict[str, float]:
    """Calculate Bollinger Bands"""
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

async def fetch_yahoo_data(symbol: str, period: str = "5d", interval: str = "1m") -> Optional[pd.DataFrame]:
    """Fetch real-time data from Yahoo Finance"""
    try:
        # Convert ASX symbols for Yahoo Finance
        yahoo_symbol = symbol if symbol.endswith('.AX') else f"{symbol}.AX"
        
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(period=period, interval=interval)
        
        if data.empty:
            logger.warning(f"No data returned for {yahoo_symbol}")
            return None
            
        return data
    except Exception as e:
        logger.error(f"Error fetching Yahoo data for {symbol}: {e}")
        return None

@live_router.get("/price/{symbol}")
async def get_live_price(symbol: str) -> LivePriceResponse:
    """Get latest price data for a symbol"""
    try:
        data = await fetch_yahoo_data(symbol, period="1d", interval="1m")
        
        if data is None or data.empty:
            return LivePriceResponse(
                success=False, 
                error=f"No data available for {symbol}"
            )
        
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
        
        return LivePriceResponse(success=True, data=price_data)
        
    except Exception as e:
        logger.error(f"Error getting live price for {symbol}: {e}")
        return LivePriceResponse(
            success=False, 
            error=str(e)
        )

@live_router.get("/technical/{symbol}")
async def get_technical_indicators(symbol: str) -> TechnicalIndicatorsResponse:
    """Calculate technical indicators for a symbol"""
    try:
        # Check cache first (cache for 1 minute)
        cache_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
        if cache_key in technical_cache:
            return TechnicalIndicatorsResponse(
                success=True, 
                indicators=technical_cache[cache_key]
            )
        
        # Fetch historical data for indicators
        data = await fetch_yahoo_data(symbol, period="1mo", interval="1d")
        
        if data is None or data.empty:
            return TechnicalIndicatorsResponse(
                success=False, 
                error=f"No data available for {symbol}"
            )
        
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
        
        indicators = {
            'rsi': rsi,
            'macd': macd_data['macd'],
            'macd_signal': macd_data['signal'],
            'macd_histogram': macd_data['histogram'],
            'bollinger_upper': bollinger['upper'],
            'bollinger_lower': bollinger['lower'],
            'bollinger_position': bollinger['position'],
            'volume_ratio': volume_ratio,
            'price_momentum': price_momentum,
            'sma_20': float(prices.rolling(20).mean().iloc[-1]),
            'sma_50': float(prices.rolling(50).mean().iloc[-1]) if len(prices) >= 50 else float(prices.mean())
        }
        
        # Cache the result
        technical_cache[cache_key] = indicators
        
        return TechnicalIndicatorsResponse(success=True, indicators=indicators)
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return TechnicalIndicatorsResponse(
            success=False, 
            error=str(e)
        )

@live_router.post("/ml-predict")
async def run_ml_prediction(request: LivePriceRequest) -> LivePredictionResponse:
    """Run ML prediction on live data"""
    try:
        symbol = request.symbol
        price_data = request.priceData
        technical_features = request.technicalFeatures
        
        # Prepare features for ML model
        features = {
            'price': price_data.get('close', 0),
            'volume': price_data.get('volume', 0),
            'price_change': ((price_data.get('close', 0) - price_data.get('open', 0)) / price_data.get('open', 1)) * 100,
            'volatility': ((price_data.get('high', 0) - price_data.get('low', 0)) / price_data.get('close', 1)) * 100,
            **technical_features
        }
        
        # Use ML model if available, otherwise fallback
        if symbol in ml_models_cache:
            try:
                model = ml_models_cache[symbol]
                
                # Prepare feature vector (ensure proper order and missing values)
                feature_names = ['rsi', 'macd', 'bollinger_position', 'volume_ratio', 'price_momentum']
                feature_vector = [features.get(name, 0) for name in feature_names]
                feature_array = np.array(feature_vector).reshape(1, -1)
                
                # Make prediction
                prediction = model.predict(feature_array)[0]
                confidence = max(model.predict_proba(feature_array)[0])
                
                # Convert to sentiment score
                sentiment_score = prediction if isinstance(prediction, (int, float)) else 0.0
                
            except Exception as model_error:
                logger.warning(f"ML model error for {symbol}: {model_error}, using fallback")
                sentiment_score, confidence = fallback_prediction(features)
        else:
            logger.info(f"No ML model for {symbol}, using fallback prediction")
            sentiment_score, confidence = fallback_prediction(features)
        
        # Generate trading signal
        signal = generate_trading_signal(sentiment_score, confidence, features)
        
        # Calculate technical score
        technical_score = calculate_technical_score(technical_features)
        
        prediction_result = {
            'timestamp': request.timestamp,
            'symbol': symbol,
            'price': price_data.get('close', 0),
            'change': features['price_change'],
            'volume': price_data.get('volume', 0),
            'sentimentScore': float(sentiment_score),
            'confidence': float(confidence),
            'signal': signal,
            'technicalScore': technical_score,
            'features': {
                'rsi': technical_features.get('rsi', 50),
                'macd': technical_features.get('macd', 0),
                'bollinger': technical_features.get('bollinger_position', 0.5),
                'volume_ratio': technical_features.get('volume_ratio', 1.0),
                'price_momentum': technical_features.get('price_momentum', 0)
            }
        }
        
        return LivePredictionResponse(success=True, prediction=prediction_result)
        
    except Exception as e:
        logger.error(f"Error running ML prediction: {e}")
        return LivePredictionResponse(
            success=False, 
            error=str(e)
        )

def fallback_prediction(features: Dict[str, float]) -> tuple[float, float]:
    """Fallback prediction when ML model is not available"""
    rsi = features.get('rsi', 50)
    macd = features.get('macd', 0)
    price_momentum = features.get('price_momentum', 0)
    bollinger_pos = features.get('bollinger_position', 0.5)
    
    # Simple rule-based prediction
    sentiment_score = 0.0
    
    # RSI contribution
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
    
    # Bollinger band contribution
    if bollinger_pos > 0.8:
        sentiment_score -= 0.2  # Near upper band
    elif bollinger_pos < 0.2:
        sentiment_score += 0.2  # Near lower band
    
    # Clamp to [-1, 1]
    sentiment_score = max(-1.0, min(1.0, sentiment_score))
    
    # Calculate confidence based on signal strength
    confidence = min(0.8, abs(sentiment_score) + 0.2)
    
    return sentiment_score, confidence

def generate_trading_signal(sentiment_score: float, confidence: float, features: Dict[str, float]) -> str:
    """Generate BUY/SELL/HOLD signal"""
    # Only generate strong signals when confidence is high
    if confidence < 0.6:
        return 'HOLD'
    
    if sentiment_score > 0.3:
        return 'BUY'
    elif sentiment_score < -0.3:
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
