import os
import json
import logging
import pandas as pd
from datetime import datetime
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, project_root)

logger = logging.getLogger(__name__)

def load_sentiment_data(dashboard) -> dict:
    """Load sentiment history data for all banks"""
    all_data = {}
    logger.info(f"Loading sentiment data from: {dashboard.data_path}")
    
    for symbol in dashboard.bank_symbols:
        file_path = os.path.join(dashboard.data_path, f"{symbol}_history.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    all_data[symbol] = data if isinstance(data, list) else [data]
            except Exception as e:
                logger.error(f"Error loading data for {symbol}: {e}")
                all_data[symbol] = []
        else:
            all_data[symbol] = []
    return all_data

def get_latest_analysis(data: list) -> dict:
    """Get the most recent analysis from the data"""
    if not data:
        return {}
    try:
        return sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)[0]
    except Exception:
        return data[-1] if data else {}

def get_current_price(symbol: str) -> float:
    """Get current price for a symbol"""
    try:
        from app.core.analysis.technical import get_market_data
        market_data = get_market_data(symbol, period='1d', interval='1m')
        if not market_data.empty:
            return float(market_data['Close'].iloc[-1])
        else:
            daily_data = get_market_data(symbol, period='5d', interval='1d')
            if not daily_data.empty:
                return float(daily_data['Close'].iloc[-1])
            return 0.0
    except Exception as e:
        logger.error(f"Error getting current price for {symbol}: {e}")
        return 0.0
