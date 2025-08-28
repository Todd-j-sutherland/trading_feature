#!/usr/bin/env python3
"""
Paper Trading Engine for simulating trade execution
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import time

from database.models import *
from config import TRADING_CONFIG, RISK_CONFIG, MARKET_CONFIG

@dataclass
class TradeResult:
    """Result of a trade execution attempt"""
    success: bool
    message: str
    trade_id: Optional[int] = None
    executed_price: Optional[float] = None
    executed_quantity: Optional[int] = None
    commission: Optional[float] = None
    slippage: Optional[float] = None

class PaperTradingEngine:
    """Core paper trading engine for order execution and portfolio management"""
    
    def __init__(self, session, account_id: int = 1):
        self.session = session
        self.account_id = account_id
        self.logger = logging.getLogger(__name__)
        
        # Cache for price data
        self.price_cache = {}
        self.cache_expiry = {}
        
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price with caching"""
        try:
            # Check cache first (5-minute expiry)
            now = datetime.now()
            if (symbol in self.price_cache and 
                symbol in self.cache_expiry and 
                now < self.cache_expiry[symbol]):
                return self.price_cache[symbol]
            
            # Fetch fresh data
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Try different price sources
            price = None
            if 'currentPrice' in info:
                price = info['currentPrice']
            elif 'regularMarketPrice' in info:
                price = info['regularMarketPrice']
            elif 'previousClose' in info:
                price = info['previousClose']
                self.logger.warning(f"Using previous close for {symbol}")
            
            if price and price > 0:
                # Cache the price
                self.price_cache[symbol] = price
                self.cache_expiry[symbol] = now + timedelta(minutes=5)
                return price
            
            # Fallback to recent data
            hist = ticker.history(period="1d", interval="1m")
            if not hist.empty:
                price = hist['Close'].iloc[-1]
                self.price_cache[symbol] = price
                self.cache_expiry[symbol] = now + timedelta(minutes=5)
                return price
                
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {e}")
        
        return None
    
    def calculate_commission(self, total_value: float) -> float:
        """Calculate commission based on trade value"""
        commission_rate = TRADING_CONFIG.get('commission_rate', 0.0025)
        min_commission = TRADING_CONFIG.get('min_commission', 5.0)
        max_commission = TRADING_CONFIG.get('max_commission', 25.0)
        
        commission = total_value * commission_rate
        return max(min_commission, min(commission, max_commission))
    
    def calculate_slippage(self, symbol: str, quantity: int, side: str) -> float:
        """Simulate market slippage"""
        # Higher slippage for larger trades and during market hours
        base_slippage = TRADING_CONFIG.get('slippage_rate', 0.001)
        
        # Increase slippage for large trades
        if quantity > 10000:
            base_slippage *= 2
        elif quantity > 5000:
            base_slippage *= 1.5
        
        # Simulate random slippage (normally would be based on order book)
        import random
        slippage_factor = random.uniform(0.5, 1.5)
        return base_slippage * slippage_factor
    
    def check_market_hours(self) -> bool:
        """Check if market is open (simplified)"""
        now = datetime.now()
        weekday = now.weekday()
        
        # Weekend check
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Simple time check (would need proper timezone handling in production)
        current_time = now.time()
        market_open = datetime.strptime("09:30", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        
        return market_open <= current_time <= market_close
    
    def validate_trade(self, symbol: str, side: str, quantity: int, price: Optional[float] = None) -> Tuple[bool, str]:
        """Validate trade parameters and risk limits"""
        # Get account
        account = self.session.query(Account).filter_by(id=self.account_id).first()
        if not account:
            return False, "Account not found"
        
        # Get current price if not provided
        if price is None:
            price = self.get_current_price(symbol)
            if price is None:
                return False, f"Could not get current price for {symbol}"
        
        # Calculate trade value
        trade_value = quantity * price
        commission = self.calculate_commission(trade_value)
        total_cost = trade_value + commission
        
        if side.upper() == "BUY":
            # Check cash availability
            if total_cost > account.cash_balance:
                return False, f"Insufficient cash. Need ${total_cost:,.2f}, have ${account.cash_balance:,.2f}"
            
            # Check position size limits
            max_position_value = account.portfolio_value * RISK_CONFIG.get('max_position_size', 0.2)
            if trade_value > max_position_value:
                return False, f"Position too large. Max ${max_position_value:,.2f}, requested ${trade_value:,.2f}"
        
        elif side.upper() == "SELL":
            # Check position availability
            position = self.session.query(Position).filter_by(
                account_id=self.account_id, symbol=symbol
            ).first()
            
            if not position or position.quantity < quantity:
                available = position.quantity if position else 0
                return False, f"Insufficient shares. Need {quantity}, have {available}"
        
        # Check daily loss limits
        today = datetime.now().date()
        today_metrics = self.session.query(Metrics).filter_by(
            account_id=self.account_id
        ).filter(Metrics.date >= today).first()
        
        if today_metrics:
            daily_loss_limit = account.portfolio_value * RISK_CONFIG.get('daily_loss_limit', 0.05)
            if today_metrics.daily_pnl < -daily_loss_limit:
                return False, f"Daily loss limit exceeded. Lost ${abs(today_metrics.daily_pnl):,.2f}"
        
        return True, "Trade validated"
    
    def execute_market_buy(self, symbol: str, quantity: int, strategy_source: str = None, 
                          confidence: float = None, notes: str = None) -> TradeResult:
        """Execute a market buy order"""
        try:
            # Validate trade
            valid, message = self.validate_trade(symbol, "BUY", quantity)
            if not valid:
                return TradeResult(success=False, message=message)
            
            # Get current price
            price = self.get_current_price(symbol)
            if price is None:
                return TradeResult(success=False, message=f"Could not get price for {symbol}")
            
            # Calculate costs
            trade_value = quantity * price
            commission = self.calculate_commission(trade_value)
            slippage_rate = self.calculate_slippage(symbol, quantity, "BUY")
            slippage = trade_value * slippage_rate
            
            # Adjust price for slippage (buy at higher price)
            executed_price = price * (1 + slippage_rate)
            net_amount = quantity * executed_price + commission
            
            # Create trade record
            trade = Trade(
                account_id=self.account_id,
                symbol=symbol,
                side="BUY",
                quantity=quantity,
                price=executed_price,
                total_value=quantity * executed_price,
                commission=commission,
                slippage=slippage,
                net_amount=net_amount,
                timestamp=datetime.utcnow(),
                status="FILLED",
                strategy_source=strategy_source,
                confidence=confidence,
                notes=notes
            )
            
            self.session.add(trade)
            
            # Update account cash
            account = self.session.query(Account).filter_by(id=self.account_id).first()
            account.cash_balance -= net_amount
            
            # Update or create position
            position = self.session.query(Position).filter_by(
                account_id=self.account_id, symbol=symbol
            ).first()
            
            if position:
                # Update existing position
                total_shares = position.quantity + quantity
                total_cost = position.total_cost + net_amount
                position.quantity = total_shares
                position.avg_cost = total_cost / total_shares
                position.total_cost = total_cost
            else:
                # Create new position
                position = Position(
                    account_id=self.account_id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=executed_price,
                    total_cost=net_amount,
                    entry_date=datetime.utcnow()
                )
                self.session.add(position)
            
            self.session.commit()
            
            return TradeResult(
                success=True,
                message=f"Bought {quantity} shares of {symbol} at ${executed_price:.2f}",
                trade_id=trade.id,
                executed_price=executed_price,
                executed_quantity=quantity,
                commission=commission,
                slippage=slippage
            )
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error executing buy order: {e}")
            return TradeResult(success=False, message=f"Execution error: {str(e)}")
    
    def execute_market_sell(self, symbol: str, quantity: int, strategy_source: str = None,
                           confidence: float = None, notes: str = None) -> TradeResult:
        """Execute a market sell order"""
        try:
            # Validate trade
            valid, message = self.validate_trade(symbol, "SELL", quantity)
            if not valid:
                return TradeResult(success=False, message=message)
            
            # Get current price
            price = self.get_current_price(symbol)
            if price is None:
                return TradeResult(success=False, message=f"Could not get price for {symbol}")
            
            # Get position
            position = self.session.query(Position).filter_by(
                account_id=self.account_id, symbol=symbol
            ).first()
            
            if not position or position.quantity < quantity:
                return TradeResult(success=False, message="Insufficient position")
            
            # Calculate proceeds
            trade_value = quantity * price
            commission = self.calculate_commission(trade_value)
            slippage_rate = self.calculate_slippage(symbol, quantity, "SELL")
            slippage = trade_value * slippage_rate
            
            # Adjust price for slippage (sell at lower price)
            executed_price = price * (1 - slippage_rate)
            net_proceeds = quantity * executed_price - commission
            
            # Calculate P&L
            avg_cost_for_shares = position.avg_cost * quantity
            realized_pnl = net_proceeds - avg_cost_for_shares
            
            # Create trade record
            trade = Trade(
                account_id=self.account_id,
                symbol=symbol,
                side="SELL",
                quantity=quantity,
                price=executed_price,
                total_value=quantity * executed_price,
                commission=commission,
                slippage=slippage,
                net_amount=net_proceeds,
                timestamp=datetime.utcnow(),
                status="FILLED",
                pnl=realized_pnl,
                strategy_source=strategy_source,
                confidence=confidence,
                notes=notes
            )
            
            self.session.add(trade)
            
            # Update account cash
            account = self.session.query(Account).filter_by(id=self.account_id).first()
            account.cash_balance += net_proceeds
            account.total_pnl += realized_pnl
            
            # Update position
            position.quantity -= quantity
            position.total_cost -= avg_cost_for_shares
            
            # Remove position if fully sold
            if position.quantity == 0:
                self.session.delete(position)
            
            self.session.commit()
            
            return TradeResult(
                success=True,
                message=f"Sold {quantity} shares of {symbol} at ${executed_price:.2f} (P&L: ${realized_pnl:+.2f})",
                trade_id=trade.id,
                executed_price=executed_price,
                executed_quantity=quantity,
                commission=commission,
                slippage=slippage
            )
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error executing sell order: {e}")
            return TradeResult(success=False, message=f"Execution error: {str(e)}")
    
    def update_portfolio_values(self):
        """Update current market values for all positions"""
        try:
            positions = self.session.query(Position).filter_by(account_id=self.account_id).all()
            
            for position in positions:
                current_price = self.get_current_price(position.symbol)
                if current_price:
                    position.current_price = current_price
                    position.market_value = position.quantity * current_price
                    position.unrealized_pnl = position.market_value - position.total_cost
                    position.unrealized_pnl_pct = (position.unrealized_pnl / position.total_cost) * 100
                    position.last_updated = datetime.utcnow()
            
            # Update account portfolio value
            account = self.session.query(Account).filter_by(id=self.account_id).first()
            total_market_value = sum(pos.market_value for pos in positions)
            account.portfolio_value = account.cash_balance + total_market_value
            account.total_pnl_pct = ((account.portfolio_value - account.initial_balance) / account.initial_balance) * 100
            
            self.session.commit()
            
        except Exception as e:
            self.logger.error(f"Error updating portfolio values: {e}")
            self.session.rollback()
    
    def get_portfolio_summary(self) -> Dict:
        """Get current portfolio summary"""
        try:
            self.update_portfolio_values()
            
            account = self.session.query(Account).filter_by(id=self.account_id).first()
            positions = self.session.query(Position).filter_by(account_id=self.account_id).all()
            
            position_data = []
            for pos in positions:
                position_data.append({
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_cost': pos.avg_cost,
                    'current_price': pos.current_price,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'unrealized_pnl_pct': pos.unrealized_pnl_pct,
                    'day_change': pos.day_change,
                    'day_change_pct': pos.day_change_pct
                })
            
            return {
                'account': {
                    'cash_balance': account.cash_balance,
                    'portfolio_value': account.portfolio_value,
                    'total_pnl': account.total_pnl,
                    'total_pnl_pct': account.total_pnl_pct,
                    'initial_balance': account.initial_balance
                },
                'positions': position_data,
                'summary': {
                    'total_positions': len(positions),
                    'total_market_value': sum(pos.market_value for pos in positions),
                    'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in positions)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio summary: {e}")
            return {}

class StrategyInterface:
    """Interface for connecting trading strategies"""
    
    def __init__(self, engine: PaperTradingEngine):
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    def execute_strategy_signal(self, signal: Dict) -> TradeResult:
        """Execute a trading signal from a strategy
        
        Expected signal format:
        {
            'symbol': 'AAPL',
            'action': 'BUY' or 'SELL',
            'quantity': 100,
            'strategy': 'ML_Strategy_v1',
            'confidence': 0.85,
            'reasoning': 'Strong buy signal from ML model'
        }
        """
        try:
            symbol = signal.get('symbol')
            action = signal.get('action', '').upper()
            quantity = signal.get('quantity', 0)
            strategy = signal.get('strategy')
            confidence = signal.get('confidence')
            reasoning = signal.get('reasoning')
            
            if action == 'BUY':
                return self.engine.execute_market_buy(
                    symbol=symbol,
                    quantity=quantity,
                    strategy_source=strategy,
                    confidence=confidence,
                    notes=reasoning
                )
            elif action == 'SELL':
                return self.engine.execute_market_sell(
                    symbol=symbol,
                    quantity=quantity,
                    strategy_source=strategy,
                    confidence=confidence,
                    notes=reasoning
                )
            else:
                return TradeResult(success=False, message=f"Invalid action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error executing strategy signal: {e}")
            return TradeResult(success=False, message=f"Strategy execution error: {str(e)}")
    
    def get_strategy_performance(self, strategy_name: str) -> Dict:
        """Get performance metrics for a specific strategy"""
        try:
            trades = self.engine.session.query(Trade).filter_by(
                account_id=self.engine.account_id,
                strategy_source=strategy_name
            ).all()
            
            if not trades:
                return {'error': 'No trades found for strategy'}
            
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.pnl > 0])
            total_pnl = sum(t.pnl for t in trades if t.pnl is not None)
            
            return {
                'strategy_name': strategy_name,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'win_rate': (winning_trades / total_trades) * 100 if total_trades > 0 else 0,
                'total_pnl': total_pnl,
                'avg_pnl': total_pnl / total_trades if total_trades > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting strategy performance: {e}")
            return {'error': str(e)}
