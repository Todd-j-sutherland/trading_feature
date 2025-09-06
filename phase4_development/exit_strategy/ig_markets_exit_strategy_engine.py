#!/usr/bin/env python3
"""
Exit Strategy Engine - Phase 4 Development (IG Markets Integration)

This module provides the missing piece that answers the fundamental question:
"How does it know when to exit the prediction?"

The engine evaluates multiple exit conditions using your existing IG Markets data source.
Includes safety flags to enable/disable exit strategy functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import sqlite3
import pandas as pd
from pathlib import Path
import sys
import os

# Add project paths for IG Markets integration
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Try to import your existing IG Markets price source (primary)
try:
    from paper_trading_app.enhanced_ig_markets_integration import EnhancedPaperTradingPriceSource
    from app.core.data.collectors.enhanced_market_data_collector import EnhancedMarketDataCollector
    IG_MARKETS_AVAILABLE = True
except ImportError:
    try:
        # Try alternative import paths
        from enhanced_ig_markets_integration import EnhancedPaperTradingPriceSource
        IG_MARKETS_AVAILABLE = True
    except ImportError:
        IG_MARKETS_AVAILABLE = False

# Try to import TA-Lib for technical analysis (optional)
try:
    import talib as ta
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

# Fallback to yfinance if IG Markets unavailable
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

# Configure logger without overriding global logging configuration
logger = logging.getLogger(__name__)
# Set a default level but don't override if parent logger is configured
if logger.level == logging.NOTSET:
    logger.setLevel(logging.INFO)

class ExitReason(Enum):
    """Exit reason enumeration"""
    TIME_LIMIT = "TIME_LIMIT"
    PROFIT_TARGET = "PROFIT_TARGET" 
    STOP_LOSS = "STOP_LOSS"
    SENTIMENT_REVERSAL = "SENTIMENT_REVERSAL"
    TECHNICAL_BREAKDOWN = "TECHNICAL_BREAKDOWN"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    MANUAL = "MANUAL"
    NO_EXIT = "NO_EXIT"

@dataclass
class Position:
    """Position data structure"""
    symbol: str
    entry_price: float
    current_price: float
    entry_time: datetime
    confidence: float
    position_type: str  # 'BUY' or 'SELL' or 'HOLD'
    shares: int = 100
    market_context: str = 'NEUTRAL'  # 'BULLISH', 'NEUTRAL', 'BEARISH'
    original_prediction_id: str = None

@dataclass
class ExitSignal:
    """Exit signal data structure"""
    should_exit: bool
    reason: ExitReason
    urgency: int  # 1-5 scale (5 = immediate exit)
    confidence: float  # 0-1 scale
    recommended_exit_price: float = None
    details: str = ""

class IGMarketsExitDataProvider:
    """Data provider using your existing IG Markets integration"""
    
    def __init__(self):
        """Initialize with your existing IG Markets system"""
        self.price_source = None
        self.data_collector = None
        
        # Initialize primary IG Markets data source
        if IG_MARKETS_AVAILABLE:
            try:
                self.price_source = EnhancedPaperTradingPriceSource()
                logger.info("✅ IG Markets price source initialized for exit strategy")
            except Exception as e:
                logger.warning(f"Failed to initialize IG Markets: {e}")
                
        # Fallback initialization
        if not self.price_source and YFINANCE_AVAILABLE:
            logger.info("📊 Using yfinance fallback for exit strategy")
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using your existing data infrastructure"""
        try:
            # Try IG Markets first (your primary source)
            if self.price_source:
                price = self.price_source.get_current_price(symbol)
                if price is not None:
                    logger.debug(f"📈 IG Markets price for {symbol}: ${price:.2f}")
                    return float(price)
            
            # Fallback to yfinance if needed
            if YFINANCE_AVAILABLE:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='1d')
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    logger.debug(f"📊 yfinance fallback price for {symbol}: ${price:.2f}")
                    return price
                    
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            
        return None
    
    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data"""
        try:
            # Get current price using your system
            current_price = self.get_current_price(symbol)
            if current_price is None:
                return {}
            
            # Basic market data structure
            market_data = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': datetime.now(),
                'data_source': 'IG Markets' if self.price_source else 'yfinance'
            }
            
            # Add technical indicators if yfinance data available
            if YFINANCE_AVAILABLE:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='30d')
                    if not hist.empty:
                        # Calculate simple technical indicators
                        market_data.update({
                            'sma_20': hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else current_price,
                            'volume': hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0,
                            'high_52w': hist['High'].max(),
                            'low_52w': hist['Low'].min(),
                            'volatility': hist['Close'].pct_change().std() * 100
                        })
                except Exception as e:
                    logger.debug(f"Technical indicators unavailable for {symbol}: {e}")
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return {}

class ExitStrategyEngine:
    """
    Main exit strategy engine using your IG Markets infrastructure
    
    Features:
    - Uses your existing IG Markets → yfinance fallback system
    - Safety flags to enable/disable functionality
    - Adaptive exit strategies based on your 44.92% success rate
    - Integration with your existing trading system
    """
    
    def __init__(self, enable_exit_strategy: bool = True):
        """
        Initialize exit strategy engine
        
        Args:
            enable_exit_strategy: Master safety flag to enable/disable exit strategy
        """
        self.enabled = enable_exit_strategy
        self.data_provider = IGMarketsExitDataProvider()
        
        # Configuration based on your system's performance profile
        self.config = {
            'profit_target_percentage': 2.8,  # Based on your $27.54 average winner
            'stop_loss_percentage': 2.0,     # Conservative stop loss
            'max_hold_hours': 18,             # Within trading day + overnight
            'confidence_threshold': 0.65,     # Above your average confidence
            'time_decay_factor': 0.1,        # Reduce confidence over time
        }
        
        # Safety flags for individual components
        self.flags = {
            'enable_profit_targets': True,
            'enable_stop_losses': True, 
            'enable_time_limits': True,
            'enable_technical_exits': TALIB_AVAILABLE,
            'enable_risk_management': True,
        }
        
        logger.info(f"✅ Exit Strategy Engine initialized (Enabled: {self.enabled})")
        if not self.enabled:
            logger.info("🚨 Exit Strategy DISABLED by safety flag")
    
    def is_enabled(self) -> bool:
        """Check if exit strategy is enabled"""
        return self.enabled
    
    def disable_exit_strategy(self, reason: str = "Safety override"):
        """Disable exit strategy with reason"""
        self.enabled = False
        logger.warning(f"🚨 Exit Strategy DISABLED: {reason}")
    
    def enable_exit_strategy(self, reason: str = "Manual enable"):
        """Re-enable exit strategy with reason"""
        self.enabled = True
        logger.info(f"✅ Exit Strategy ENABLED: {reason}")
    
    def evaluate_position_exit(self, 
                              symbol: str,
                              entry_price: float, 
                              predicted_action: str,
                              prediction_confidence: float,
                              entry_timestamp: str,
                              shares: int = 100) -> Dict[str, Any]:
        """
        Evaluate if a position should be exited
        
        Returns comprehensive exit analysis using your IG Markets data
        """
        if not self.enabled:
            return {
                'should_exit': False,
                'exit_reason': 'EXIT_STRATEGY_DISABLED',
                'exit_confidence': 0.0,
                'message': 'Exit strategy disabled by safety flag'
            }
        
        try:
            # Get current market data using your IG Markets system
            market_data = self.data_provider.get_market_data(symbol)
            if not market_data:
                return self._create_error_response("Unable to fetch market data")
            
            current_price = market_data['current_price']
            
            # Create position object
            entry_time = datetime.fromisoformat(entry_timestamp.replace('Z', '+00:00')) if isinstance(entry_timestamp, str) else entry_timestamp
            
            position = Position(
                symbol=symbol,
                entry_price=entry_price,
                current_price=current_price, 
                entry_time=entry_time,
                confidence=prediction_confidence,
                position_type=predicted_action,
                shares=shares
            )
            
            # Evaluate all exit conditions
            exit_signals = self._evaluate_all_exit_conditions(position, market_data)
            
            # Find highest priority exit signal
            active_signals = [signal for signal in exit_signals if signal.should_exit]
            
            if active_signals:
                # Take highest priority signal
                primary_signal = max(active_signals, key=lambda x: x.urgency)
                
                return {
                    'should_exit': True,
                    'exit_reason': primary_signal.reason.value,
                    'exit_confidence': primary_signal.confidence,
                    'current_price': current_price,
                    'return_percentage': ((current_price - entry_price) / entry_price) * 100,
                    'urgency': primary_signal.urgency,
                    'details': primary_signal.details,
                    'data_source': market_data.get('data_source', 'unknown'),
                    'all_signals': [{'reason': s.reason.value, 'confidence': s.confidence} for s in active_signals]
                }
            else:
                return {
                    'should_exit': False,
                    'exit_reason': 'NO_EXIT_CONDITIONS_MET',
                    'exit_confidence': 0.0,
                    'current_price': current_price,
                    'return_percentage': ((current_price - entry_price) / entry_price) * 100,
                    'data_source': market_data.get('data_source', 'unknown'),
                    'hold_recommendation': 'CONTINUE_HOLDING'
                }
                
        except Exception as e:
            logger.error(f"Error evaluating exit for {symbol}: {e}")
            return self._create_error_response(f"Exit evaluation error: {e}")
    
    def _evaluate_all_exit_conditions(self, position: Position, market_data: Dict) -> List[ExitSignal]:
        """Evaluate all exit conditions and return list of signals"""
        signals = []
        
        # 1. Profit Target Exit (60% weight in optimal strategy)
        if self.flags['enable_profit_targets']:
            profit_signal = self._evaluate_profit_target(position, market_data)
            if profit_signal.should_exit:
                signals.append(profit_signal)
        
        # 2. Time-Based Exit (25% weight in optimal strategy)
        if self.flags['enable_time_limits']:
            time_signal = self._evaluate_time_limit(position, market_data)
            if time_signal.should_exit:
                signals.append(time_signal)
        
        # 3. Stop Loss Exit (5% weight in optimal strategy)
        if self.flags['enable_stop_losses']:
            stop_signal = self._evaluate_stop_loss(position, market_data)
            if stop_signal.should_exit:
                signals.append(stop_signal)
        
        # 4. Technical Breakdown Exit (10% weight in optimal strategy)
        if self.flags['enable_technical_exits']:
            tech_signal = self._evaluate_technical_breakdown(position, market_data)
            if tech_signal.should_exit:
                signals.append(tech_signal)
        
        # 5. Risk Management Exit
        if self.flags['enable_risk_management']:
            risk_signal = self._evaluate_risk_management(position, market_data)
            if risk_signal.should_exit:
                signals.append(risk_signal)
        
        return signals
    
    def _evaluate_profit_target(self, position: Position, market_data: Dict) -> ExitSignal:
        """Evaluate profit target exit condition"""
        current_price = market_data['current_price']
        return_pct = ((current_price - position.entry_price) / position.entry_price) * 100
        
        # Adaptive profit target based on confidence (your optimal strategy)
        base_target = self.config['profit_target_percentage']
        confidence_multiplier = 0.8 + (position.confidence * 0.4)  # 0.8x to 1.2x based on confidence
        profit_target = base_target * confidence_multiplier
        
        if position.position_type == 'BUY' and return_pct >= profit_target:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.PROFIT_TARGET,
                urgency=4,
                confidence=0.85,
                recommended_exit_price=current_price,
                details=f"Profit target reached: {return_pct:.2f}% >= {profit_target:.2f}%"
            )
        elif position.position_type == 'SELL' and return_pct <= -profit_target:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.PROFIT_TARGET,
                urgency=4,
                confidence=0.85,
                recommended_exit_price=current_price,
                details=f"Short profit target: {return_pct:.2f}% <= -{profit_target:.2f}%"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_time_limit(self, position: Position, market_data: Dict) -> ExitSignal:
        """Evaluate time-based exit condition"""
        current_time = market_data.get('timestamp', datetime.now())
        hold_duration = current_time - position.entry_time
        max_hold = timedelta(hours=self.config['max_hold_hours'])
        
        if hold_duration >= max_hold:
            # Time decay reduces confidence over time
            time_confidence = max(0.3, 1.0 - (hold_duration.total_seconds() / max_hold.total_seconds()) * self.config['time_decay_factor'])
            
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.TIME_LIMIT,
                urgency=3,
                confidence=time_confidence,
                recommended_exit_price=market_data['current_price'],
                details=f"Max hold time exceeded: {hold_duration.total_seconds()/3600:.1f}h >= {self.config['max_hold_hours']}h"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_stop_loss(self, position: Position, market_data: Dict) -> ExitSignal:
        """Evaluate stop loss exit condition"""
        current_price = market_data['current_price']
        return_pct = ((current_price - position.entry_price) / position.entry_price) * 100
        stop_loss_threshold = -self.config['stop_loss_percentage']
        
        if position.position_type == 'BUY' and return_pct <= stop_loss_threshold:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.STOP_LOSS,
                urgency=5,  # Highest urgency for stop loss
                confidence=0.90,
                recommended_exit_price=current_price,
                details=f"Stop loss triggered: {return_pct:.2f}% <= {stop_loss_threshold:.2f}%"
            )
        elif position.position_type == 'SELL' and return_pct >= abs(stop_loss_threshold):
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.STOP_LOSS,
                urgency=5,
                confidence=0.90,
                recommended_exit_price=current_price,
                details=f"Short stop loss: {return_pct:.2f}% >= {abs(stop_loss_threshold):.2f}%"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_technical_breakdown(self, position: Position, market_data: Dict) -> ExitSignal:
        """Evaluate technical breakdown exit condition"""
        try:
            current_price = market_data['current_price']
            sma_20 = market_data.get('sma_20', current_price)
            
            # Simple technical breakdown: price below 20-day moving average
            if position.position_type == 'BUY' and current_price < (sma_20 * 0.97):  # 3% below SMA
                return ExitSignal(
                    should_exit=True,
                    reason=ExitReason.TECHNICAL_BREAKDOWN,
                    urgency=3,
                    confidence=0.70,
                    recommended_exit_price=current_price,
                    details=f"Technical breakdown: Price ${current_price:.2f} below SMA20 ${sma_20:.2f}"
                )
                
        except Exception as e:
            logger.debug(f"Technical analysis failed: {e}")
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_risk_management(self, position: Position, market_data: Dict) -> ExitSignal:
        """Evaluate risk management exit condition"""
        # Exit low confidence positions more aggressively
        if position.confidence < self.config['confidence_threshold']:
            current_time = market_data.get('timestamp', datetime.now())
            hold_duration = current_time - position.entry_time
            
            # Exit low confidence positions after 2 hours if not profitable
            if hold_duration >= timedelta(hours=2):
                current_price = market_data['current_price'] 
                return_pct = ((current_price - position.entry_price) / position.entry_price) * 100
                
                if abs(return_pct) < 0.5:  # Not profitable enough for low confidence
                    return ExitSignal(
                        should_exit=True,
                        reason=ExitReason.RISK_MANAGEMENT,
                        urgency=2,
                        confidence=0.60,
                        recommended_exit_price=current_price,
                        details=f"Low confidence position ({position.confidence:.1%}) with minimal return ({return_pct:.2f}%)"
                    )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            'should_exit': False,
            'exit_reason': 'ERROR',
            'exit_confidence': 0.0,
            'error': error_message,
            'message': 'Exit evaluation failed - holding position for safety'
        }
    
    def get_exit_conditions_status(self) -> Dict[str, Any]:
        """Get status of all exit conditions and safety flags"""
        return {
            'exit_strategy_enabled': self.enabled,
            'data_source_available': IG_MARKETS_AVAILABLE or YFINANCE_AVAILABLE,
            'ig_markets_available': IG_MARKETS_AVAILABLE,
            'yfinance_available': YFINANCE_AVAILABLE,
            'talib_available': TALIB_AVAILABLE,
            'exit_conditions': {
                'profit_targets': self.flags['enable_profit_targets'],
                'stop_losses': self.flags['enable_stop_losses'],
                'time_limits': self.flags['enable_time_limits'],
                'technical_exits': self.flags['enable_technical_exits'],
                'risk_management': self.flags['enable_risk_management']
            },
            'configuration': self.config
        }
    
    def set_safety_flag(self, flag_name: str, value: bool, reason: str = "Manual override"):
        """Set individual safety flags"""
        if flag_name in self.flags:
            old_value = self.flags[flag_name]
            self.flags[flag_name] = value
            logger.info(f"🔧 Safety flag '{flag_name}': {old_value} → {value} ({reason})")
        else:
            logger.warning(f"Unknown safety flag: {flag_name}")
    
    def evaluate_all_positions(self, positions: List[Dict]) -> List[Dict]:
        """Evaluate exit conditions for multiple positions"""
        results = []
        
        for pos in positions:
            try:
                result = self.evaluate_position_exit(
                    symbol=pos['symbol'],
                    entry_price=pos['entry_price'],
                    predicted_action=pos['predicted_action'],
                    prediction_confidence=pos['prediction_confidence'],
                    entry_timestamp=pos['entry_timestamp'],
                    shares=pos.get('shares', 100)
                )
                result['symbol'] = pos['symbol']
                results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating position {pos.get('symbol', 'unknown')}: {e}")
                results.append({
                    'symbol': pos.get('symbol', 'unknown'),
                    'should_exit': False,
                    'exit_reason': 'EVALUATION_ERROR',
                    'error': str(e)
                })
        
        return results

if __name__ == "__main__":
    # Test the exit strategy engine
    engine = ExitStrategyEngine(enable_exit_strategy=True)
    
    print("🚪 Exit Strategy Engine - IG Markets Integration Test")
    print("=" * 60)
    
    # Test position evaluation
    test_result = engine.evaluate_position_exit(
        symbol="ANZ.AX",
        entry_price=32.76,
        predicted_action="BUY",
        prediction_confidence=0.832,
        entry_timestamp="2025-09-04 02:30:04"
    )
    
    print(f"Test Result: {test_result}")
    print(f"\nExit Conditions Status: {engine.get_exit_conditions_status()}")
