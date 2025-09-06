#!/usr/bin/env python3
"""
Updated IG Markets Paper Trader with OAuth authentication
Fixes session token issues by using OAuth Bearer tokens
"""

import os
import logging
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import uuid
import requests
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PaperTrade:
    trade_id: str
    prediction_id: str
    symbol: str
    action: str  # BUY, SELL, HOLD
    quantity: int
    entry_price: float
    entry_time: datetime
    confidence: float
    ig_markets_epic: str
    status: str = "OPEN"  # OPEN, CLOSED
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None

class IGMarketsPaperTrader:
    """
    Paper trading service using IG Markets demo account with OAuth authentication
    """
    
    def __init__(self, config_path: str = "config/ig_markets_config.json"):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.db_path = "data/ig_markets_paper_trades.db"
        
        # OAuth authentication tokens
        self.access_token = None
        self.refresh_token = None
        self.account_id = None
        self.token_expires_at = None
        
        # Legacy tokens (kept for backward compatibility)
        self.auth_token = None
        self.cst_token = None
        self.security_token = None
        
        # Initialize database
        self._init_database()
        
        # Authenticate with IG Markets
        self._authenticate()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load IG Markets configuration"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except FileNotFoundError:
            # Create default config if not exists
            default_config = {
                "api_key": os.getenv("IG_MARKETS_API_KEY", ""),
                "username": os.getenv("IG_MARKETS_USERNAME", ""),
                "password": os.getenv("IG_MARKETS_PASSWORD", ""),
                "account_id": os.getenv("IG_MARKETS_ACCOUNT_ID", ""),
                "base_url": "https://demo-api.ig.com",  # Demo environment
                "default_position_size": 100,
                "risk_percentage": 2.0,
                "max_positions": 10
            }
            
            # Create config directory if needed
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            logger.info(f"Created default config at {config_path}")
            logger.warning("Please update the configuration with your IG Markets credentials")
            return default_config
    
    def _init_database(self):
        """Initialize paper trading database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Paper trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS paper_trades (
                trade_id TEXT PRIMARY KEY,
                prediction_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                ig_markets_epic TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                entry_price REAL NOT NULL,
                entry_time DATETIME NOT NULL,
                confidence REAL NOT NULL,
                status TEXT DEFAULT 'OPEN',
                exit_price REAL,
                exit_time DATETIME,
                exit_reason TEXT,
                profit_loss REAL,
                profit_loss_pct REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
            )
        """)
        
        # Trade execution log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_execution_log (
                log_id TEXT PRIMARY KEY,
                trade_id TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                price REAL,
                status TEXT,
                ig_response TEXT,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES paper_trades(trade_id)
            )
        """)
        
        # Performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_summary (
                date TEXT PRIMARY KEY,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                losing_trades INTEGER DEFAULT 0,
                total_profit_loss REAL DEFAULT 0.0,
                win_rate REAL DEFAULT 0.0,
                avg_profit_per_trade REAL DEFAULT 0.0,
                max_drawdown REAL DEFAULT 0.0,
                sharpe_ratio REAL DEFAULT 0.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Database initialized: {self.db_path}")
    
    def _authenticate(self) -> bool:
        """Authenticate with IG Markets API using OAuth"""
        if not self.config.get("api_key") or not self.config.get("username"):
            logger.error("❌ IG Markets credentials not configured")
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
                auth_data = response.json()
                
                # Extract OAuth tokens
                oauth_token = auth_data.get('oauthToken', {})
                self.access_token = oauth_token.get('access_token')
                self.refresh_token = oauth_token.get('refresh_token')
                self.account_id = auth_data.get('accountId')
                
                # Calculate token expiry time (30 minutes from now)
                expires_in = int(oauth_token.get('expires_in', 30))
                self.token_expires_at = datetime.now() + timedelta(minutes=expires_in)
                
                # Update session headers for OAuth
                self.session.headers.update({
                    'X-IG-API-KEY': self.config['api_key'],
                    'Authorization': f'Bearer {self.access_token}',
                    'IG-ACCOUNT-ID': self.account_id,
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Version': '3'
                })
                
                logger.info("✅ Successfully authenticated with IG Markets (OAuth)")
                logger.info(f"Account ID: {self.account_id}")
                logger.info(f"Token expires at: {self.token_expires_at}")
                return True
            else:
                logger.error(f"❌ Authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def _check_token_expiry(self) -> bool:
        """Check if token needs refresh"""
        if not self.token_expires_at:
            return False
            
        # Refresh token if it expires in next 5 minutes
        return datetime.now() >= (self.token_expires_at - timedelta(minutes=5))
    
    def _refresh_access_token(self) -> bool:
        """Refresh OAuth access token"""
        if not self.refresh_token:
            logger.warning("No refresh token available, re-authenticating...")
            return self._authenticate()
            
        url = f"{self.config['base_url']}/gateway/deal/session/refresh-token"
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'X-IG-API-KEY': self.config['api_key'],
            'Authorization': f'Bearer {self.access_token}',
            'Version': '1'
        }
        
        data = {
            'refresh_token': self.refresh_token
        }
        
        try:
            response = self.session.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                auth_data = response.json()
                oauth_token = auth_data.get('oauthToken', {})
                
                self.access_token = oauth_token.get('access_token')
                self.refresh_token = oauth_token.get('refresh_token')
                
                expires_in = int(oauth_token.get('expires_in', 30))
                self.token_expires_at = datetime.now() + timedelta(minutes=expires_in)
                
                # Update session headers
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}'
                })
                
                logger.info("✅ Successfully refreshed OAuth token")
                return True
            else:
                logger.warning(f"Token refresh failed: {response.status_code}, re-authenticating...")
                return self._authenticate()
                
        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}")
            return self._authenticate()
    
    def get_market_price(self, epic: str) -> Optional[Dict]:
        """Get current market price from IG Markets"""
        # Check token expiry
        if self._check_token_expiry():
            if not self._refresh_access_token():
                logger.error("Failed to refresh token")
                return None
        
        url = f"{self.config['base_url']}/gateway/deal/markets/{epic}"
        
        try:
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get('snapshot', {})
                
                return {
                    'epic': epic,
                    'bid': market_data.get('bid'),
                    'offer': market_data.get('offer'),
                    'market_status': market_data.get('marketStatus'),
                    'timestamp': datetime.now().isoformat()
                }
            elif response.status_code == 404:
                logger.warning(f"Epic {epic} not found or not available")
                return None
            else:
                logger.error(f"❌ Failed to get price for {epic}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting market price: {e}")
            return None
    
    def map_asx_to_epic(self, asx_symbol: str) -> str:
        """Map ASX symbol to IG Markets EPIC - Updated mappings for demo environment"""
        # These are common EPICs that should be available in IG demo
        mapping = {
            'CBA.AX': 'IX.D.SPTSX60.DAILY.IP',  # Using indices as they're more reliable in demo
            'ANZ.AX': 'IX.D.DAX.DAILY.IP',
            'WBC.AX': 'IX.D.FTSE.DAILY.IP',
            'NAB.AX': 'IX.D.NASDAQ.DAILY.IP',
            'MQG.AX': 'IX.D.DOW.DAILY.IP',
            'BHP.AX': 'IX.D.HANGSENG.DAILY.IP',
            'CSL.AX': 'IX.D.NIKKEI.DAILY.IP',
            'QBE.AX': 'IX.D.SPTSX60.DAILY.IP',
            'SUN.AX': 'IX.D.CAC.DAILY.IP',
            'WOW.AX': 'IX.D.AEX.DAILY.IP'
        }
        
        epic = mapping.get(asx_symbol, 'IX.D.FTSE.DAILY.IP')  # Default to FTSE
        logger.info(f"Mapped {asx_symbol} to {epic}")
        return epic
    
    def execute_paper_trade(self, prediction: Dict) -> Optional[PaperTrade]:
        """Execute a paper trade based on prediction"""
        try:
            symbol = prediction['symbol']
            action = prediction['predicted_action']
            confidence = prediction['action_confidence']
            
            # Skip HOLD actions in paper trading
            if action == 'HOLD':
                logger.info(f"Skipping HOLD action for {symbol}")
                return None
            
            # Map to IG Markets EPIC
            epic = self.map_asx_to_epic(symbol)
            
            # Get current market price
            market_data = self.get_market_price(epic)
            if not market_data:
                logger.error(f"❌ Could not get market price for {epic}")
                return None
            
            # Calculate position size based on confidence
            base_size = self.config.get('default_position_size', 100)
            position_size = int(base_size * confidence)
            
            # Determine entry price (use offer for buy, bid for sell)
            entry_price = market_data['offer'] if action == 'BUY' else market_data['bid']
            
            # Create paper trade record
            trade = PaperTrade(
                trade_id=str(uuid.uuid4()),
                prediction_id=prediction['prediction_id'],
                symbol=symbol,
                action=action,
                quantity=position_size,
                entry_price=entry_price,
                entry_time=datetime.now(),
                confidence=confidence,
                ig_markets_epic=epic
            )
            
            # Store in database
            self._store_trade(trade)
            
            # Log execution
            self._log_execution(trade.trade_id, "OPEN", entry_price, "SUCCESS", market_data)
            
            logger.info(f"✅ Paper trade executed: {action} {position_size} {symbol} @ {entry_price}")
            return trade
            
        except Exception as e:
            logger.error(f"❌ Error executing paper trade: {e}")
            return None
    
    def evaluate_open_trades(self) -> List[PaperTrade]:
        """Evaluate all open paper trades for exit conditions"""
        open_trades = self._get_open_trades()
        closed_trades = []
        
        for trade in open_trades:
            try:
                # Get current market price
                market_data = self.get_market_price(trade.ig_markets_epic)
                if not market_data:
                    continue
                
                current_price = market_data['bid'] if trade.action == 'BUY' else market_data['offer']
                
                # Check exit conditions using the exit strategy engine
                exit_decision = self._check_exit_conditions(trade, current_price)
                
                if exit_decision['should_exit']:
                    closed_trade = self._close_trade(trade, current_price, exit_decision['reason'])
                    if closed_trade:
                        closed_trades.append(closed_trade)
                        
            except Exception as e:
                logger.error(f"❌ Error evaluating trade {trade.trade_id}: {e}")
        
        return closed_trades
    
    def _check_exit_conditions(self, trade: PaperTrade, current_price: float) -> Dict:
        """Check if trade should be exited using Phase 4 exit strategy"""
        try:
            # Import exit strategy engine
            import sys
            sys.path.append('phase4_development/exit_strategy')
            from ig_markets_exit_strategy_engine import ExitStrategyEngine
            
            engine = ExitStrategyEngine()
            
            # Use the correct method signature: individual parameters
            exit_conditions = engine.evaluate_position_exit(
                symbol=trade.symbol,
                entry_price=trade.entry_price,
                predicted_action=trade.action,
                prediction_confidence=trade.confidence,
                entry_timestamp=trade.entry_time.isoformat(),
                shares=trade.quantity
            )
            
            return {
                'should_exit': exit_conditions.get('should_exit', False),
                'reason': exit_conditions.get('exit_reason', 'NO_EXIT'),
                'confidence': exit_conditions.get('confidence', 0.0),
                'urgency': exit_conditions.get('urgency', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error checking exit conditions: {e}")
            # Fallback to simple profit/loss exit
            profit_pct = ((current_price - trade.entry_price) / trade.entry_price) * 100
            
            if profit_pct >= 2.5:  # 2.5% profit target
                return {'should_exit': True, 'reason': 'PROFIT_TARGET', 'confidence': 0.8}
            elif profit_pct <= -2.0:  # 2% stop loss
                return {'should_exit': True, 'reason': 'STOP_LOSS', 'confidence': 0.9}
            else:
                return {'should_exit': False, 'reason': 'NO_EXIT', 'confidence': 0.0}
    
    def _close_trade(self, trade: PaperTrade, exit_price: float, exit_reason: str) -> Optional[PaperTrade]:
        """Close a paper trade"""
        try:
            # Calculate profit/loss
            if trade.action == 'BUY':
                profit_loss = (exit_price - trade.entry_price) * trade.quantity
            else:  # SELL
                profit_loss = (trade.entry_price - exit_price) * trade.quantity
            
            profit_loss_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            if trade.action == 'SELL':
                profit_loss_pct = -profit_loss_pct
            
            # Update trade record
            trade.status = 'CLOSED'
            trade.exit_price = exit_price
            trade.exit_time = datetime.now()
            trade.exit_reason = exit_reason
            trade.profit_loss = profit_loss
            trade.profit_loss_pct = profit_loss_pct
            
            # Update in database
            self._update_trade(trade)
            
            # Log execution
            self._log_execution(trade.trade_id, "CLOSE", exit_price, "SUCCESS", None)
            
            logger.info(f"✅ Trade closed: {trade.symbol} P&L: ${profit_loss:.2f} ({profit_loss_pct:.2f}%)")
            return trade
            
        except Exception as e:
            logger.error(f"❌ Error closing trade: {e}")
            return None
    
    def _store_trade(self, trade: PaperTrade):
        """Store trade in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO paper_trades (
                trade_id, prediction_id, symbol, ig_markets_epic, action,
                quantity, entry_price, entry_time, confidence, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.trade_id, trade.prediction_id, trade.symbol, trade.ig_markets_epic,
            trade.action, trade.quantity, trade.entry_price, trade.entry_time.isoformat(),
            trade.confidence, trade.status
        ))
        
        conn.commit()
        conn.close()
    
    def _update_trade(self, trade: PaperTrade):
        """Update trade in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE paper_trades SET
                status = ?, exit_price = ?, exit_time = ?, exit_reason = ?,
                profit_loss = ?, profit_loss_pct = ?
            WHERE trade_id = ?
        """, (
            trade.status, trade.exit_price,
            trade.exit_time.isoformat() if trade.exit_time else None,
            trade.exit_reason, trade.profit_loss, trade.profit_loss_pct,
            trade.trade_id
        ))
        
        conn.commit()
        conn.close()
    
    def _get_open_trades(self) -> List[PaperTrade]:
        """Get all open trades"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM paper_trades WHERE status = 'OPEN'
        """)
        
        trades = []
        for row in cursor.fetchall():
            trade = PaperTrade(
                trade_id=row[0],
                prediction_id=row[1],
                symbol=row[2],
                ig_markets_epic=row[3],
                action=row[4],
                quantity=row[5],
                entry_price=row[6],
                entry_time=datetime.fromisoformat(row[7]),
                confidence=row[8],
                status=row[9]
            )
            trades.append(trade)
        
        conn.close()
        return trades
    
    def _log_execution(self, trade_id: str, action: str, price: float, status: str, ig_response: Any):
        """Log trade execution"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO trade_execution_log (
                log_id, trade_id, action, timestamp, price, status, ig_response
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()), trade_id, action, datetime.now().isoformat(),
            price, status, json.dumps(ig_response) if ig_response else None
        ))
        
        conn.commit()
        conn.close()
    
    def get_performance_summary(self, days: int = 30) -> Dict:
        """Get performance summary"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).date()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(profit_loss) as total_profit_loss,
                AVG(profit_loss) as avg_profit_per_trade,
                AVG(profit_loss_pct) as avg_return_pct,
                MIN(profit_loss_pct) as max_drawdown
            FROM paper_trades 
            WHERE status = 'CLOSED' 
            AND date(entry_time) >= ?
        """, (start_date,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            win_rate = (row[1] / row[0]) * 100 if row[0] > 0 else 0
            return {
                'total_trades': row[0],
                'winning_trades': row[1],
                'losing_trades': row[2],
                'win_rate': win_rate,
                'total_profit_loss': row[3] or 0,
                'avg_profit_per_trade': row[4] or 0,
                'avg_return_pct': row[5] or 0,
                'max_drawdown': row[6] or 0
            }
        else:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit_loss': 0,
                'avg_profit_per_trade': 0,
                'avg_return_pct': 0,
                'max_drawdown': 0
            }
    
    def process_new_predictions(self) -> List[PaperTrade]:
        """Process new predictions and execute paper trades"""
        # Get untraded predictions using separate database queries
        predictions = self._get_untraded_predictions()
        
        # Execute paper trades for new predictions
        executed_trades = []
        for prediction in predictions:
            trade = self.execute_paper_trade(prediction)
            if trade:
                executed_trades.append(trade)
        
        return executed_trades
    
    def _get_untraded_predictions(self) -> List[Dict]:
        """Get recent predictions that haven't been paper traded yet"""
        
        # Step 1: Get existing paper trade prediction IDs
        existing_prediction_ids = set()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT prediction_id FROM paper_trades")
            for row in cursor.fetchall():
                existing_prediction_ids.add(row[0])
            
            conn.close()
            logger.info(f"Found {len(existing_prediction_ids)} existing paper trades")
            
        except Exception as e:
            logger.warning(f"Could not read paper trades database: {e}")
            existing_prediction_ids = set()
        
        # Step 2: Get recent predictions
        main_db = "data/trading_predictions.db"
        untraded_predictions = []
        
        try:
            conn = sqlite3.connect(main_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM predictions 
                WHERE prediction_timestamp > datetime('now', '-4 hours')
                AND predicted_action IN ('BUY', 'SELL')
                ORDER BY prediction_timestamp DESC
            """)
            
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                prediction = dict(zip(columns, row))
                
                # Only include if not already traded
                if prediction['prediction_id'] not in existing_prediction_ids:
                    untraded_predictions.append(prediction)
            
            conn.close()
            logger.info(f"Found {len(untraded_predictions)} new predictions to trade")
            
        except Exception as e:
            logger.error(f"Error reading predictions database: {e}")
            return []
        
        return untraded_predictions

def main():
    """Main execution function"""
    print("🎯 IG Markets Paper Trading Service (OAuth)")
    print("=" * 50)
    
    # Initialize paper trader
    trader = IGMarketsPaperTrader()
    
    # Process new predictions
    print("\n📊 Processing new predictions...")
    new_trades = trader.process_new_predictions()
    print(f"✅ Executed {len(new_trades)} new paper trades")
    
    # Evaluate open trades
    print("\n🔍 Evaluating open trades...")
    closed_trades = trader.evaluate_open_trades()
    print(f"✅ Closed {len(closed_trades)} trades")
    
    # Show performance summary
    print("\n📈 Performance Summary (Last 30 days):")
    performance = trader.get_performance_summary()
    print(f"Total Trades: {performance['total_trades']}")
    print(f"Win Rate: {performance['win_rate']:.1f}%")
    print(f"Total P&L: ${performance['total_profit_loss']:.2f}")
    print(f"Avg Return: {performance['avg_return_pct']:.2f}%")
    
    print("\n✅ Paper trading service completed!")

if __name__ == "__main__":
    main()
