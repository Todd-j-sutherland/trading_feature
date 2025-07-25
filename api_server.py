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
from typing import List, Dict, Optional
import asyncio
import yfinance as yf
import pandas as pd

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
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
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
            
            ml_data.append({
                "time": aest_timestamp,
                "sentimentScore": float(row['sentiment_score'] or 0),
                "confidence": float(row['confidence'] or 0),
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
        
        if sentiment > 0.05 and confidence > 0.7:
            signal = "BUY"
        elif sentiment < -0.05 and confidence > 0.7:
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
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
