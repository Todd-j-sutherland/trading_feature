#!/usr/bin/env python3
"""
Paper Trading Service with comprehensive IG Markets integration and settings.py configuration
Integrates with paper-trading-app and ig_markets_paper_trading directories

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
- Settings.py configuration integration
- Enhanced database schema compatibility

Trading Operations:
- Execute BUY/SELL signals from prediction service
- Market order simulation with real spreads
- Stop loss and take profit management
- Risk-based position sizing
- Portfolio performance tracking
"""
import asyncio
import sys
import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid
import time

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "paper-trading-app"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ig_markets_paper_trading"))

from services.base_service import BaseService

# Import settings with fallback
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config"))
    from settings import Settings
except ImportError:
    # Fallback settings class
    class Settings:
        BANK_SYMBOLS = ['CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX', 'MQG.AX']
        MARKET_DATA_CONFIG = {'market_hours': {'open': '10:00', 'close': '16:00', 'timezone': 'Australia/Sydney'}}

@dataclass
class Position:
    """Paper trading position structure"""
    position_id: str
    symbol: str
    side: str  # BUY or SELL
    quantity: int
    entry_price: float
    current_price: float
    entry_time: str
    position_value: float
    pnl: float
    pnl_percentage: float
    status: str  # OPEN, CLOSED, PARTIAL
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    ig_order_id: Optional[str] = None
    prediction_confidence: Optional[float] = None
    prediction_id: Optional[str] = None

@dataclass
class Trade:
    """Individual trade record"""
    trade_id: str
    position_id: str
    symbol: str
    action: str  # BUY, SELL
    quantity: int
    price: float
    timestamp: str
    fees: float
    trade_value: float
    order_type: str
    ig_order_id: Optional[str] = None
    execution_status: str = "FILLED"

@dataclass
class Portfolio:
    """Portfolio summary"""
    total_value: float
    cash_balance: float
    positions_value: float
    total_pnl: float
    total_pnl_percentage: float
    open_positions: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    largest_gain: float
    largest_loss: float
    average_trade: float

class PaperTradingService(BaseService):
    """Comprehensive paper trading service with IG Markets integration and settings.py configuration"""

    def __init__(self):
        super().__init__("paper-trading")
        
        # Load settings configuration
        self._load_paper_trading_settings()
        
        # Initialize data storage
        self.positions: Dict[str, Position] = {}
        self.trades: Dict[str, Trade] = {}
        self.portfolio_history: List[Dict] = []
        
        # IG Markets integration
        self.ig_client = None
        self.ig_integration_enabled = False
        
        # Performance tracking
        self.trade_count = 0
        self.total_pnl = 0.0
        self.win_count = 0
        self.loss_count = 0
        
        # Initialize databases
        self._initialize_databases()
        
        # Load existing data
        self._load_existing_positions()
        self._load_existing_trades()
        
        # Register service methods
        self._register_methods()
        
        # Initialize IG Markets if configured
        asyncio.create_task(self._initialize_ig_markets())
    
    def _load_paper_trading_settings(self):
        """Load paper trading configuration from settings with comprehensive fallbacks"""
        try:
            # Paper trading specific settings
            self.paper_trading_config = getattr(Settings, 'PAPER_TRADING_CONFIG', {
                'initial_balance': 100000.0,
                'commission_rate': 0.001,  # 0.1%
                'min_commission': 9.50,
                'max_position_size': 0.1,  # 10% of portfolio
                'stop_loss_default': 0.05,  # 5%
                'take_profit_default': 0.15,  # 15%
                'max_daily_trades': 20,
                'risk_management_enabled': True,
                'auto_execute_predictions': True,
                'min_confidence_threshold': 0.65
            })
            
            # Database configuration with comprehensive compatibility
            self.database_config = {
                'paper_trading_db': getattr(Settings, 'PAPER_TRADING_DB', 'paper_trading.db'),
                'outcomes_db': getattr(Settings, 'ENHANCED_OUTCOMES_DB', 'data/enhanced_outcomes.db'),
                'ig_markets_db': getattr(Settings, 'IG_MARKETS_DB', 'data/ig_markets_paper_trades.db'),
                'predictions_db': getattr(Settings, 'PREDICTIONS_DB', 'predictions.db'),
                'trading_predictions_db': getattr(Settings, 'TRADING_PREDICTIONS_DB', 'trading_predictions.db')
            }
            
            # Trading symbols from settings
            self.trading_symbols = getattr(Settings, 'BANK_SYMBOLS', [
                'CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX', 'MQG.AX', 'COL.AX', 'BHP.AX'
            ])
            
            # IG Markets configuration
            self.ig_config = getattr(Settings, 'IG_MARKETS_CONFIG', {
                'enabled': False,
                'api_key': '',
                'username': '',
                'password': '',
                'demo_mode': True,
                'max_order_value': 10000.0,
                'spread_adjustment': 0.001  # 0.1% spread simulation
            })
            
            # Enhanced risk management settings
            self.risk_config = {
                'max_portfolio_risk': getattr(Settings, 'MAX_PORTFOLIO_RISK', 0.02),  # 2%
                'max_position_risk': getattr(Settings, 'MAX_POSITION_RISK', 0.005),  # 0.5%
                'correlation_limit': getattr(Settings, 'CORRELATION_LIMIT', 0.7),
                'sector_concentration_limit': getattr(Settings, 'SECTOR_CONCENTRATION_LIMIT', 0.4),
                'daily_loss_limit': getattr(Settings, 'DAILY_LOSS_LIMIT', 0.05),  # 5% daily loss limit
                'position_hold_limit_days': getattr(Settings, 'POSITION_HOLD_LIMIT', 30)
            }
            
            # Market timing settings from settings
            self.market_timing = getattr(Settings, 'MARKET_DATA_CONFIG', {}).get('market_hours', {
                'open': '10:00',
                'close': '16:00',
                'timezone': 'Australia/Sydney',
                'trading_days': [0, 1, 2, 3, 4]  # Monday-Friday
            })
            
            # Performance tracking settings
            self.performance_config = {
                'benchmark_symbol': getattr(Settings, 'BENCHMARK_SYMBOL', 'XJO.AX'),  # ASX 200
                'track_sector_performance': getattr(Settings, 'TRACK_SECTOR_PERFORMANCE', True),
                'performance_update_interval': getattr(Settings, 'PERFORMANCE_UPDATE_INTERVAL', 300),  # 5 minutes
                'max_history_days': getattr(Settings, 'MAX_HISTORY_DAYS', 365)
            }
            
            self.settings_loaded = True
            self.logger.info(f'"action": "paper_trading_settings_loaded", "initial_balance": {self.paper_trading_config["initial_balance"]}, "trading_symbols": {len(self.trading_symbols)}')
            
        except Exception as e:
            self.logger.error(f'"error": "settings_load_failed", "details": "{e}", "action": "using_defaults"')
            self.settings_loaded = False
            # Use comprehensive defaults
            self.paper_trading_config = {
                'initial_balance': 100000.0,
                'commission_rate': 0.001,
                'min_commission': 9.50,
                'max_position_size': 0.1,
                'risk_management_enabled': True,
                'auto_execute_predictions': True,
                'min_confidence_threshold': 0.65
            }
            self.database_config = {
                'paper_trading_db': 'paper_trading.db',
                'outcomes_db': 'data/enhanced_outcomes.db',
                'ig_markets_db': 'data/ig_markets_paper_trades.db',
                'predictions_db': 'predictions.db',
                'trading_predictions_db': 'trading_predictions.db'
            }
            self.trading_symbols = ['CBA.AX', 'ANZ.AX', 'NAB.AX', 'WBC.AX']
            self.risk_config = {
                'max_portfolio_risk': 0.02,
                'max_position_risk': 0.005,
                'correlation_limit': 0.7,
                'sector_concentration_limit': 0.4
            }
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
from decimal import Decimal, ROUND_HALF_UP
import uuid
import re
import threading
from contextlib import contextmanager

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base.base_service import BaseService

# Add paper trading app to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "paper-trading-app"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ig_markets_paper_trading"))

class PaperTradingService(BaseService):
    """Paper trading service with enhanced IG Markets integration and comprehensive risk management"""
    
    def __init__(self):
        super().__init__("paper-trading")
        
        # Database connections with validation
        self.paper_trading_db = "paper_trading.db"
        self.ig_markets_db = "data/ig_markets_paper_trades.db"
        self._db_lock = threading.Lock()  # Thread-safe database access
        
        # Portfolio state with Decimal precision for financial calculations
        self.portfolio = {
            "cash_balance": Decimal("100000.00"),  # Starting with $100k
            "total_value": Decimal("100000.00"),
            "open_positions": {},
            "daily_pnl": Decimal("0.00"),
            "total_pnl": Decimal("0.00"),
            "initial_balance": Decimal("100000.00")
        }
        
        # Enhanced trading rules and limits with validation
        self.trading_rules = {
            "max_position_size": Decimal("10000.00"),    # Max $10k per position
            "max_portfolio_exposure": Decimal("0.8"),    # Max 80% portfolio exposure
            "max_daily_loss": Decimal("5000.00"),        # Max $5k daily loss
            "position_size_pct": Decimal("0.05"),        # 5% of portfolio per trade
            "stop_loss_pct": Decimal("0.05"),            # 5% stop loss
            "take_profit_pct": Decimal("0.10"),          # 10% take profit
            "min_trade_value": Decimal("100.00"),        # Minimum $100 trade
            "max_trades_per_day": 20,                    # Max 20 trades per day
            "cooling_off_period": 300,                   # 5 minutes between duplicate trades
            "max_position_concentration": Decimal("0.25") # Max 25% in single position
        }
        
        # IG Markets integration with security validation
        self.ig_client = None
        self.ig_credentials = self._validate_ig_credentials()
        
        # Enhanced performance tracking
        self.trade_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_commission = Decimal("0.00")
        self.daily_trade_count = 0
        self.last_trade_time = {}  # Track last trade time per symbol
        self.last_reset_date = datetime.now().date()
        
        # Risk monitoring
        self.risk_alerts = []
        self.position_monitoring = True
        self.auto_stop_loss = True
        
        # Register enhanced methods with comprehensive validation
        self.register_handler("execute_trade", self.execute_trade)
        self.register_handler("get_positions", self.get_positions)
        self.register_handler("get_portfolio_status", self.get_portfolio_status)
        self.register_handler("sync_with_ig_markets", self.sync_with_ig_markets)
        self.register_handler("get_trading_performance", self.get_trading_performance)
        self.register_handler("close_position", self.close_position)
        self.register_handler("get_trade_history", self.get_trade_history)
        self.register_handler("update_trading_rules", self.update_trading_rules)
        self.register_handler("process_prediction_signal", self.process_prediction_signal)
        self.register_handler("reset_portfolio", self.reset_portfolio)
        self.register_handler("get_risk_metrics", self.get_risk_metrics)
        self.register_handler("validate_trade_request", self.validate_trade_request)
        self.register_handler("emergency_close_all", self.emergency_close_all)
        
        # Initialize databases and components with error handling
        asyncio.create_task(self._safe_initialize_databases())
        asyncio.create_task(self._safe_initialize_ig_client())
        asyncio.create_task(self._setup_signal_subscription())
        asyncio.create_task(self._start_portfolio_monitoring())
        asyncio.create_task(self._start_daily_reset_checker())
    
    def _validate_ig_credentials(self) -> Dict[str, Any]:
        """Validate and secure IG Markets credentials"""
        credentials = {
            "api_key": os.getenv("IG_API_KEY", "").strip(),
            "username": os.getenv("IG_USERNAME", "").strip(),
            "password": os.getenv("IG_PASSWORD", "").strip(),
            "demo": True  # Always use demo for paper trading
        }
        
        # Validate credential format (basic security)
        if credentials["api_key"] and not re.match(r'^[a-zA-Z0-9_-]+$', credentials["api_key"]):
            self.logger.warning('"action": "invalid_api_key_format"')
            credentials["api_key"] = ""
        
        if credentials["username"] and not re.match(r'^[a-zA-Z0-9@._-]+$', credentials["username"]):
            self.logger.warning('"action": "invalid_username_format"')
            credentials["username"] = ""
        
        # Don't log passwords, just validate presence
        if not all([credentials["api_key"], credentials["username"], credentials["password"]]):
            self.logger.info('"action": "ig_credentials_incomplete", "mode": "local_simulation"')
        
        return credentials
    
    @contextmanager
    def _get_db_connection(self, db_path: str):
        """Thread-safe database connection context manager"""
        with self._db_lock:
            conn = sqlite3.connect(db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            try:
                yield conn
            finally:
                conn.close()
    
    async def _safe_initialize_databases(self):
        """Safely initialize databases with comprehensive error handling"""
        try:
            await self._initialize_databases()
        except Exception as e:
            self.logger.error(f'"error": "database_initialization_failed", "details": "{e}", "action": "service_degraded"')
    
    async def _safe_initialize_ig_client(self):
        """Safely initialize IG client with error handling"""
        try:
            await self._initialize_ig_client()
        except Exception as e:
            self.logger.error(f'"error": "ig_client_initialization_failed", "details": "{e}", "action": "local_mode_fallback"')
    
    async def _setup_signal_subscription(self):
        """Setup prediction signal subscription with error handling"""
        try:
            if self.redis_client:
                event_handler = self.subscribe_to_events(["prediction_generated"], self._handle_prediction_signal)
                if event_handler:
                    asyncio.create_task(event_handler())
                    self.logger.info('"action": "signal_subscription_setup"')
        except Exception as e:
            self.logger.error(f'"error": "signal_subscription_failed", "details": "{e}"')
    
    async def _start_portfolio_monitoring(self):
        """Start background portfolio monitoring and risk management"""
        while self.running:
            try:
                await self._monitor_portfolio_health()
                await self._check_stop_loss_take_profit()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                self.logger.error(f'"error": "portfolio_monitoring_error", "details": "{e}"')
                await asyncio.sleep(300)  # Retry in 5 minutes on error
    
    async def _start_daily_reset_checker(self):
        """Reset daily counters and metrics at market open"""
        while self.running:
            try:
                current_date = datetime.now().date()
                if current_date != self.last_reset_date:
                    await self._reset_daily_metrics()
                    self.last_reset_date = current_date
                
                await asyncio.sleep(3600)  # Check every hour
            except Exception as e:
                self.logger.error(f'"error": "daily_reset_checker_error", "details": "{e}"')
                await asyncio.sleep(3600)
    
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
        """Execute a paper trade with comprehensive validation and risk management"""
        try:
            # Input validation
            if not isinstance(symbol, str) or not symbol.strip():
                return {"error": "Symbol must be a non-empty string"}
            
            symbol = symbol.upper().strip()
            if not re.match(r'^[A-Z]{2,5}\.AX$', symbol):
                return {"error": "Invalid ASX symbol format (expected: XXX.AX)"}
            
            if action not in ["BUY", "SELL"]:
                return {"error": "Invalid action. Must be BUY or SELL"}
            
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                return {"error": "Confidence must be a number between 0 and 1"}
            
            # Check daily trade limit
            if self.daily_trade_count >= self.trading_rules["max_trades_per_day"]:
                return {"error": "Daily trade limit exceeded"}
            
            # Check cooling off period
            last_trade_time = self.last_trade_time.get(symbol, 0)
            if (datetime.now().timestamp() - last_trade_time) < self.trading_rules["cooling_off_period"]:
                return {"error": f"Cooling off period active for {symbol}"}
            
            # Generate trade ID
            trade_id = str(uuid.uuid4())
            
            # Calculate quantity if not provided
            if quantity is None:
                quantity = await self._calculate_position_size(symbol, action)
                if quantity == 0:
                    return {"error": "Calculated position size is zero"}
            
            # Validate quantity
            if not isinstance(quantity, int) or quantity <= 0:
                return {"error": "Quantity must be a positive integer"}
            
            if quantity > 10000:  # Reasonable upper limit
                return {"error": "Quantity exceeds maximum limit (10,000 shares)"}
            
            # Get current market price if not provided
            if price is None:
                price_result = await self._get_current_price(symbol)
                if price_result is None:
                    return {"error": f"Unable to get price for {symbol}"}
                price = price_result
            
            # Validate price
            if not isinstance(price, (int, float)) or price <= 0:
                return {"error": "Price must be a positive number"}
            
            price = Decimal(str(price)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
            # Validate trade against rules
            validation_result = await self._validate_trade(symbol, action, quantity, price)
            if not validation_result["valid"]:
                return {"error": validation_result["reason"]}
            
            # Calculate commission with precision
            commission = self._calculate_commission(quantity, price)
            
            # Execute the trade
            if action == "BUY":
                result = await self._execute_buy_order(trade_id, symbol, quantity, price, commission, signal_source, confidence)
            else:
                result = await self._execute_sell_order(trade_id, symbol, quantity, price, commission, signal_source, confidence)
            
            if result["status"] == "executed":
                # Update tracking
                self.daily_trade_count += 1
                self.trade_count += 1
                self.last_trade_time[symbol] = datetime.now().timestamp()
                
                # Update portfolio
                await self._update_portfolio()
                
                # Record trade in database
                await self._record_trade(trade_id, symbol, action, quantity, price, commission, signal_source, confidence, result["status"])
                
                # Send to IG Markets if connected
                if self.ig_client:
                    try:
                        ig_result = await asyncio.wait_for(
                            self.ig_client.place_order({
                                "symbol": symbol,
                                "action": action,
                                "quantity": quantity,
                                "price": float(price),
                                "trade_id": trade_id
                            }),
                            timeout=10.0
                        )
                        result["ig_order_id"] = ig_result.get("order_id")
                    except asyncio.TimeoutError:
                        self.logger.warning(f'"trade_id": "{trade_id}", "error": "ig_markets_timeout", "action": "ig_sync_skipped"')
                    except Exception as e:
                        self.logger.error(f'"trade_id": "{trade_id}", "error": "{e}", "action": "ig_markets_sync_failed"')
                
                self.logger.info(f'"trade_id": "{trade_id}", "symbol": "{symbol}", "action": "{action}", "quantity": {quantity}, "price": {price}, "action": "trade_executed"')
                
                # Publish trade event
                self.publish_event("trade_executed", {
                    "trade_id": trade_id,
                    "symbol": symbol,
                    "action": action,
                    "quantity": quantity,
                    "price": float(price),
                    "signal_source": signal_source,
                    "confidence": confidence
                }, priority="high")
                
                # Check for risk alerts after trade
                await self._check_risk_thresholds()
            
            return result
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "action": "{action}", "error": "{e}", "action": "trade_execution_failed"')
            return {"error": f"Trade execution failed: {str(e)}"}
    
    async def _calculate_position_size(self, symbol: str, action: str) -> int:
        """Calculate appropriate position size based on rules with enhanced validation"""
        try:
            # Get current price with validation
            current_price = await self._get_current_price(symbol)
            if not current_price or current_price <= 0:
                return 0  # Can't calculate without valid price
            
            current_price = Decimal(str(current_price))
            
            # Calculate position size as percentage of portfolio
            available_cash = self.portfolio["cash_balance"]
            portfolio_value = self.portfolio["total_value"]
            
            # Use smaller of available cash or portfolio percentage
            position_value = min(
                available_cash * self.trading_rules["position_size_pct"],
                portfolio_value * self.trading_rules["position_size_pct"]
            )
            
            # Don't exceed max position size
            position_value = min(position_value, self.trading_rules["max_position_size"])
            
            # Don't exceed minimum trade value threshold
            if position_value < self.trading_rules["min_trade_value"]:
                return 0
            
            # Calculate quantity with commission consideration
            estimated_commission = Decimal("20.00")  # Conservative estimate
            available_for_shares = position_value - estimated_commission
            
            if available_for_shares <= 0:
                return 0
            
            quantity = int(available_for_shares / current_price)
            
            # Check position concentration limits
            if action == "BUY":
                position_key = f"{symbol}_LONG"
                if position_key in self.portfolio["open_positions"]:
                    # Adding to existing position
                    existing_value = self.portfolio["open_positions"][position_key]["value"]
                    new_total_value = existing_value + (quantity * current_price)
                    
                    concentration = new_total_value / self.portfolio["total_value"]
                    if concentration > self.trading_rules["max_position_concentration"]:
                        # Reduce quantity to stay within concentration limit
                        max_additional_value = (self.trading_rules["max_position_concentration"] * self.portfolio["total_value"]) - existing_value
                        if max_additional_value > 0:
                            quantity = int(max_additional_value / current_price)
                        else:
                            quantity = 0
            
            # Minimum 1 share, maximum reasonable limit
            return max(0, min(quantity, 10000))
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "position_size_calculation_failed"')
            return 0  # Conservative fallback
    
    async def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for symbol with enhanced error handling"""
        try:
            # Try to get from market data service with timeout
            market_data = await asyncio.wait_for(
                self.call_service("market-data", "get_market_data", symbol=symbol),
                timeout=5.0
            )
            
            if market_data and isinstance(market_data, dict) and "technical" in market_data:
                price = market_data["technical"].get("current_price")
                if isinstance(price, (int, float)) and price > 0:
                    return float(price)
            
        except asyncio.TimeoutError:
            self.logger.warning(f'"symbol": "{symbol}", "error": "market_data_timeout", "action": "using_simulated_price"')
        except Exception as e:
            self.logger.warning(f'"symbol": "{symbol}", "error": "{e}", "action": "market_data_failed_using_simulation"')
        
        # Fallback to simulated price
        return self._get_simulated_price(symbol)
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Generate simulated price for testing with realistic variation"""
        # Base prices with more realistic ASX values
        base_prices = {
            "CBA.AX": 105.50,
            "ANZ.AX": 25.20,
            "NAB.AX": 30.15,
            "WBC.AX": 22.80,
            "MQG.AX": 185.40,
            "COL.AX": 16.75,
            "BHP.AX": 45.30,
            "CSL.AX": 280.50,
            "TLS.AX": 3.85,
            "WOW.AX": 38.20
        }
        
        base_price = base_prices.get(symbol, 50.0)
        
        # Add time-based and random variation (±3%)
        import random
        import math
        
        # Time-based component for intraday movement
        hour = datetime.now().hour
        minute = datetime.now().minute
        time_factor = math.sin((hour * 60 + minute) / (24 * 60) * 2 * math.pi) * 0.01
        
        # Random component
        random_factor = random.uniform(-0.02, 0.02)
        
        total_variation = time_factor + random_factor
        final_price = base_price * (1 + total_variation)
        
        return round(final_price, 2)
    
    async def _validate_trade(self, symbol: str, action: str, quantity: int, price: Decimal) -> Dict[str, Any]:
        """Validate trade against trading rules with comprehensive checks"""
        try:
            trade_value = Decimal(str(quantity)) * price
            
            # Basic validation
            if trade_value < self.trading_rules["min_trade_value"]:
                return {"valid": False, "reason": f"Trade value below minimum (${self.trading_rules['min_trade_value']})"}
            
            # Check portfolio exposure
            total_exposure = Decimal("0")
            for pos in self.portfolio["open_positions"].values():
                total_exposure += pos["value"]
            
            max_exposure = self.portfolio["total_value"] * self.trading_rules["max_portfolio_exposure"]
            
            if action == "BUY" and (total_exposure + trade_value) > max_exposure:
                return {"valid": False, "reason": f"Exceeds maximum portfolio exposure ({float(self.trading_rules['max_portfolio_exposure']) * 100}%)"}
            
            # Check position size limit
            if trade_value > self.trading_rules["max_position_size"]:
                return {"valid": False, "reason": f"Exceeds maximum position size (${self.trading_rules['max_position_size']})"}
            
            # Check available cash for buy orders
            commission = self._calculate_commission(quantity, price)
            total_cost = trade_value + commission
            
            if action == "BUY" and total_cost > self.portfolio["cash_balance"]:
                return {"valid": False, "reason": f"Insufficient cash balance (need ${total_cost}, have ${self.portfolio['cash_balance']})"}
            
            # Check daily loss limit
            if self.portfolio["daily_pnl"] < -self.trading_rules["max_daily_loss"]:
                return {"valid": False, "reason": f"Daily loss limit exceeded (${self.trading_rules['max_daily_loss']})"}
            
            # Check position concentration for BUY orders
            if action == "BUY":
                position_key = f"{symbol}_LONG"
                if position_key in self.portfolio["open_positions"]:
                    existing_value = self.portfolio["open_positions"][position_key]["value"]
                    total_position_value = existing_value + trade_value
                    concentration = total_position_value / self.portfolio["total_value"]
                    
                    if concentration > self.trading_rules["max_position_concentration"]:
                        return {"valid": False, "reason": f"Exceeds position concentration limit ({float(self.trading_rules['max_position_concentration']) * 100}%)"}
            
            # Check if we have position to sell
            if action == "SELL":
                position_key = f"{symbol}_LONG"
                if position_key not in self.portfolio["open_positions"]:
                    return {"valid": False, "reason": "No position to sell"}
                
                current_quantity = self.portfolio["open_positions"][position_key]["quantity"]
                if quantity > current_quantity:
                    return {"valid": False, "reason": f"Insufficient shares to sell (want {quantity}, have {current_quantity})"}
            
            return {"valid": True}
            
        except Exception as e:
            self.logger.error(f'"symbol": "{symbol}", "error": "{e}", "action": "trade_validation_error"')
            return {"valid": False, "reason": f"Validation error: {str(e)}"}
    
    def _calculate_commission(self, quantity: int, price: Decimal) -> Decimal:
        """Calculate trading commission with accurate structure"""
        try:
            trade_value = Decimal(str(quantity)) * price
            
            # Australian broker commission structure
            # Base commission + percentage of trade value
            base_commission = Decimal("19.95")  # Typical Australian broker base fee
            percentage_fee = trade_value * Decimal("0.001")  # 0.1% of trade value
            
            # Minimum and maximum commission limits
            min_commission = Decimal("19.95")
            max_commission = Decimal("100.00")
            
            total_commission = base_commission + percentage_fee
            total_commission = max(min_commission, min(total_commission, max_commission))
            
            return total_commission.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            
        except Exception as e:
            self.logger.error(f'"quantity": {quantity}, "price": {price}, "error": "{e}", "action": "commission_calculation_error"')
            return Decimal("20.00")  # Conservative fallback
    
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
        """Update portfolio valuations with comprehensive accuracy"""
        try:
            total_position_value = Decimal("0.0")
            total_unrealized_pnl = Decimal("0.0")
            
            with self.db_lock:
                # Update unrealized P&L for open positions
                for position_key, position in self.portfolio["open_positions"].items():
                    current_price = await self._get_current_price(position["symbol"])
                    if current_price:
                        current_price = Decimal(str(current_price))
                        avg_price = Decimal(str(position["avg_price"]))
                        quantity = Decimal(str(position["quantity"]))
                        
                        # Calculate current values with precision
                        current_value = quantity * current_price
                        cost_basis = quantity * avg_price
                        unrealized_pnl = current_value - cost_basis
                        
                        # Update position data
                        position["current_price"] = float(current_price)
                        position["value"] = float(current_value)
                        position["unrealized_pnl"] = float(unrealized_pnl)
                        position["updated_at"] = datetime.now().isoformat()
                        
                        total_position_value += current_value
                        total_unrealized_pnl += unrealized_pnl
                
                # Update portfolio totals
                self.portfolio["total_position_value"] = float(total_position_value)
                self.portfolio["unrealized_pnl"] = float(total_unrealized_pnl)
                self.portfolio["total_value"] = float(self.portfolio["cash_balance"] + total_position_value)
                
                # Save portfolio snapshot
                await self._save_portfolio_snapshot()
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "portfolio_update_failed"')
    
    async def _save_portfolio_snapshot(self):
        """Save comprehensive portfolio snapshot to database"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                # Store comprehensive portfolio state
                cursor.execute('''
                    INSERT OR REPLACE INTO portfolio_snapshots (
                        timestamp, date, total_value, cash_balance, total_position_value,
                        realized_pnl, unrealized_pnl, daily_pnl, total_commission,
                        total_trades, winning_trades, open_positions, 
                        portfolio_data, risk_metrics
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    datetime.now().date().isoformat(),
                    self.portfolio["total_value"],
                    self.portfolio["cash_balance"],
                    self.portfolio.get("total_position_value", 0),
                    self.portfolio.get("realized_pnl", 0),
                    self.portfolio.get("unrealized_pnl", 0),
                    self.portfolio.get("daily_pnl", 0),
                    self.portfolio.get("total_commission", 0),
                    self.portfolio.get("total_trades", 0),
                    self.portfolio.get("winning_trades", 0),
                    len(self.portfolio["open_positions"]),
                    json.dumps(self.portfolio),
                    json.dumps(self._calculate_risk_metrics())
                ))
                
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "portfolio_snapshot_failed"')
    
    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        try:
            metrics = {
                "portfolio_beta": 1.0,  # Simplified - would need market data for calculation
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "win_rate": 0.0,
                "position_concentration": 0.0,
                "leverage": 0.0
            }
            
            # Calculate win rate
            total_trades = self.portfolio.get("total_trades", 0)
            winning_trades = self.portfolio.get("winning_trades", 0)
            if total_trades > 0:
                metrics["win_rate"] = winning_trades / total_trades * 100
            
            # Calculate position concentration (largest position as % of portfolio)
            if self.portfolio["open_positions"]:
                total_value = self.portfolio["total_value"]
                if total_value > 0:
                    max_position_value = max(
                        pos.get("value", 0) for pos in self.portfolio["open_positions"].values()
                    )
                    metrics["position_concentration"] = (max_position_value / total_value) * 100
            
            # Calculate leverage (total position value / portfolio value)
            total_position_value = self.portfolio.get("total_position_value", 0)
            if self.portfolio["total_value"] > 0:
                metrics["leverage"] = total_position_value / self.portfolio["total_value"]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'"error": "{e}", "action": "risk_calculation_failed"')
            return {}
    
    async def _update_position_status(self, position_id: str, status: str, pnl: float):
        """Update position status in database with comprehensive tracking"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute('''
                    UPDATE positions SET 
                        status = ?, 
                        pnl = ?, 
                        close_time = ?,
                        updated_at = ?
                    WHERE position_id = ?
                ''', (
                    status, 
                    pnl, 
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                    position_id
                ))
                
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f'"position_id": "{position_id}", "error": "{e}", "action": "position_update_failed"')
    
    async def _record_position(self, position_id: str, symbol: str, quantity: int, entry_price: float, status: str):
        """Record position in database with comprehensive data"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute('''
                    INSERT INTO positions (
                        position_id, symbol, quantity, entry_price, current_price, 
                        pnl, open_time, status, stop_loss, take_profit,
                        risk_amount, position_size_pct, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position_id, symbol, quantity, entry_price, entry_price, 0.0,
                    datetime.now().isoformat(), status,
                    entry_price * (1 - self.trading_rules["stop_loss_pct"]),
                    entry_price * (1 + self.trading_rules["take_profit_pct"]),
                    quantity * entry_price * self.trading_rules["stop_loss_pct"],  # Risk amount
                    (quantity * entry_price) / self.portfolio["total_value"] * 100,  # Position size %
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f'"position_id": "{position_id}", "error": "{e}", "action": "position_record_failed"')
    
    async def _record_trade(self, trade_id: str, symbol: str, action: str, quantity: int,
                          price: float, commission: float, signal_source: str, confidence: float, status: str):
        """Record trade in database with comprehensive details"""
        try:
            with self.db_lock:
                cursor = self.db_connection.cursor()
                
                cursor.execute('''
                    INSERT INTO trades (
                        trade_id, symbol, action, quantity, price, timestamp, 
                        status, commission, signal_source, confidence,
                        trade_value, portfolio_value_before, portfolio_value_after,
                        execution_time, notes, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade_id, symbol, action, quantity, price, 
                    datetime.now().isoformat(), status, commission, 
                    signal_source, confidence,
                    quantity * price,  # trade_value
                    self.portfolio["total_value"],  # portfolio_value_before
                    0,  # portfolio_value_after (will be updated)
                    0.1,  # execution_time (simulated)
                    f"Confidence: {confidence:.2f}, Source: {signal_source}",  # notes
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                self.db_connection.commit()
                
        except Exception as e:
            self.logger.error(f'"trade_id": "{trade_id}", "error": "{e}", "action": "trade_record_failed"')
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
