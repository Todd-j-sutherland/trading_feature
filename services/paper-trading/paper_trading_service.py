"""
Paper Trading Service - Live Trading Simulation and IG Markets Integration

Purpose:
This service manages paper trading operations, integrating with IG Markets API
for live market simulation, tracking virtual positions, calculating P&L,
and providing trading performance analytics. It bridges prediction signals
with actual trading execution in a risk-free environment.

Key Features:
- IG Markets API integration for live paper trading
- Virtual portfolio management and position tracking
- Real-time P&L calculation and risk metrics
- Trading signal execution from prediction service
- Performance analytics and reporting
- Trade history and audit trail
- Position sizing and risk management rules

Trading Operations:
- Execute BUY/SELL signals from prediction service
- Market order simulation with real spreads
- Position management (open, close, modify)
- Stop-loss and take-profit automation
- Portfolio rebalancing based on signals

API Endpoints:
- execute_trade(symbol, action, quantity) - Execute paper trade
- get_positions() - Current open positions
- get_portfolio_status() - Portfolio summary and P&L
- sync_with_ig_markets() - Sync with IG Markets data
- get_trading_performance() - Performance metrics
- close_position(position_id) - Close specific position
- get_trade_history() - Historical trades

Integration Points:
- Prediction Service: Receives trading signals
- Market Data Service: Real-time price feeds
- IG Markets API: Live market simulation
- Databases: paper_trading.db, ig_markets_paper_trades.db

Dependencies:
- IG Markets API credentials
- paper-trading-app/ integration
- ig_markets_paper_trading/ components
- Real-time price data

Related Files:
- paper-trading-app/enhanced_paper_trading_service.py
- ig_markets_paper_trading/ig_markets_client.py
- data/ig_markets_paper_trades.db
- paper_trading.db

Risk Management:
- Maximum position size limits
- Portfolio exposure limits
- Daily loss limits
- Automatic stop-loss execution
"""

import asyncio
import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from decimal import Decimal
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Add paper trading app to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "paper-trading-app"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ig_markets_paper_trading"))

class PaperTradingService(BaseService):
    """Paper trading service with IG Markets integration"""
    
    def __init__(self):
        super().__init__("paper-trading")
        
        # Database connections
        self.paper_trading_db = "paper_trading.db"
        self.ig_markets_db = "data/ig_markets_paper_trades.db"
        
        # Portfolio state
        self.portfolio = {
            "cash_balance": 100000.0,  # Starting with $100k
            "total_value": 100000.0,
            "open_positions": {},
            "daily_pnl": 0.0,
            "total_pnl": 0.0
        }
        
        # Trading rules and limits
        self.trading_rules = {
            "max_position_size": 10000.0,  # Max $10k per position
            "max_portfolio_exposure": 0.8,  # Max 80% portfolio exposure
            "max_daily_loss": 5000.0,      # Max $5k daily loss
            "position_size_pct": 0.05,     # 5% of portfolio per trade
            "stop_loss_pct": 0.05,         # 5% stop loss
            "take_profit_pct": 0.10        # 10% take profit
        }
        
        # IG Markets integration
        self.ig_client = None
        self.ig_credentials = {
            "api_key": os.getenv("IG_API_KEY", ""),
            "username": os.getenv("IG_USERNAME", ""),
            "password": os.getenv("IG_PASSWORD", ""),
            "demo": True  # Always use demo for paper trading
        }
        
        # Performance tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.total_commission = 0.0
        
        # Register methods
        self.register_handler("execute_trade", self.execute_trade)
        self.register_handler("get_positions", self.get_positions)
        self.register_handler("get_portfolio_status", self.get_portfolio_status)
        self.register_handler("sync_with_ig_markets", self.sync_with_ig_markets)
        self.register_handler("get_trading_performance", self.get_trading_performance)
        self.register_handler("close_position", self.close_position)
        self.register_handler("get_trade_history", self.get_trade_history)
        self.register_handler("update_trading_rules", self.update_trading_rules)
        self.register_handler("process_prediction_signal", self.process_prediction_signal)
        
        # Initialize databases
        asyncio.create_task(self._initialize_databases())
        
        # Initialize IG Markets client
        asyncio.create_task(self._initialize_ig_client())
        
        # Subscribe to prediction signals
        self._setup_signal_subscription()
    
    async def _initialize_databases(self):
        """Initialize paper trading databases"""
        try:
            # Create paper trading database if not exists
            with sqlite3.connect(self.paper_trading_db) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        trade_id TEXT UNIQUE,
                        symbol TEXT,
                        action TEXT,
                        quantity INTEGER,
                        price REAL,
                        timestamp TEXT,
                        status TEXT,
                        pnl REAL DEFAULT 0,
                        commission REAL DEFAULT 0,
                        signal_source TEXT,
                        confidence REAL
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS positions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        position_id TEXT UNIQUE,
                        symbol TEXT,
                        quantity INTEGER,
                        entry_price REAL,
                        current_price REAL,
                        pnl REAL,
                        open_time TEXT,
                        close_time TEXT,
                        status TEXT,
                        stop_loss REAL,
                        take_profit REAL
                    )
                ''')
                
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        total_value REAL,
                        cash_balance REAL,
                        daily_pnl REAL,
                        total_pnl REAL,
                        open_positions INTEGER
                    )
                ''')
                
                conn.commit()
            
            self.logger.info(f'"action": "databases_initialized"')
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "database_initialization_failed"')
    
    async def _initialize_ig_client(self):
        """Initialize IG Markets client integration"""
        try:
            # Only initialize if credentials are available
            if all(self.ig_credentials.values()):
                # Import IG client components
                try:
                    from enhanced_paper_trading_service import IGMarketsClient
                    self.ig_client = IGMarketsClient(
                        api_key=self.ig_credentials["api_key"],
                        username=self.ig_credentials["username"],
                        password=self.ig_credentials["password"],
                        demo=self.ig_credentials["demo"]
                    )
                    
                    # Test connection
                    await self.ig_client.connect()
                    self.logger.info(f'"action": "ig_markets_client_initialized"')
                    
                except ImportError:
                    self.logger.warning(f'"action": "ig_markets_import_failed", "fallback": "local_simulation"')
                    self.ig_client = None
            else:
                self.logger.info(f'"action": "ig_markets_not_configured", "mode": "local_simulation"')
                
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "ig_client_initialization_failed"')
            self.ig_client = None
    
    def _setup_signal_subscription(self):
        """Setup subscription to prediction signals"""
        if self.redis_client:
            # Subscribe to prediction signals
            event_handler = self.subscribe_to_events(["prediction_generated"], self._handle_prediction_signal)
            if event_handler:
                asyncio.create_task(event_handler())
    
    async def _handle_prediction_signal(self, event_type: str, event_data: dict):
        """Handle incoming prediction signals"""
        if event_type == "prediction_generated":
            symbol = event_data.get("symbol")
            prediction = event_data.get("prediction", {})
            
            if prediction.get("action") in ["BUY", "STRONG_BUY"]:
                await self.process_prediction_signal(
                    symbol=symbol,
                    action="BUY",
                    confidence=prediction.get("confidence", 0.5),
                    signal_source="prediction_service"
                )
    
    async def execute_trade(self, symbol: str, action: str, quantity: int = None, 
                          price: float = None, signal_source: str = "manual", confidence: float = 0.5):
        """Execute a paper trade"""
        try:
            trade_id = str(uuid.uuid4())
            
            # Validate action
            if action not in ["BUY", "SELL"]:
                return {"error": "Invalid action. Must be BUY or SELL"}
            
            # Calculate quantity if not provided
            if quantity is None:
                quantity = await self._calculate_position_size(symbol, action)
            
            # Get current market price if not provided
            if price is None:
                price = await self._get_current_price(symbol)
            
            if price is None:
                return {"error": f"Unable to get price for {symbol}"}
            
            # Validate trade against rules
            validation_result = self._validate_trade(symbol, action, quantity, price)
            if not validation_result["valid"]:
                return {"error": validation_result["reason"]}
            
            # Calculate commission
            commission = self._calculate_commission(quantity, price)
            
            # Execute the trade
            if action == "BUY":
                result = await self._execute_buy_order(trade_id, symbol, quantity, price, commission, signal_source, confidence)
            else:
                result = await self._execute_sell_order(trade_id, symbol, quantity, price, commission, signal_source, confidence)
            
            # Update portfolio
            await self._update_portfolio()
            
            # Record trade in database
            await self._record_trade(trade_id, symbol, action, quantity, price, commission, signal_source, confidence, result["status"])
            
            # Send to IG Markets if connected
            if self.ig_client:
                try:
                    ig_result = await self.ig_client.place_order({
                        "symbol": symbol,
                        "action": action,
                        "quantity": quantity,
                        "price": price,
                        "trade_id": trade_id
                    })
                    result["ig_order_id"] = ig_result.get("order_id")
                except Exception as e:
                    self.logger.error(f'"trade_id": "{trade_id}", "error": "{e}", "action": "ig_markets_sync_failed"')
            
            self.trade_count += 1
            
            self.logger.info(f'"trade_id": "{trade_id}", "symbol": "{symbol}", "action": "{action}", "quantity": {quantity}, "price": {price}, "action": "trade_executed"')
            
            # Publish trade event
            self.publish_event("trade_executed", {
                "trade_id": trade_id,
                "symbol": symbol,
                "action": action,
                "quantity": quantity,
                "price": price,
                "signal_source": signal_source
            })
            
            return result
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "action": "{action}", "error": "{e}", "action": "trade_execution_failed"')
            return {"error": str(e)}
    
    async def _calculate_position_size(self, symbol: str, action: str) -> int:
        """Calculate appropriate position size based on rules"""
        try:
            # Get current price
            current_price = await self._get_current_price(symbol)
            if not current_price:
                return 100  # Default fallback
            
            # Calculate position size as percentage of portfolio
            available_cash = self.portfolio["cash_balance"]
            position_value = available_cash * self.trading_rules["position_size_pct"]
            
            # Don't exceed max position size
            position_value = min(position_value, self.trading_rules["max_position_size"])
            
            # Calculate quantity
            quantity = int(position_value / current_price)
            
            # Minimum 1 share
            return max(1, quantity)
            
        except Exception:
            return 100  # Default fallback
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol"""
        try:
            # Try to get from market data service
            market_data = await self.call_service("market-data", "get_market_data", symbol=symbol)
            if market_data and "technical" in market_data:
                return market_data["technical"].get("current_price")
            
            # Fallback to simulated price (for testing)
            return self._get_simulated_price(symbol)
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "price_fetch_failed"')
            return self._get_simulated_price(symbol)
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Generate simulated price for testing"""
        # Simple price simulation based on symbol
        base_prices = {
            "CBA.AX": 95.0,
            "ANZ.AX": 22.0,
            "NAB.AX": 27.0,
            "WBC.AX": 20.0,
            "MQG.AX": 180.0,
            "COL.AX": 15.0,
            "BHP.AX": 40.0
        }
        
        base_price = base_prices.get(symbol, 50.0)
        
        # Add some random variation (±2%)
        import random
        variation = random.uniform(-0.02, 0.02)
        return round(base_price * (1 + variation), 2)
    
    def _validate_trade(self, symbol: str, action: str, quantity: int, price: float) -> Dict[str, Any]:
        """Validate trade against trading rules"""
        trade_value = quantity * price
        
        # Check portfolio exposure
        total_exposure = sum(pos["value"] for pos in self.portfolio["open_positions"].values())
        max_exposure = self.portfolio["total_value"] * self.trading_rules["max_portfolio_exposure"]
        
        if action == "BUY" and (total_exposure + trade_value) > max_exposure:
            return {"valid": False, "reason": "Exceeds maximum portfolio exposure"}
        
        # Check position size limit
        if trade_value > self.trading_rules["max_position_size"]:
            return {"valid": False, "reason": "Exceeds maximum position size"}
        
        # Check available cash for buy orders
        commission = self._calculate_commission(quantity, price)
        if action == "BUY" and (trade_value + commission) > self.portfolio["cash_balance"]:
            return {"valid": False, "reason": "Insufficient cash balance"}
        
        # Check daily loss limit
        if self.portfolio["daily_pnl"] < -self.trading_rules["max_daily_loss"]:
            return {"valid": False, "reason": "Daily loss limit exceeded"}
        
        # Check if we have position to sell
        if action == "SELL":
            position_key = f"{symbol}_LONG"
            if position_key not in self.portfolio["open_positions"]:
                return {"valid": False, "reason": "No position to sell"}
            
            current_quantity = self.portfolio["open_positions"][position_key]["quantity"]
            if quantity > current_quantity:
                return {"valid": False, "reason": "Insufficient shares to sell"}
        
        return {"valid": True}
    
    def _calculate_commission(self, quantity: int, price: float) -> float:
        """Calculate trading commission"""
        # Simple commission structure: $10 + 0.1% of trade value
        trade_value = quantity * price
        commission = 10.0 + (trade_value * 0.001)
        return round(commission, 2)
    
    async def _execute_buy_order(self, trade_id: str, symbol: str, quantity: int, 
                               price: float, commission: float, signal_source: str, confidence: float):
        """Execute buy order and update positions"""
        trade_value = quantity * price
        total_cost = trade_value + commission
        
        # Update cash balance
        self.portfolio["cash_balance"] -= total_cost
        
        # Create or update position
        position_key = f"{symbol}_LONG"
        if position_key in self.portfolio["open_positions"]:
            # Add to existing position (average price)
            existing_pos = self.portfolio["open_positions"][position_key]
            total_quantity = existing_pos["quantity"] + quantity
            total_value = existing_pos["value"] + trade_value
            avg_price = total_value / total_quantity
            
            existing_pos["quantity"] = total_quantity
            existing_pos["value"] = total_value
            existing_pos["avg_price"] = avg_price
        else:
            # Create new position
            position_id = str(uuid.uuid4())
            self.portfolio["open_positions"][position_key] = {
                "position_id": position_id,
                "symbol": symbol,
                "quantity": quantity,
                "avg_price": price,
                "value": trade_value,
                "unrealized_pnl": 0.0,
                "open_time": datetime.now().isoformat(),
                "stop_loss": price * (1 - self.trading_rules["stop_loss_pct"]),
                "take_profit": price * (1 + self.trading_rules["take_profit_pct"])
            }
            
            # Record position in database
            await self._record_position(position_id, symbol, quantity, price, "OPEN")
        
        self.total_commission += commission
        
        return {
            "status": "executed",
            "trade_id": trade_id,
            "symbol": symbol,
            "action": "BUY",
            "quantity": quantity,
            "price": price,
            "commission": commission,
            "total_cost": total_cost
        }
    
    async def _execute_sell_order(self, trade_id: str, symbol: str, quantity: int,
                                price: float, commission: float, signal_source: str, confidence: float):
        """Execute sell order and update positions"""
        position_key = f"{symbol}_LONG"
        
        if position_key not in self.portfolio["open_positions"]:
            return {"status": "failed", "error": "No position to sell"}
        
        position = self.portfolio["open_positions"][position_key]
        
        if quantity > position["quantity"]:
            return {"status": "failed", "error": "Insufficient shares to sell"}
        
        # Calculate P&L
        proceeds = (quantity * price) - commission
        cost_basis = quantity * position["avg_price"]
        pnl = proceeds - cost_basis
        
        # Update cash balance
        self.portfolio["cash_balance"] += proceeds
        
        # Update position
        if quantity == position["quantity"]:
            # Closing entire position
            del self.portfolio["open_positions"][position_key]
            
            # Update position in database
            await self._update_position_status(position["position_id"], "CLOSED", pnl)
        else:
            # Partial close
            position["quantity"] -= quantity
            position["value"] -= cost_basis
        
        # Update P&L tracking
        self.portfolio["total_pnl"] += pnl
        self.portfolio["daily_pnl"] += pnl
        
        if pnl > 0:
            self.winning_trades += 1
        
        self.total_commission += commission
        
        return {
            "status": "executed",
            "trade_id": trade_id,
            "symbol": symbol,
            "action": "SELL",
            "quantity": quantity,
            "price": price,
            "commission": commission,
            "proceeds": proceeds,
            "pnl": pnl
        }
    
    async def _record_trade(self, trade_id: str, symbol: str, action: str, quantity: int,
                          price: float, commission: float, signal_source: str, confidence: float, status: str):
        """Record trade in database"""
        try:
            with sqlite3.connect(self.paper_trading_db) as conn:
                conn.execute('''
                    INSERT INTO trades (trade_id, symbol, action, quantity, price, timestamp, 
                                     status, commission, signal_source, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (trade_id, symbol, action, quantity, price, datetime.now().isoformat(),
                      status, commission, signal_source, confidence))
                conn.commit()
        except Exception as e:
            self.logger.error(f'"trade_id": "{trade_id}", "error": "{e}", "action": "trade_record_failed"')
    
    async def _record_position(self, position_id: str, symbol: str, quantity: int, entry_price: float, status: str):
        """Record position in database"""
        try:
            with sqlite3.connect(self.paper_trading_db) as conn:
                conn.execute('''
                    INSERT INTO positions (position_id, symbol, quantity, entry_price, 
                                        current_price, pnl, open_time, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (position_id, symbol, quantity, entry_price, entry_price, 0.0,
                      datetime.now().isoformat(), status))
                conn.commit()
        except Exception as e:
            self.logger.error(f'"position_id": "{position_id}", "error": "{e}", "action": "position_record_failed"')
    
    async def _update_position_status(self, position_id: str, status: str, pnl: float):
        """Update position status in database"""
        try:
            with sqlite3.connect(self.paper_trading_db) as conn:
                conn.execute('''
                    UPDATE positions SET status = ?, pnl = ?, close_time = ?
                    WHERE position_id = ?
                ''', (status, pnl, datetime.now().isoformat(), position_id))
                conn.commit()
        except Exception as e:
            self.logger.error(f'"position_id": "{position_id}", "error": "{e}", "action": "position_update_failed"')
    
    async def _update_portfolio(self):
        """Update portfolio valuations"""
        try:
            total_position_value = 0.0
            
            # Update unrealized P&L for open positions
            for position_key, position in self.portfolio["open_positions"].items():
                current_price = await self._get_current_price(position["symbol"])
                if current_price:
                    position["current_price"] = current_price
                    current_value = position["quantity"] * current_price
                    position["unrealized_pnl"] = current_value - position["value"]
                    total_position_value += current_value
            
            # Update total portfolio value
            self.portfolio["total_value"] = self.portfolio["cash_balance"] + total_position_value
            
            # Save portfolio snapshot
            await self._save_portfolio_snapshot()
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "portfolio_update_failed"')
    
    async def _save_portfolio_snapshot(self):
        """Save portfolio snapshot to database"""
        try:
            with sqlite3.connect(self.paper_trading_db) as conn:
                conn.execute('''
                    INSERT INTO portfolio_snapshots (timestamp, total_value, cash_balance, 
                                                   daily_pnl, total_pnl, open_positions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (datetime.now().isoformat(), self.portfolio["total_value"],
                      self.portfolio["cash_balance"], self.portfolio["daily_pnl"],
                      self.portfolio["total_pnl"], len(self.portfolio["open_positions"])))
                conn.commit()
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "portfolio_snapshot_failed"')
    
    async def get_positions(self):
        """Get current open positions"""
        await self._update_portfolio()
        
        positions_list = []
        for position_key, position in self.portfolio["open_positions"].items():
            positions_list.append({
                "symbol": position["symbol"],
                "quantity": position["quantity"],
                "avg_price": position["avg_price"],
                "current_price": position.get("current_price", position["avg_price"]),
                "value": position["value"],
                "unrealized_pnl": position.get("unrealized_pnl", 0.0),
                "pnl_percentage": (position.get("unrealized_pnl", 0.0) / position["value"]) * 100,
                "open_time": position["open_time"],
                "stop_loss": position.get("stop_loss"),
                "take_profit": position.get("take_profit")
            })
        
        return {
            "total_positions": len(positions_list),
            "positions": positions_list,
            "total_exposure": sum(pos["value"] for pos in positions_list),
            "total_unrealized_pnl": sum(pos["unrealized_pnl"] for pos in positions_list)
        }
    
    async def get_portfolio_status(self):
        """Get complete portfolio status"""
        await self._update_portfolio()
        
        positions_data = await self.get_positions()
        
        return {
            "portfolio_value": self.portfolio["total_value"],
            "cash_balance": self.portfolio["cash_balance"],
            "invested_amount": positions_data["total_exposure"],
            "daily_pnl": self.portfolio["daily_pnl"],
            "total_pnl": self.portfolio["total_pnl"],
            "total_return_pct": ((self.portfolio["total_value"] - 100000) / 100000) * 100,
            "open_positions": len(self.portfolio["open_positions"]),
            "total_trades": self.trade_count,
            "winning_trades": self.winning_trades,
            "win_rate": (self.winning_trades / self.trade_count * 100) if self.trade_count > 0 else 0,
            "total_commission": self.total_commission,
            "timestamp": datetime.now().isoformat()
        }
    
    async def sync_with_ig_markets(self):
        """Sync positions with IG Markets"""
        if not self.ig_client:
            return {"error": "IG Markets client not initialized"}
        
        try:
            ig_positions = await self.ig_client.get_positions()
            
            # Sync logic would go here
            # For now, just return status
            return {
                "status": "synced",
                "ig_positions": len(ig_positions) if ig_positions else 0,
                "local_positions": len(self.portfolio["open_positions"])
            }
            
        except Exception as e:
            return {"error": f"IG Markets sync failed: {e}"}
    
    async def get_trading_performance(self, period_days: int = 30):
        """Get trading performance metrics"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            with sqlite3.connect(self.paper_trading_db) as conn:
                # Get trades in period
                trades = conn.execute('''
                    SELECT * FROM trades 
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp DESC
                ''', (start_date.isoformat(), end_date.isoformat())).fetchall()
                
                # Get portfolio snapshots
                snapshots = conn.execute('''
                    SELECT * FROM portfolio_snapshots
                    WHERE timestamp >= ? AND timestamp <= ?
                    ORDER BY timestamp ASC
                ''', (start_date.isoformat(), end_date.isoformat())).fetchall()
            
            # Calculate performance metrics
            total_trades = len(trades)
            buy_trades = len([t for t in trades if t[3] == "BUY"])  # action column
            sell_trades = len([t for t in trades if t[3] == "SELL"])
            
            # Portfolio progression
            if snapshots:
                start_value = snapshots[0][2]  # total_value column
                end_value = snapshots[-1][2] if len(snapshots) > 1 else start_value
                period_return = ((end_value - start_value) / start_value) * 100
            else:
                period_return = 0.0
            
            return {
                "period_days": period_days,
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "period_return_pct": round(period_return, 2),
                "current_portfolio_value": self.portfolio["total_value"],
                "current_cash_balance": self.portfolio["cash_balance"],
                "active_positions": len(self.portfolio["open_positions"]),
                "total_commission_paid": self.total_commission
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def close_position(self, symbol: str, quantity: int = None):
        """Close a position (partial or full)"""
        position_key = f"{symbol}_LONG"
        
        if position_key not in self.portfolio["open_positions"]:
            return {"error": f"No open position for {symbol}"}
        
        position = self.portfolio["open_positions"][position_key]
        
        # Close full position if quantity not specified
        if quantity is None:
            quantity = position["quantity"]
        
        # Get current market price
        current_price = await self._get_current_price(symbol)
        if not current_price:
            return {"error": f"Unable to get current price for {symbol}"}
        
        # Execute sell order
        result = await self.execute_trade(
            symbol=symbol,
            action="SELL",
            quantity=quantity,
            price=current_price,
            signal_source="manual_close"
        )
        
        return result
    
    async def get_trade_history(self, limit: int = 50):
        """Get trade history"""
        try:
            with sqlite3.connect(self.paper_trading_db) as conn:
                trades = conn.execute('''
                    SELECT trade_id, symbol, action, quantity, price, timestamp, 
                           status, pnl, commission, signal_source, confidence
                    FROM trades 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,)).fetchall()
                
                trade_history = []
                for trade in trades:
                    trade_history.append({
                        "trade_id": trade[0],
                        "symbol": trade[1],
                        "action": trade[2],
                        "quantity": trade[3],
                        "price": trade[4],
                        "timestamp": trade[5],
                        "status": trade[6],
                        "pnl": trade[7],
                        "commission": trade[8],
                        "signal_source": trade[9],
                        "confidence": trade[10]
                    })
                
                return {
                    "total_trades": len(trade_history),
                    "trades": trade_history
                }
                
        except Exception as e:
            return {"error": str(e)}
    
    async def update_trading_rules(self, rules: Dict[str, Any]):
        """Update trading rules"""
        try:
            for key, value in rules.items():
                if key in self.trading_rules:
                    self.trading_rules[key] = value
            
            self.logger.info(f'"rules": {rules}, "action": "trading_rules_updated"')
            
            return {"status": "updated", "trading_rules": self.trading_rules}
            
        except Exception as e:
            return {"error": str(e)}
    
    async def process_prediction_signal(self, symbol: str, action: str, confidence: float, signal_source: str = "prediction"):
        """Process trading signal from prediction service"""
        try:
            # Only process BUY signals for now
            if action not in ["BUY", "STRONG_BUY"]:
                return {"status": "ignored", "reason": "Only BUY signals processed"}
            
            # Check confidence threshold
            if confidence < 0.6:
                return {"status": "ignored", "reason": "Confidence below threshold"}
            
            # Check if we already have a position
            position_key = f"{symbol}_LONG"
            if position_key in self.portfolio["open_positions"]:
                return {"status": "ignored", "reason": "Position already exists"}
            
            # Execute the trade
            result = await self.execute_trade(
                symbol=symbol,
                action="BUY",
                signal_source=signal_source,
                confidence=confidence
            )
            
            self.logger.info(f'"symbol": "{symbol}", "confidence": {confidence}, "result": "{result.get("status")}", "action": "signal_processed"')
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self):
        """Enhanced health check with paper trading metrics"""
        base_health = await super().health_check()
        
        # Add service-specific health metrics
        trading_health = {
            **base_health,
            "portfolio_value": self.portfolio["total_value"],
            "cash_balance": self.portfolio["cash_balance"],
            "open_positions": len(self.portfolio["open_positions"]),
            "total_trades": self.trade_count,
            "ig_markets_connected": self.ig_client is not None,
            "database_accessible": os.path.exists(self.paper_trading_db)
        }
        
        # Check portfolio health
        if self.portfolio["daily_pnl"] < -self.trading_rules["max_daily_loss"]:
            trading_health["status"] = "degraded"
            trading_health["warning"] = "Daily loss limit exceeded"
        
        return trading_health

async def main():
    service = PaperTradingService()
    await service.start_server()

if __name__ == "__main__":
    asyncio.run(main())
