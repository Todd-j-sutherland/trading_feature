#!/usr/bin/env python3
"""
Real-time ML API for Frontend Integration

Provides WebSocket and REST API endpoints for live trading predictions
Integrates with the enhanced multi-bank ML system for real-time analysis
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import asyncio
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys
import logging
from dataclasses import dataclass
import yfinance as yf

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Import our enhanced ML components
try:
    from enhanced_ml_system.multi_bank_data_collector import MultiBankDataCollector
    from enhanced_ml_system.html_dashboard_generator import HTMLBankDashboard
except ImportError as e:
    print(f"Warning: Could not import enhanced ML components: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Real-time ML Trading API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API
class BankPrediction(BaseModel):
    symbol: str
    bank_name: str
    sector: str
    current_price: float
    price_change_1d: float
    price_change_5d: float
    rsi: float
    sentiment_score: float
    sentiment_confidence: float
    predicted_direction: str
    predicted_magnitude: float
    prediction_confidence: float
    optimal_action: str
    timestamp: str

class MarketSummary(BaseModel):
    total_banks: int
    avg_change_1d: float
    avg_sentiment: float
    buy_signals: int
    sell_signals: int
    hold_signals: int
    best_performer: Dict[str, Any]
    worst_performer: Dict[str, Any]
    last_updated: str

class SentimentHeadline(BaseModel):
    symbol: str
    headline: str
    sentiment_score: float
    confidence: float
    category: str
    timestamp: str

# Global variables for real-time updates
connected_clients: List[WebSocket] = []
ml_collector = None
dashboard_generator = None
last_update_time = None

@dataclass
class RealtimeMLSystem:
    """Coordinates real-time ML predictions and data collection"""
    
    def __init__(self):
        self.db_path = 'data/multi_bank_analysis.db'
        self.collector = MultiBankDataCollector() if 'MultiBankDataCollector' in globals() else None
        self.dashboard = HTMLBankDashboard() if 'HTMLBankDashboard' in globals() else None
        self.last_predictions = {}
        self.update_interval = 60  # seconds
        
    async def get_latest_predictions(self) -> List[BankPrediction]:
        """Get latest ML predictions for all banks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT DISTINCT 
                        symbol, bank_name, sector, timestamp,
                        current_price, price_change_1d, price_change_5d,
                        rsi, sentiment_score, sentiment_confidence,
                        predicted_direction, predicted_magnitude,
                        prediction_confidence, optimal_action
                    FROM bank_performance 
                    WHERE id IN (
                        SELECT MAX(id) FROM bank_performance GROUP BY symbol
                    )
                    ORDER BY price_change_1d DESC
                """
                
                df = pd.read_sql_query(query, conn)
                
                predictions = []
                for _, row in df.iterrows():
                    prediction = BankPrediction(
                        symbol=row['symbol'],
                        bank_name=row['bank_name'],
                        sector=row['sector'],
                        current_price=float(row['current_price']),
                        price_change_1d=float(row['price_change_1d']),
                        price_change_5d=float(row['price_change_5d']) if pd.notna(row['price_change_5d']) else 0.0,
                        rsi=float(row['rsi']),
                        sentiment_score=float(row['sentiment_score']),
                        sentiment_confidence=float(row['sentiment_confidence']),
                        predicted_direction=row['predicted_direction'] or 'HOLD',
                        predicted_magnitude=float(row['predicted_magnitude']) if pd.notna(row['predicted_magnitude']) else 0.0,
                        prediction_confidence=float(row['prediction_confidence']) if pd.notna(row['prediction_confidence']) else 0.5,
                        optimal_action=row['optimal_action'],
                        timestamp=row['timestamp']
                    )
                    predictions.append(prediction)
                    
                return predictions
                
        except Exception as e:
            logger.error(f"Error getting latest predictions: {e}")
            return []
    
    async def get_market_summary(self) -> MarketSummary:
        """Generate market summary statistics"""
        predictions = await self.get_latest_predictions()
        
        if not predictions:
            return MarketSummary(
                total_banks=0,
                avg_change_1d=0.0,
                avg_sentiment=0.0,
                buy_signals=0,
                sell_signals=0,
                hold_signals=0,
                best_performer={},
                worst_performer={},
                last_updated=datetime.now().isoformat()
            )
        
        # Calculate statistics
        total_banks = len(predictions)
        avg_change = sum(p.price_change_1d for p in predictions) / total_banks
        avg_sentiment = sum(p.sentiment_score for p in predictions) / total_banks
        
        # Count actions
        buy_signals = sum(1 for p in predictions if p.optimal_action in ['BUY', 'STRONG_BUY'])
        sell_signals = sum(1 for p in predictions if p.optimal_action in ['SELL', 'STRONG_SELL'])
        hold_signals = sum(1 for p in predictions if p.optimal_action == 'HOLD')
        
        # Find best and worst performers
        best = max(predictions, key=lambda p: p.price_change_1d)
        worst = min(predictions, key=lambda p: p.price_change_1d)
        
        return MarketSummary(
            total_banks=total_banks,
            avg_change_1d=round(avg_change, 2),
            avg_sentiment=round(avg_sentiment, 3),
            buy_signals=buy_signals,
            sell_signals=sell_signals,
            hold_signals=hold_signals,
            best_performer={
                'symbol': best.symbol,
                'name': best.bank_name,
                'change': best.price_change_1d,
                'action': best.optimal_action
            },
            worst_performer={
                'symbol': worst.symbol,
                'name': worst.bank_name,
                'change': worst.price_change_1d,
                'action': worst.optimal_action
            },
            last_updated=datetime.now().isoformat()
        )
    
    async def get_sentiment_headlines(self, limit: int = 10) -> List[SentimentHeadline]:
        """Get recent sentiment headlines"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT symbol, headline, sentiment_score, confidence, category, timestamp
                    FROM news_sentiment_analysis
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                
                df = pd.read_sql_query(query, conn, params=(limit,))
                
                headlines = []
                for _, row in df.iterrows():
                    headline = SentimentHeadline(
                        symbol=row['symbol'],
                        headline=row['headline'],
                        sentiment_score=float(row['sentiment_score']),
                        confidence=float(row['confidence']),
                        category=row['category'],
                        timestamp=row['timestamp']
                    )
                    headlines.append(headline)
                    
                return headlines
                
        except Exception as e:
            logger.error(f"Error getting sentiment headlines: {e}")
            return []
    
    async def run_live_analysis(self):
        """Run live ML analysis and update database"""
        if self.collector:
            try:
                logger.info("Running live ML analysis...")
                await asyncio.get_event_loop().run_in_executor(
                    None, self.collector.collect_all_banks_data
                )
                logger.info("✅ Live analysis completed")
            except Exception as e:
                logger.error(f"Error in live analysis: {e}")

# Initialize the real-time ML system
realtime_ml = RealtimeMLSystem()

# REST API Endpoints
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/predictions", response_model=List[BankPrediction])
async def get_predictions():
    """Get latest ML predictions for all banks"""
    predictions = await realtime_ml.get_latest_predictions()
    return predictions

@app.get("/api/market-summary", response_model=MarketSummary)
async def get_market_summary():
    """Get market summary statistics"""
    summary = await realtime_ml.get_market_summary()
    return summary

@app.get("/api/sentiment-headlines", response_model=List[SentimentHeadline])
async def get_sentiment_headlines(limit: int = 10):
    """Get recent sentiment headlines"""
    headlines = await realtime_ml.get_sentiment_headlines(limit)
    return headlines

@app.get("/api/bank/{symbol}", response_model=BankPrediction)
async def get_bank_prediction(symbol: str):
    """Get prediction for a specific bank"""
    predictions = await realtime_ml.get_latest_predictions()
    bank_prediction = next((p for p in predictions if p.symbol == symbol), None)
    
    if not bank_prediction:
        raise HTTPException(status_code=404, detail=f"Bank {symbol} not found")
    
    return bank_prediction

@app.post("/api/refresh-data")
async def refresh_data():
    """Manually trigger data refresh"""
    try:
        await realtime_ml.run_live_analysis()
        return {"status": "success", "message": "Data refresh initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {e}")

# WebSocket endpoint for real-time updates
@app.websocket("/ws/live-updates")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time trading updates"""
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"Client connected. Total clients: {len(connected_clients)}")
    
    try:
        # Send initial data
        predictions = await realtime_ml.get_latest_predictions()
        summary = await realtime_ml.get_market_summary()
        
        await websocket.send_text(json.dumps({
            "type": "initial_data",
            "predictions": [p.dict() for p in predictions],
            "summary": summary.dict(),
            "timestamp": datetime.now().isoformat()
        }))
        
        # Keep connection alive and send periodic updates
        while True:
            try:
                # Wait for next update or client message
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
            except asyncio.TimeoutError:
                # Send periodic heartbeat/update
                try:
                    predictions = await realtime_ml.get_latest_predictions()
                    summary = await realtime_ml.get_market_summary()
                    
                    await websocket.send_text(json.dumps({
                        "type": "update",
                        "predictions": [p.dict() for p in predictions],
                        "summary": summary.dict(),
                        "timestamp": datetime.now().isoformat()
                    }))
                except Exception as e:
                    logger.error(f"Error sending update: {e}")
                    break
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(connected_clients)}")

async def broadcast_update():
    """Broadcast updates to all connected WebSocket clients"""
    if not connected_clients:
        return
    
    try:
        predictions = await realtime_ml.get_latest_predictions()
        summary = await realtime_ml.get_market_summary()
        
        message = json.dumps({
            "type": "live_update",
            "predictions": [p.dict() for p in predictions],
            "summary": summary.dict(),
            "timestamp": datetime.now().isoformat()
        })
        
        # Send to all connected clients
        disconnected_clients = []
        for client in connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            connected_clients.remove(client)
            
    except Exception as e:
        logger.error(f"Error in broadcast_update: {e}")

# Background task for periodic data updates
async def periodic_data_update():
    """Background task to update ML predictions periodically"""
    while True:
        try:
            # Run ML analysis every 5 minutes
            await realtime_ml.run_live_analysis()
            
            # Broadcast updates to connected clients
            await broadcast_update()
            
            logger.info("✅ Periodic update completed")
            
        except Exception as e:
            logger.error(f"Error in periodic update: {e}")
        
        # Wait 5 minutes before next update
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("🚀 Starting Real-time ML API server...")
    
    # Start periodic data updates
    asyncio.create_task(periodic_data_update())
    
    logger.info("✅ Real-time ML API server started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Real-time ML API server...")
    
    # Close all WebSocket connections
    for client in connected_clients:
        try:
            await client.close()
        except:
            pass
    
    logger.info("✅ Real-time ML API server stopped")

if __name__ == "__main__":
    import uvicorn
    
    print("🏦 Starting Real-time ML Trading API")
    print("=" * 50)
    print("🔗 API Documentation: http://localhost:8001/docs")
    print("🌐 WebSocket: ws://localhost:8001/ws/live-updates")
    print("📊 Predictions: http://localhost:8001/api/predictions")
    print("📈 Market Summary: http://localhost:8001/api/market-summary")
    
    uvicorn.run(
        "realtime_ml_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
