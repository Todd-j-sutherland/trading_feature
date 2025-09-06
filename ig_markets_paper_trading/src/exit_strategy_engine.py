#!/usr/bin/env python3
"""
Enhanced Exit Strategy Engine for IG Markets Paper Trading
Integrated with your 7-bank trading system
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
import os
import sys

# Try to import IG Markets client
try:
    from .ig_markets_client import IGMarketsClient
    IG_CLIENT_AVAILABLE = True
except ImportError:
    try:
        from ig_markets_client import IGMarketsClient
        IG_CLIENT_AVAILABLE = True
    except ImportError:
        IG_CLIENT_AVAILABLE = False

# Fallback to yfinance
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

logger = logging.getLogger(__name__)

class ExitReason(Enum):
    """Exit reason enumeration"""
    TIME_LIMIT = "TIME_LIMIT"
    PROFIT_TARGET = "PROFIT_TARGET" 
    STOP_LOSS = "STOP_LOSS"
    TECHNICAL_BREAKDOWN = "TECHNICAL_BREAKDOWN"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    MANUAL = "MANUAL"
    NO_EXIT = "NO_EXIT"

@dataclass
class ExitSignal:
    """Exit signal data structure"""
    should_exit: bool
    reason: ExitReason
    urgency: int  # 1-5 scale (5 = immediate exit)
    confidence: float  # 0-1 scale
    recommended_exit_price: float = None
    details: str = ""

class ExitStrategyEngine:
    """
    Enhanced Exit Strategy Engine for your 7-bank trading system
    
    Banks: CBA.AX, WBC.AX, ANZ.AX, NAB.AX, MQG.AX, BEN.AX, BOQ.AX
    """
    
    def __init__(self, config_path: str = "config/ig_markets_config_banks.json"):
        """Initialize with bank-specific configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize IG Markets client if available
        self.ig_client = None
        if IG_CLIENT_AVAILABLE:
            try:
                self.ig_client = IGMarketsClient()
                logger.info("✅ IG Markets client initialized for exit strategy")
            except Exception as e:
                logger.warning(f"Failed to initialize IG Markets client: {e}")
        
        # Exit strategy configuration optimized for your bank trading
        self.exit_config = {
            'profit_target_percentage': 3.5,  # Increased for $100k account
            'stop_loss_percentage': 2.5,     # Conservative for banks
            'max_hold_hours': 24,             # Full trading day + overnight
            'confidence_threshold': 0.65,     # Your system's sweet spot
            'bank_specific_multipliers': {
                'CBA.AX': 1.0,  # Big 4 banks - standard targets
                'WBC.AX': 1.0,
                'ANZ.AX': 1.0, 
                'NAB.AX': 1.0,
                'MQG.AX': 1.2,  # More volatile - higher targets
                'BEN.AX': 0.8,  # Regional banks - conservative
                'BOQ.AX': 0.8
            }
        }
        
        self.enabled = True
        logger.info("✅ Exit Strategy Engine initialized for 7-bank system")
    
    def _load_config(self) -> Dict:
        """Load configuration for bank trading"""
        try:
            config_full_path = os.path.join(os.path.dirname(__file__), '..', self.config_path)
            with open(config_full_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            return {"symbol_mappings": {}}
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price using IG Markets or fallback"""
        try:
            # Try IG Markets first
            if self.ig_client:
                # Get the epic mapping for this symbol
                symbol_config = self.config.get('symbol_mappings', {}).get(symbol, {})
                epic = symbol_config.get('ig_epic') or symbol_config.get('fallback_epic')
                
                if epic:
                    price = self.ig_client.get_market_price(epic)
                    if price:
                        logger.debug(f"📈 IG Markets price for {symbol}: ${price:.2f}")
                        return float(price)
            
            # Fallback to yfinance
            if YFINANCE_AVAILABLE:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='1d')
                if not data.empty:
                    price = float(data['Close'].iloc[-1])
                    logger.debug(f"📊 yfinance price for {symbol}: ${price:.2f}")
                    return price
                    
        except Exception as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            
        return None
    
    def evaluate_exit(self, position: Dict) -> Dict[str, Any]:
        """
        Main exit evaluation for a bank position
        
        Args:
            position: Dict with keys: symbol, entry_price, entry_time, confidence, action, quantity
        
        Returns:
            Exit decision with reasoning
        """
        if not self.enabled:
            return self._create_no_exit_response("Exit strategy disabled")
        
        try:
            symbol = position['symbol']
            entry_price = position['entry_price']
            entry_time = datetime.fromisoformat(position['entry_time'].replace('Z', '+00:00')) if isinstance(position['entry_time'], str) else position['entry_time']
            confidence = position['confidence']
            action = position['action']
            
            # Get current price
            current_price = self.get_current_price(symbol)
            if current_price is None:
                return self._create_error_response("Unable to fetch current price")
            
            # Calculate return
            if action == 'BUY':
                return_pct = ((current_price - entry_price) / entry_price) * 100
            else:  # SELL
                return_pct = ((entry_price - current_price) / entry_price) * 100
            
            # Evaluate all exit conditions
            exit_signals = []
            
            # 1. Profit target (bank-specific)
            profit_signal = self._evaluate_profit_target(symbol, return_pct, confidence, action)
            if profit_signal.should_exit:
                exit_signals.append(profit_signal)
            
            # 2. Stop loss
            stop_signal = self._evaluate_stop_loss(symbol, return_pct, action)
            if stop_signal.should_exit:
                exit_signals.append(stop_signal)
            
            # 3. Time limit
            time_signal = self._evaluate_time_limit(entry_time, confidence)
            if time_signal.should_exit:
                exit_signals.append(time_signal)
            
            # 4. Risk management for banks
            risk_signal = self._evaluate_bank_risk_management(symbol, return_pct, confidence, entry_time)
            if risk_signal.should_exit:
                exit_signals.append(risk_signal)
            
            # Return highest priority exit signal
            if exit_signals:
                primary_signal = max(exit_signals, key=lambda x: x.urgency)
                return {
                    'should_exit': True,
                    'exit_reason': primary_signal.reason.value,
                    'exit_confidence': primary_signal.confidence,
                    'current_price': current_price,
                    'return_percentage': return_pct,
                    'urgency': primary_signal.urgency,
                    'details': primary_signal.details,
                    'recommended_exit_price': current_price,
                    'data_source': 'IG Markets' if self.ig_client else 'yfinance'
                }
            else:
                return {
                    'should_exit': False,
                    'exit_reason': 'NO_EXIT_CONDITIONS_MET',
                    'current_price': current_price,
                    'return_percentage': return_pct,
                    'hold_recommendation': 'CONTINUE_HOLDING',
                    'data_source': 'IG Markets' if self.ig_client else 'yfinance'
                }
                
        except Exception as e:
            logger.error(f"Error evaluating exit for {position.get('symbol', 'unknown')}: {e}")
            return self._create_error_response(f"Exit evaluation error: {e}")
    
    def _evaluate_profit_target(self, symbol: str, return_pct: float, confidence: float, action: str) -> ExitSignal:
        """Evaluate profit target with bank-specific adjustments"""
        
        # Get bank-specific multiplier
        multiplier = self.exit_config['bank_specific_multipliers'].get(symbol, 1.0)
        base_target = self.exit_config['profit_target_percentage']
        
        # Adjust for confidence (higher confidence = higher targets)
        confidence_adj = 0.8 + (confidence * 0.4)  # 0.8x to 1.2x
        
        profit_target = base_target * multiplier * confidence_adj
        
        should_exit = False
        if action == 'BUY' and return_pct >= profit_target:
            should_exit = True
        elif action == 'SELL' and return_pct >= profit_target:
            should_exit = True
        
        if should_exit:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.PROFIT_TARGET,
                urgency=4,
                confidence=0.85,
                details=f"{symbol} profit target: {return_pct:.2f}% >= {profit_target:.2f}% (bank mult: {multiplier}x)"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_stop_loss(self, symbol: str, return_pct: float, action: str) -> ExitSignal:
        """Evaluate stop loss for bank positions"""
        
        # Bank-specific stop loss (more conservative for regional banks)
        base_stop = self.exit_config['stop_loss_percentage']
        if symbol in ['BEN.AX', 'BOQ.AX']:
            stop_threshold = -base_stop * 0.8  # Tighter stops for regional banks
        else:
            stop_threshold = -base_stop
        
        if return_pct <= stop_threshold:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.STOP_LOSS,
                urgency=5,  # Highest urgency
                confidence=0.95,
                details=f"{symbol} stop loss: {return_pct:.2f}% <= {stop_threshold:.2f}%"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_time_limit(self, entry_time: datetime, confidence: float) -> ExitSignal:
        """Evaluate time-based exit"""
        
        current_time = datetime.now()
        if entry_time.tzinfo is None:
            entry_time = entry_time.replace(tzinfo=current_time.tzinfo)
        
        hold_duration = current_time - entry_time
        max_hold = timedelta(hours=self.exit_config['max_hold_hours'])
        
        if hold_duration >= max_hold:
            # Lower confidence positions exit sooner
            time_confidence = max(0.4, confidence * 0.8)
            
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.TIME_LIMIT,
                urgency=3,
                confidence=time_confidence,
                details=f"Time limit reached: {hold_duration.total_seconds()/3600:.1f}h >= {self.exit_config['max_hold_hours']}h"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _evaluate_bank_risk_management(self, symbol: str, return_pct: float, confidence: float, entry_time: datetime) -> ExitSignal:
        """Bank-specific risk management"""
        
        # Exit low confidence bank positions more aggressively
        if confidence < self.exit_config['confidence_threshold']:
            current_time = datetime.now()
            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=current_time.tzinfo)
                
            hold_duration = current_time - entry_time
            
            # For big 4 banks, be more patient with low confidence
            patience_hours = 4 if symbol in ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX'] else 2
            
            if hold_duration >= timedelta(hours=patience_hours) and abs(return_pct) < 1.0:
                return ExitSignal(
                    should_exit=True,
                    reason=ExitReason.RISK_MANAGEMENT,
                    urgency=2,
                    confidence=0.70,
                    details=f"Low confidence {symbol} ({confidence:.1%}) with minimal return ({return_pct:.2f}%) after {patience_hours}h"
                )
        
        return ExitSignal(should_exit=False, reason=ExitReason.NO_EXIT, urgency=0, confidence=0.0)
    
    def _create_no_exit_response(self, message: str) -> Dict[str, Any]:
        """Create no-exit response"""
        return {
            'should_exit': False,
            'exit_reason': 'NO_EXIT',
            'exit_confidence': 0.0,
            'message': message
        }
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'should_exit': False,
            'exit_reason': 'ERROR',
            'exit_confidence': 0.0,
            'error': error_message,
            'message': 'Exit evaluation failed - holding position for safety'
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get exit strategy status"""
        return {
            'enabled': self.enabled,
            'ig_client_available': IG_CLIENT_AVAILABLE and self.ig_client is not None,
            'yfinance_available': YFINANCE_AVAILABLE,
            'supported_banks': list(self.exit_config['bank_specific_multipliers'].keys()),
            'configuration': self.exit_config
        }
    
    def enable(self):
        """Enable exit strategy"""
        self.enabled = True
        logger.info("✅ Exit Strategy Engine enabled")
    
    def disable(self):
        """Disable exit strategy"""
        self.enabled = False
        logger.warning("🚨 Exit Strategy Engine disabled")

if __name__ == "__main__":
    # Test the exit strategy engine
    engine = ExitStrategyEngine()
    
    print("🚪 Enhanced Exit Strategy Engine - 7 Banks Test")
    print("=" * 50)
    
    # Test with a bank position
    test_position = {
        'symbol': 'CBA.AX',
        'entry_price': 135.50,
        'entry_time': '2025-09-05 09:30:00',
        'confidence': 0.78,
        'action': 'BUY',
        'quantity': 100
    }
    
    result = engine.evaluate_exit(test_position)
    print(f"Test Result: {result}")
    print(f"Engine Status: {engine.get_status()}")
