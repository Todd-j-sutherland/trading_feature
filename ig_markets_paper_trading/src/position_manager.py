#!/usr/bin/env python3
"""
Position Manager - Handles position limits and fund management
Ensures only 1 position per symbol and checks available funds before trading
"""

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class Position:
    position_id: str
    symbol: str
    epic: str
    action: str
    quantity: int
    entry_price: float
    entry_time: datetime
    confidence: float
    status: str = "OPEN"
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None

@dataclass
class AccountBalance:
    total_balance: float
    available_funds: float
    used_funds: float
    unrealized_pnl: float
    realized_pnl: float

class PositionManager:
    """
    Manages positions and account funds for paper trading
    Enforces position limits and fund availability checks
    """
    
    def __init__(self, db_path: str = "data/paper_trading.db", config_path: str = "config/trading_parameters.json"):
        self.db_path = db_path
        self.config = self._load_config(config_path)
        self._init_database()
        self._init_account()
        
    def _load_config(self, config_path: str) -> Dict:
        """Load trading parameters configuration"""
        try:
            config_full_path = os.path.join(os.path.dirname(__file__), '..', config_path)
            with open(config_full_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Default configuration if config file not found"""
        return {
            "account": {"starting_balance": 10000.0},
            "position_management": {
                "max_positions": 10,
                "max_positions_per_symbol": 1,
                "max_position_size": 1000.0
            },
            "risk_management": {
                "max_risk_per_trade": 0.02,
                "max_account_risk": 0.20
            },
            "trading_rules": {
                "min_confidence_threshold": 0.6,
                "require_funds_check": True
            }
        }
    
    def _init_database(self):
        """Initialize SQLite database for position tracking"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Account balance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_balance (
                date TEXT PRIMARY KEY,
                total_balance REAL NOT NULL,
                available_funds REAL NOT NULL,
                used_funds REAL NOT NULL,
                unrealized_pnl REAL DEFAULT 0.0,
                realized_pnl REAL DEFAULT 0.0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Positions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                position_id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                epic TEXT NOT NULL,
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
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Position limits tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS position_limits (
                symbol TEXT PRIMARY KEY,
                open_positions INTEGER DEFAULT 0,
                last_trade_time DATETIME,
                total_trades INTEGER DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Trade activity log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_log (
                log_id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                action TEXT NOT NULL,
                symbol TEXT,
                details TEXT,
                result TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Position manager database initialized: {self.db_path}")
    
    def _init_account(self):
        """Initialize account with starting balance if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Check if account already exists
        cursor.execute("SELECT * FROM account_balance WHERE date = ?", (today,))
        existing = cursor.fetchone()
        
        if not existing:
            starting_balance = self.config["account"]["starting_balance"]
            cursor.execute("""
                INSERT INTO account_balance (date, total_balance, available_funds, used_funds)
                VALUES (?, ?, ?, ?)
            """, (today, starting_balance, starting_balance, 0.0))
            
            logger.info(f"✅ Account initialized with balance: ${starting_balance:,.2f}")
        
        conn.commit()
        conn.close()
    
    def get_account_balance(self) -> AccountBalance:
        """Get current account balance and fund allocation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        
        # Get latest balance
        cursor.execute("""
            SELECT total_balance, available_funds, used_funds, unrealized_pnl, realized_pnl
            FROM account_balance 
            WHERE date = ?
        """, (today,))
        
        row = cursor.fetchone()
        if not row:
            # Create today's balance based on yesterday's
            cursor.execute("""
                SELECT total_balance, available_funds, used_funds, unrealized_pnl, realized_pnl
                FROM account_balance 
                ORDER BY date DESC LIMIT 1
            """)
            
            prev_row = cursor.fetchone()
            if prev_row:
                cursor.execute("""
                    INSERT INTO account_balance (date, total_balance, available_funds, used_funds, unrealized_pnl, realized_pnl)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (today, prev_row[0], prev_row[1], prev_row[2], 0.0, prev_row[4]))
                row = (prev_row[0], prev_row[1], prev_row[2], 0.0, prev_row[4])
            else:
                # Initialize with starting balance
                starting_balance = self.config["account"]["starting_balance"]
                cursor.execute("""
                    INSERT INTO account_balance (date, total_balance, available_funds, used_funds, unrealized_pnl, realized_pnl)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (today, starting_balance, starting_balance, 0.0, 0.0, 0.0))
                row = (starting_balance, starting_balance, 0.0, 0.0, 0.0)
        
        conn.commit()
        conn.close()
        
        return AccountBalance(
            total_balance=row[0],
            available_funds=row[1],
            used_funds=row[2],
            unrealized_pnl=row[3],
            realized_pnl=row[4]
        )
    
    def can_open_position(self, symbol: str, required_funds: float) -> Tuple[bool, str]:
        """Check if a new position can be opened for this symbol"""
        
        # Check if symbol already has open position
        if self.has_open_position(symbol):
            return False, f"Symbol {symbol} already has an open position (1 position per symbol limit)"
        
        # Check available funds
        balance = self.get_account_balance()
        if required_funds > balance.available_funds:
            return False, f"Insufficient funds: need ${required_funds:,.2f}, available ${balance.available_funds:,.2f}"
        
        # Check maximum positions limit
        open_positions = self.get_open_positions_count()
        max_positions = self.config["position_management"]["max_positions"]
        if open_positions >= max_positions:
            return False, f"Maximum positions reached: {open_positions}/{max_positions}"
        
        # Check position size limits
        max_position_size = self.config["position_management"]["max_position_size"]
        if required_funds > max_position_size:
            return False, f"Position size too large: ${required_funds:,.2f} > ${max_position_size:,.2f}"
        
        # Check risk limits
        max_risk = self.config["risk_management"]["max_risk_per_trade"]
        max_risk_amount = balance.total_balance * max_risk
        if required_funds > max_risk_amount:
            return False, f"Position exceeds risk limit: ${required_funds:,.2f} > ${max_risk_amount:,.2f} ({max_risk*100}%)"
        
        return True, "Position can be opened"
    
    def has_open_position(self, symbol: str) -> bool:
        """Check if symbol already has an open position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM positions 
            WHERE symbol = ? AND status = 'OPEN'
        """, (symbol,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def get_open_positions_count(self) -> int:
        """Get total number of open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM positions WHERE status = 'OPEN'")
        count = cursor.fetchone()[0]
        
        conn.close()
        return count
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT position_id, symbol, epic, action, quantity, entry_price, 
                   entry_time, confidence, status, exit_price, exit_time, 
                   exit_reason, profit_loss, profit_loss_pct
            FROM positions 
            WHERE status = 'OPEN'
        """)
        
        positions = []
        for row in cursor.fetchall():
            position = Position(
                position_id=row[0],
                symbol=row[1],
                epic=row[2],
                action=row[3],
                quantity=row[4],
                entry_price=row[5],
                entry_time=datetime.fromisoformat(row[6]),
                confidence=row[7],
                status=row[8],
                exit_price=row[9],
                exit_time=datetime.fromisoformat(row[10]) if row[10] else None,
                exit_reason=row[11],
                profit_loss=row[12],
                profit_loss_pct=row[13]
            )
            positions.append(position)
        
        conn.close()
        return positions
    
    def calculate_position_size(self, confidence: float, current_price: float, available_funds: float) -> int:
        """Calculate position size based on confidence and available funds"""
        
        # Base position size calculation
        max_position_value = min(
            available_funds,
            self.config["position_management"]["max_position_size"],
            available_funds * self.config["risk_management"]["max_risk_per_trade"]
        )
        
        # Adjust based on confidence (confidence between 0.6 and 1.0)
        confidence_multiplier = max(0.1, min(1.0, (confidence - 0.5) * 2))  # Scale 0.6-1.0 to 0.2-1.0
        adjusted_position_value = max_position_value * confidence_multiplier
        
        # Calculate quantity (minimum 100 shares)
        quantity = max(100, int(adjusted_position_value / current_price))
        
        # Ensure we don't exceed available funds
        total_cost = quantity * current_price
        if total_cost > available_funds:
            quantity = int(available_funds / current_price)
        
        return max(0, quantity)
    
    def reserve_funds(self, amount: float) -> bool:
        """Reserve funds for a new position"""
        balance = self.get_account_balance()
        
        if amount > balance.available_funds:
            return False
        
        new_available = balance.available_funds - amount
        new_used = balance.used_funds + amount
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        cursor.execute("""
            UPDATE account_balance 
            SET available_funds = ?, used_funds = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        """, (new_available, new_used, today))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💰 Reserved ${amount:,.2f} - Available: ${new_available:,.2f}, Used: ${new_used:,.2f}")
        return True
    
    def release_funds(self, amount: float, realized_pnl: float = 0.0):
        """Release funds from a closed position"""
        balance = self.get_account_balance()
        
        new_used = max(0, balance.used_funds - amount)
        new_available = balance.available_funds + amount + realized_pnl
        new_total = balance.total_balance + realized_pnl
        new_realized_pnl = balance.realized_pnl + realized_pnl
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date().isoformat()
        cursor.execute("""
            UPDATE account_balance 
            SET total_balance = ?, available_funds = ?, used_funds = ?, 
                realized_pnl = ?, updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        """, (new_total, new_available, new_used, new_realized_pnl, today))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💰 Released ${amount:,.2f} + P&L ${realized_pnl:,.2f} - Available: ${new_available:,.2f}")
    
    def open_position(self, position: Position) -> bool:
        """Open a new position"""
        # Calculate required funds
        required_funds = position.quantity * position.entry_price
        
        # Check if position can be opened
        can_open, reason = self.can_open_position(position.symbol, required_funds)
        if not can_open:
            logger.warning(f"❌ Cannot open position for {position.symbol}: {reason}")
            return False
        
        # Reserve funds
        if not self.reserve_funds(required_funds):
            logger.error(f"❌ Failed to reserve funds for {position.symbol}")
            return False
        
        # Store position in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO positions (
                position_id, symbol, epic, action, quantity, entry_price,
                entry_time, confidence, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position.position_id, position.symbol, position.epic, position.action,
            position.quantity, position.entry_price, position.entry_time.isoformat(),
            position.confidence, position.status
        ))
        
        # Update position limits tracking
        cursor.execute("""
            INSERT OR REPLACE INTO position_limits (symbol, open_positions, last_trade_time, total_trades)
            VALUES (?, 1, ?, COALESCE((SELECT total_trades FROM position_limits WHERE symbol = ?), 0) + 1)
        """, (position.symbol, position.entry_time.isoformat(), position.symbol))
        
        # Log the action
        self.log_action("OPEN_POSITION", position.symbol, 
                       f"Opened {position.action} position: {position.quantity} @ ${position.entry_price}", 
                       "SUCCESS")
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Opened position: {position.action} {position.quantity} {position.symbol} @ ${position.entry_price}")
        return True
    
    def close_position(self, position_id: str, exit_price: float, exit_reason: str) -> bool:
        """Close an existing position"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get position details
        cursor.execute("""
            SELECT position_id, symbol, epic, action, quantity, entry_price, 
                   entry_time, confidence, status
            FROM positions WHERE position_id = ? AND status = 'OPEN'
        """, (position_id,))
        
        row = cursor.fetchone()
        if not row:
            logger.error(f"❌ Position not found or already closed: {position_id}")
            conn.close()
            return False
        
        # Calculate profit/loss
        symbol, action, quantity, entry_price = row[1], row[3], row[4], row[5]
        
        if action == 'BUY':
            profit_loss = (exit_price - entry_price) * quantity
        else:  # SELL
            profit_loss = (entry_price - exit_price) * quantity
        
        profit_loss_pct = ((exit_price - entry_price) / entry_price) * 100
        if action == 'SELL':
            profit_loss_pct = -profit_loss_pct
        
        # Update position record
        exit_time = datetime.now()
        cursor.execute("""
            UPDATE positions SET
                status = 'CLOSED', exit_price = ?, exit_time = ?, exit_reason = ?,
                profit_loss = ?, profit_loss_pct = ?, updated_at = CURRENT_TIMESTAMP
            WHERE position_id = ?
        """, (exit_price, exit_time.isoformat(), exit_reason, profit_loss, profit_loss_pct, position_id))
        
        # Update position limits tracking
        cursor.execute("""
            UPDATE position_limits 
            SET open_positions = 0, last_trade_time = ?, updated_at = CURRENT_TIMESTAMP
            WHERE symbol = ?
        """, (exit_time.isoformat(), symbol))
        
        # Log the action
        self.log_action("CLOSE_POSITION", symbol,
                       f"Closed {action} position: {quantity} @ ${exit_price} (P&L: ${profit_loss:.2f})",
                       "SUCCESS")
        
        conn.commit()
        conn.close()
        
        # Release funds
        original_funds = quantity * entry_price
        self.release_funds(original_funds, profit_loss)
        
        logger.info(f"✅ Closed position: {symbol} P&L: ${profit_loss:.2f} ({profit_loss_pct:.2f}%)")
        return True
    
    def log_action(self, action: str, symbol: str, details: str, result: str):
        """Log trading action"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        log_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{action}_{symbol}"
        
        cursor.execute("""
            INSERT INTO trade_log (log_id, timestamp, action, symbol, details, result)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, datetime.now().isoformat(), action, symbol, details, result))
        
        conn.commit()
        conn.close()
    
    def get_performance_summary(self) -> Dict:
        """Get performance summary for all closed positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(profit_loss) as total_profit_loss,
                AVG(profit_loss) as avg_profit_per_trade,
                AVG(profit_loss_pct) as avg_return_pct,
                MIN(profit_loss_pct) as max_drawdown,
                MAX(profit_loss_pct) as max_gain
            FROM positions 
            WHERE status = 'CLOSED'
        """)
        
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
                'max_drawdown': row[6] or 0,
                'max_gain': row[7] or 0
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
                'max_drawdown': 0,
                'max_gain': 0
            }
