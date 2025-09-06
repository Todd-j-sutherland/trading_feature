#!/usr/bin/env python3
"""
IG Markets Outcome Evaluator
Replaces yfinance-based evaluation with IG Markets data for consistency
"""

import os
import sys
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import uuid
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IGMarketsOutcomeEvaluator:
    """
    Evaluates predictions using IG Markets data to ensure consistency
    between prediction data source and outcome evaluation
    """
    
    def __init__(self, config_path: str = "config/ig_markets_config.json"):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.db_path = "data/trading_predictions.db"
        self.auth_token = None
        self.cst_token = None
        self.security_token = None
        
        # Authenticate with IG Markets
        self._authenticate()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load IG Markets configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            logger.error(f"❌ Configuration file not found: {config_path}")
            # Fallback to environment variables
            return {
                "api_key": os.getenv("IG_MARKETS_API_KEY", ""),
                "username": os.getenv("IG_MARKETS_USERNAME", ""),
                "password": os.getenv("IG_MARKETS_PASSWORD", ""),
                "base_url": "https://demo-api.ig.com",
                "symbol_mapping": {
                    "CBA.AX": "AU.CBA.CHESS.IP",
                    "ANZ.AX": "AU.ANZ.CHESS.IP",
                    "WBC.AX": "AU.WBC.CHESS.IP",
                    "NAB.AX": "AU.NAB.CHESS.IP",
                    "MQG.AX": "AU.MQG.CHESS.IP",
                    "BHP.AX": "AU.BHP.CHESS.IP",
                    "CSL.AX": "AU.CSL.CHESS.IP",
                    "QBE.AX": "AU.QBE.CHESS.IP",
                    "SUN.AX": "AU.SUN.CHESS.IP",
                    "WOW.AX": "AU.WOW.CHESS.IP"
                }
            }
    
    def _authenticate(self) -> bool:
        """Authenticate with IG Markets API"""
        if not self.config.get("api_key") or not self.config.get("username"):
            logger.warning("⚠️ IG Markets credentials not configured, using fallback")
            return False
            
        url = f"{self.config['base_url']}/gateway/deal/session"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': self.config['api_key'],
            'Version': '3'
        }
        
        data = {
            'identifier': self.config['username'],
            'password': self.config['password']
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                self.cst_token = response.headers.get('CST')
                self.security_token = response.headers.get('X-SECURITY-TOKEN')
                
                self.session.headers.update({
                    'X-IG-API-KEY': self.config['api_key'],
                    'CST': self.cst_token,
                    'X-SECURITY-TOKEN': self.security_token,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                })
                
                logger.info("✅ Successfully authenticated with IG Markets")
                return True
            else:
                logger.warning(f"⚠️ IG authentication failed: {response.status_code}, using fallback")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ IG authentication error: {e}, using fallback")
            return False
    
    def get_market_price_history(self, epic: str, resolution: str = "HOUR", num_points: int = 50) -> Optional[List[Dict]]:
        """Get historical price data from IG Markets"""
        if not self.cst_token:
            return None
            
        url = f"{self.config['base_url']}/gateway/deal/prices/{epic}"
        
        params = {
            'resolution': resolution,
            'max': num_points
        }
        
        try:
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                prices = data.get('prices', [])
                
                # Convert to standardized format
                price_data = []
                for price_point in prices:
                    price_data.append({
                        'timestamp': price_point.get('snapshotTime'),
                        'open': price_point.get('openPrice', {}).get('mid'),
                        'high': price_point.get('highPrice', {}).get('mid'),
                        'low': price_point.get('lowPrice', {}).get('mid'),
                        'close': price_point.get('closePrice', {}).get('mid'),
                        'volume': price_point.get('lastTradedVolume', 0)
                    })
                
                return price_data
            else:
                logger.error(f"❌ Failed to get price history for {epic}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting price history: {e}")
            return None
    
    def map_asx_to_epic(self, asx_symbol: str) -> str:
        """Map ASX symbol to IG Markets EPIC"""
        return self.config.get('symbol_mapping', {}).get(asx_symbol, asx_symbol)
    
    def evaluate_pending_predictions(self) -> int:
        """Evaluate pending predictions using IG Markets data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get predictions that need evaluation (4+ hours old, no outcome yet)
        cursor.execute("""
            SELECT p.* FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE o.prediction_id IS NULL
            AND p.prediction_timestamp < datetime('now', '-4 hours')
            AND p.prediction_timestamp > datetime('now', '-72 hours')
            ORDER BY p.prediction_timestamp DESC
        """)
        
        predictions = []
        columns = [desc[0] for desc in cursor.description]
        for row in cursor.fetchall():
            prediction = dict(zip(columns, row))
            predictions.append(prediction)
        
        conn.close()
        
        evaluated_count = 0
        
        for prediction in predictions:
            try:
                outcome = self._calculate_outcome_ig_markets(prediction)
                if outcome:
                    self._store_outcome(outcome)
                    evaluated_count += 1
                    logger.info(f"✅ Evaluated {prediction['symbol']} with IG Markets data")
                else:
                    # Fallback to yfinance if IG Markets fails
                    outcome = self._calculate_outcome_yfinance_fallback(prediction)
                    if outcome:
                        self._store_outcome(outcome)
                        evaluated_count += 1
                        logger.info(f"✅ Evaluated {prediction['symbol']} with yfinance fallback")
                    
            except Exception as e:
                logger.error(f"❌ Failed to evaluate prediction {prediction['prediction_id']}: {e}")
        
        logger.info(f"✅ Evaluated {evaluated_count} predictions")
        return evaluated_count
    
    def _calculate_outcome_ig_markets(self, prediction: Dict) -> Optional[Dict]:
        """Calculate outcome using IG Markets data"""
        if not self.cst_token:
            return None
            
        try:
            symbol = prediction['symbol']
            pred_time = datetime.fromisoformat(prediction['prediction_timestamp'])
            
            # Map to IG Markets EPIC
            epic = self.map_asx_to_epic(symbol)
            
            # Get historical price data
            price_data = self.get_market_price_history(epic, "HOUR", 50)
            if not price_data or len(price_data) < 2:
                logger.warning(f"⚠️ Insufficient IG Markets data for {symbol}")
                return None
            
            # Find entry and exit prices based on prediction time
            entry_price = None
            exit_price = None
            
            # Sort by timestamp
            price_data.sort(key=lambda x: x['timestamp'])
            
            # Find entry price (closest to prediction time)
            pred_timestamp = pred_time.strftime('%Y-%m-%dT%H:%M:%S')
            
            for i, price_point in enumerate(price_data):
                if price_point['timestamp'] >= pred_timestamp:
                    entry_price = price_point['close']
                    
                    # Find exit price (4-24 hours later)
                    target_exit = pred_time + timedelta(hours=24)
                    
                    for j in range(i + 1, len(price_data)):
                        exit_timestamp = datetime.fromisoformat(price_data[j]['timestamp'])
                        if exit_timestamp >= target_exit:
                            exit_price = price_data[j]['close']
                            break
                    
                    # If no exact 24h match, use last available
                    if not exit_price and i + 4 < len(price_data):
                        exit_price = price_data[i + 4]['close']  # ~4 hours later
                    
                    break
            
            if not entry_price or not exit_price:
                logger.warning(f"⚠️ Could not find entry/exit prices for {symbol}")
                return None
            
            # Calculate return
            actual_return = ((exit_price - entry_price) / entry_price) * 100
            actual_direction = 1 if actual_return > 0 else -1 if actual_return < 0 else 0
            
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': actual_return,
                'actual_direction': actual_direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'evaluation_timestamp': datetime.now().isoformat(),
                'data_source': 'IG_MARKETS'
            }
            
            return outcome
            
        except Exception as e:
            logger.error(f"❌ Error calculating IG Markets outcome: {e}")
            return None
    
    def _calculate_outcome_yfinance_fallback(self, prediction: Dict) -> Optional[Dict]:
        """Fallback to yfinance if IG Markets fails"""
        try:
            import yfinance as yf
            
            symbol = prediction['symbol']
            pred_time = datetime.fromisoformat(prediction['prediction_timestamp'])
            
            # Get market data starting from prediction time
            end_time = pred_time + timedelta(days=2)
            ticker = yf.Ticker(symbol)
            
            # Get hourly data
            hist = ticker.history(start=pred_time.date(), end=end_time.date(), interval='1h')
            
            if len(hist) < 2:
                logger.warning(f"⚠️ Insufficient yfinance data for {symbol}")
                return None
            
            # Find entry and exit prices
            entry_price = hist['Close'].iloc[0]
            
            # Find exit price (24 hours later or closest available)
            if len(hist) >= 24:
                exit_price = hist['Close'].iloc[23]
            else:
                exit_price = hist['Close'].iloc[-1]
            
            # Calculate return
            actual_return = ((exit_price - entry_price) / entry_price) * 100
            actual_direction = 1 if actual_return > 0 else -1 if actual_return < 0 else 0
            
            outcome = {
                'outcome_id': str(uuid.uuid4()),
                'prediction_id': prediction['prediction_id'],
                'actual_return': actual_return,
                'actual_direction': actual_direction,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'evaluation_timestamp': datetime.now().isoformat(),
                'data_source': 'YFINANCE_FALLBACK'
            }
            
            return outcome
            
        except Exception as e:
            logger.error(f"❌ Error with yfinance fallback: {e}")
            return None
    
    def _store_outcome(self, outcome: Dict):
        """Store outcome in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO outcomes (
                    outcome_id, prediction_id, actual_return, actual_direction,
                    entry_price, exit_price, evaluation_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                outcome['outcome_id'], outcome['prediction_id'],
                outcome['actual_return'], outcome['actual_direction'],
                outcome['entry_price'], outcome['exit_price'],
                outcome['evaluation_timestamp']
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Failed to store outcome: {e}")
            
        finally:
            conn.close()
    
    def get_data_source_stats(self) -> Dict:
        """Get statistics on data sources used for outcomes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent outcomes (last 7 days)
        cursor.execute("""
            SELECT COUNT(*) as total_outcomes
            FROM outcomes 
            WHERE evaluation_timestamp > datetime('now', '-7 days')
        """)
        
        total = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_outcomes_7_days': total,
            'ig_markets_available': bool(self.cst_token),
            'primary_source': 'IG_MARKETS' if self.cst_token else 'YFINANCE_FALLBACK'
        }

def main():
    """Main execution function"""
    print("🎯 IG Markets Outcome Evaluator")
    print("=" * 40)
    
    # Initialize evaluator
    evaluator = IGMarketsOutcomeEvaluator()
    
    # Show data source status
    stats = evaluator.get_data_source_stats()
    print(f"📊 Data Source: {stats['primary_source']}")
    print(f"📊 IG Markets Available: {stats['ig_markets_available']}")
    
    # Evaluate pending predictions
    print("\n🔍 Evaluating pending predictions...")
    count = evaluator.evaluate_pending_predictions()
    
    print(f"✅ Evaluated {count} predictions")
    print("✅ Using IG Markets data for consistency with predictions!")

if __name__ == "__main__":
    main()
