#!/usr/bin/env python3
"""
Minimal FastAPI backend for debugging performance issues
"""

print("🔍 Starting minimal API server...")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json
from datetime import datetime, timezone
import pytz
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np

print("✅ Basic imports loaded")

# Create FastAPI app
app = FastAPI(title="Minimal ASX Trading API")

print("✅ FastAPI app created")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("✅ CORS configured")

# Database path
DATABASE_PATH = "data/ml_models/training_data.db"

# Australian Eastern Time zone
AUSTRALIA_TZ = pytz.timezone('Australia/Sydney')

print("✅ Timezone configured")

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

print("✅ Database connection function defined")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Minimal ASX Trading API is running",
        "timestamp": datetime.now().isoformat(),
        "status": "healthy"
    }

print("✅ Root endpoint defined")

@app.get("/api/banks/{symbol}/ohlcv")
async def get_ohlcv(symbol: str, period: str = "1D", limit: int = 500):
    """Get OHLCV data for a bank symbol - simplified version"""
    try:
        print(f"🔍 Fetching data for {symbol}, period: {period}")
        
        # Use yfinance to get real price data
        ticker = yf.Ticker(symbol)
        
        # Simple period mapping
        if period == "1H":
            data = ticker.history(period="1d", interval="1h")
        elif period == "1D":
            data = ticker.history(period="5d", interval="1d")
        elif period == "1W":
            data = ticker.history(period="1mo", interval="1d")
        else:
            data = ticker.history(period="1d", interval="1h")
        
        print(f"✅ Got {len(data)} data points for {symbol}")
        
        if data.empty:
            return {"success": False, "data": [], "message": "No data available"}
        
        # Convert to the format expected by frontend
        ohlcv_data = []
        for timestamp, row in data.iterrows():
            ohlcv_data.append({
                "timestamp": int(timestamp.timestamp()),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
        
        # Limit results
        ohlcv_data = ohlcv_data[-limit:]
        
        return {
            "success": True,
            "data": ohlcv_data,
            "count": len(ohlcv_data),
            "symbol": symbol,
            "period": period
        }
        
    except Exception as e:
        print(f"❌ Error fetching data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

print("✅ OHLCV endpoint defined")

@app.get("/api/test")
async def test():
    """Simple test endpoint"""
    return {"status": "ok", "message": "Minimal API working"}

print("✅ Test endpoint defined")

if __name__ == "__main__":
    print("🚀 Starting uvicorn server...")
    import uvicorn
    uvicorn.run("api_server_minimal:app", host="0.0.0.0", port=8000, reload=False)
    print("✅ Server started")
