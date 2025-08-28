#!/usr/bin/env python3
"""
Database models for Paper Trading App using SQLAlchemy
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

Base = declarative_base()

class Account(Base):
    """Account balance and portfolio summary"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True)
    account_name = Column(String(100), default="Main Account")
    cash_balance = Column(Float, nullable=False)
    initial_balance = Column(Float, nullable=False)
    portfolio_value = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    total_pnl_pct = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trades = relationship("Trade", back_populates="account")
    positions = relationship("Position", back_populates="account")
    metrics = relationship("Metrics", back_populates="account")

class Trade(Base):
    """Individual trade records"""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)  # quantity * price
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False)   # total_value + commission + slippage
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="FILLED")  # FILLED, PENDING, CANCELLED
    pnl = Column(Float, default=0.0)             # Realized P&L for this trade
    notes = Column(Text)
    strategy_source = Column(String(50))         # Which strategy generated this trade
    confidence = Column(Float)                   # Strategy confidence (0-1)
    
    # Relationships
    account = relationship("Account", back_populates="trades")

class Position(Base):
    """Current portfolio positions"""
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    symbol = Column(String(20), nullable=False, unique=True)
    quantity = Column(Integer, nullable=False)
    avg_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)   # quantity * avg_cost
    current_price = Column(Float, default=0.0)
    market_value = Column(Float, default=0.0)    # quantity * current_price
    unrealized_pnl = Column(Float, default=0.0)
    unrealized_pnl_pct = Column(Float, default=0.0)
    day_change = Column(Float, default=0.0)
    day_change_pct = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Position metadata
    entry_date = Column(DateTime, default=datetime.utcnow)
    sector = Column(String(50))
    asset_class = Column(String(20), default="EQUITY")
    
    # Relationships
    account = relationship("Account", back_populates="positions")

class Metrics(Base):
    """Daily performance metrics"""
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    
    # Daily metrics
    daily_pnl = Column(Float, default=0.0)
    daily_pnl_pct = Column(Float, default=0.0)
    daily_return = Column(Float, default=0.0)
    
    # Cumulative metrics
    cumulative_pnl = Column(Float, default=0.0)
    cumulative_return = Column(Float, default=0.0)
    portfolio_value = Column(Float, default=0.0)
    
    # Trading metrics
    trades_count = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # Risk metrics
    volatility = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    current_drawdown = Column(Float, default=0.0)
    
    # Advanced metrics
    profit_factor = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)
    
    # Relationships
    account = relationship("Account", back_populates="metrics")

class Strategy(Base):
    """Strategy configurations and performance"""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parameters = Column(Text)  # JSON string of strategy parameters
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Performance tracking
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_rate = Column(Float, default=0.0)
    avg_return = Column(Float, default=0.0)
    
    def get_parameters(self):
        """Get strategy parameters as dictionary"""
        if self.parameters:
            return json.loads(self.parameters)
        return {}
    
    def set_parameters(self, params_dict):
        """Set strategy parameters from dictionary"""
        self.parameters = json.dumps(params_dict)

class PriceData(Base):
    """Historical price data cache"""
    __tablename__ = 'price_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float)
    high_price = Column(Float)
    low_price = Column(Float)
    close_price = Column(Float)
    volume = Column(Integer)
    source = Column(String(20), default="yfinance")
    
    # Composite index for efficient querying
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )

class OrderHistory(Base):
    """Order history for tracking pending/cancelled orders"""
    __tablename__ = 'order_history'
    
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    symbol = Column(String(20), nullable=False)
    order_type = Column(String(20), nullable=False)  # MARKET, LIMIT, STOP_LOSS, TAKE_PROFIT
    side = Column(String(10), nullable=False)        # BUY, SELL
    quantity = Column(Integer, nullable=False)
    target_price = Column(Float)                     # For limit orders
    stop_price = Column(Float)                       # For stop orders
    status = Column(String(20), default="PENDING")   # PENDING, FILLED, CANCELLED, EXPIRED
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)
    filled_price = Column(Float)
    filled_quantity = Column(Integer, default=0)
    
    # Strategy info
    strategy_source = Column(String(50))
    confidence = Column(Float)
    notes = Column(Text)

# Database utility functions
def create_database(database_url="sqlite:///paper_trading.db"):
    """Create database and all tables"""
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """Get database session"""
    Session = sessionmaker(bind=engine)
    return Session()

def init_default_account(session, initial_balance=100000.0):
    """Initialize default account if none exists"""
    account = session.query(Account).first()
    if not account:
        account = Account(
            account_name="Main Account",
            cash_balance=initial_balance,
            initial_balance=initial_balance,
            portfolio_value=initial_balance,
            total_pnl=0.0,
            total_pnl_pct=0.0
        )
        session.add(account)
        session.commit()
        print(f"Created default account with ${initial_balance:,.2f}")
    return account
