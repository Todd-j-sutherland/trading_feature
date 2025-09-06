#!/usr/bin/env python3
"""
Exit Strategy Engine - Phase 4 Development

This module provides the missing piece that answers the fundamental question:
"How does it know when to exit the prediction?"

The engine evaluates multiple exit conditions and determines when to close positions.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import sqlite3
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ExitReason(Enum):
    """Exit reason enumeration"""
    TIME_LIMIT = "TIME_LIMIT"
    PROFIT_TARGET = "PROFIT_TARGET" 
    STOP_LOSS = "STOP_LOSS"
    SENTIMENT_REVERSAL = "SENTIMENT_REVERSAL"
    TECHNICAL_BREAKDOWN = "TECHNICAL_BREAKDOWN"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    MANUAL = "MANUAL"

@dataclass
class Position:
    """Position data structure"""
    symbol: str
    entry_price: float
    current_price: float
    entry_time: datetime
    confidence: float
    position_type: str  # 'BUY' or 'SELL'
    shares: int
    market_context: str  # 'BULLISH', 'NEUTRAL', 'BEARISH'
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

class ExitCondition:
    """Base class for exit conditions"""
    
    def __init__(self, name: str, priority: int = 1):
        self.name = name
        self.priority = priority  # Higher number = higher priority
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Evaluate if this condition triggers an exit"""
        raise NotImplementedError("Subclasses must implement evaluate method")

class TimeBasedExit(ExitCondition):
    """Time-based exit condition"""
    
    def __init__(self, max_hold_days: int = 5):
        super().__init__("Time-Based Exit", priority=2)
        self.max_hold_days = max_hold_days
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Exit if position held too long"""
        current_time = current_data.get('current_time', datetime.now())
        hold_duration = current_time - position.entry_time
        
        if hold_duration.days >= self.max_hold_days:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.TIME_LIMIT,
                urgency=4,
                confidence=1.0,
                recommended_exit_price=position.current_price,
                details=f"Position held for {hold_duration.days} days (max: {self.max_hold_days})"
            )
        
        # Warning at 80% of time limit
        if hold_duration.days >= (self.max_hold_days * 0.8):
            return ExitSignal(
                should_exit=False,
                reason=ExitReason.TIME_LIMIT,
                urgency=2,
                confidence=0.7,
                details=f"Position approaching time limit ({hold_duration.days}/{self.max_hold_days} days)"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.TIME_LIMIT, urgency=1, confidence=0.0)

class ProfitTargetExit(ExitCondition):
    """Profit target exit condition"""
    
    def __init__(self):
        super().__init__("Profit Target Exit", priority=3)
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Exit if profit target reached"""
        profit_pct = self._calculate_profit_percentage(position)
        profit_target = self._calculate_profit_target(position)
        
        if profit_pct >= profit_target:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.PROFIT_TARGET,
                urgency=5,
                confidence=1.0,
                recommended_exit_price=position.current_price,
                details=f"Profit target reached: {profit_pct:.1f}% >= {profit_target:.1f}%"
            )
        
        # Warning at 80% of profit target
        if profit_pct >= (profit_target * 0.8):
            return ExitSignal(
                should_exit=False,
                reason=ExitReason.PROFIT_TARGET,
                urgency=2,
                confidence=0.6,
                details=f"Approaching profit target: {profit_pct:.1f}% (target: {profit_target:.1f}%)"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.PROFIT_TARGET, urgency=1, confidence=0.0)
    
    def _calculate_profit_percentage(self, position: Position) -> float:
        """Calculate current profit percentage"""
        if position.position_type == 'BUY':
            return ((position.current_price - position.entry_price) / position.entry_price) * 100
        else:  # SELL
            return ((position.entry_price - position.current_price) / position.entry_price) * 100
    
    def _calculate_profit_target(self, position: Position) -> float:
        """Calculate dynamic profit target based on confidence"""
        # Base target: 3% for medium confidence (65%)
        base_target = 3.0
        
        # Adjust based on confidence
        if position.confidence >= 0.8:
            return base_target * 1.5  # 4.5% for high confidence
        elif position.confidence >= 0.7:
            return base_target * 1.2  # 3.6% for good confidence
        elif position.confidence >= 0.6:
            return base_target       # 3.0% for medium confidence
        else:
            return base_target * 0.8  # 2.4% for low confidence

class StopLossExit(ExitCondition):
    """Stop-loss exit condition"""
    
    def __init__(self):
        super().__init__("Stop Loss Exit", priority=5)  # Highest priority
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Exit if stop-loss triggered"""
        loss_pct = abs(self._calculate_loss_percentage(position))
        stop_loss_pct = self._calculate_stop_loss(position)
        
        if loss_pct >= stop_loss_pct:
            return ExitSignal(
                should_exit=True,
                reason=ExitReason.STOP_LOSS,
                urgency=5,
                confidence=1.0,
                recommended_exit_price=position.current_price,
                details=f"Stop loss triggered: -{loss_pct:.1f}% >= -{stop_loss_pct:.1f}%"
            )
        
        # Warning at 80% of stop loss
        if loss_pct >= (stop_loss_pct * 0.8):
            return ExitSignal(
                should_exit=False,
                reason=ExitReason.STOP_LOSS,
                urgency=3,
                confidence=0.8,
                details=f"Approaching stop loss: -{loss_pct:.1f}% (limit: -{stop_loss_pct:.1f}%)"
            )
        
        return ExitSignal(should_exit=False, reason=ExitReason.STOP_LOSS, urgency=1, confidence=0.0)
    
    def _calculate_loss_percentage(self, position: Position) -> float:
        """Calculate current loss percentage (negative value)"""
        if position.position_type == 'BUY':
            return ((position.current_price - position.entry_price) / position.entry_price) * 100
        else:  # SELL
            return ((position.entry_price - position.current_price) / position.entry_price) * 100
    
    def _calculate_stop_loss(self, position: Position) -> float:
        """Calculate dynamic stop-loss based on confidence and market context"""
        # Base stop-loss: 2.5% for medium confidence
        base_stop_loss = 2.5
        
        # Adjust based on confidence (higher confidence = wider stops)
        if position.confidence >= 0.8:
            confidence_adjustment = 1.4  # 3.5% for high confidence
        elif position.confidence >= 0.7:
            confidence_adjustment = 1.2  # 3.0% for good confidence
        elif position.confidence >= 0.6:
            confidence_adjustment = 1.0  # 2.5% for medium confidence
        else:
            confidence_adjustment = 0.8  # 2.0% for low confidence
        
        # Adjust based on market context
        market_adjustments = {
            'BULLISH': 1.2,   # Wider stops in bullish market
            'NEUTRAL': 1.0,   # Standard stops
            'BEARISH': 0.8    # Tighter stops in bearish market
        }
        
        market_adjustment = market_adjustments.get(position.market_context, 1.0)
        
        return base_stop_loss * confidence_adjustment * market_adjustment

class SentimentReversalExit(ExitCondition):
    """Sentiment reversal exit condition"""
    
    def __init__(self, db_path: str = "predictions.db"):
        super().__init__("Sentiment Reversal Exit", priority=3)
        self.db_path = db_path
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Exit if sentiment has reversed significantly"""
        try:
            current_sentiment = self._get_current_sentiment(position.symbol)
            entry_sentiment = self._get_entry_sentiment(position)
            
            if current_sentiment is None or entry_sentiment is None:
                return ExitSignal(should_exit=False, reason=ExitReason.SENTIMENT_REVERSAL, urgency=1, confidence=0.0)
            
            sentiment_change = current_sentiment - entry_sentiment
            
            # For BUY positions: exit if sentiment becomes very negative
            # For SELL positions: exit if sentiment becomes very positive
            reversal_threshold = 0.4  # 40% sentiment swing
            
            if position.position_type == 'BUY' and sentiment_change <= -reversal_threshold:
                return ExitSignal(
                    should_exit=True,
                    reason=ExitReason.SENTIMENT_REVERSAL,
                    urgency=4,
                    confidence=0.8,
                    recommended_exit_price=position.current_price,
                    details=f"Sentiment reversed: {entry_sentiment:.2f} → {current_sentiment:.2f}"
                )
            
            elif position.position_type == 'SELL' and sentiment_change >= reversal_threshold:
                return ExitSignal(
                    should_exit=True,
                    reason=ExitReason.SENTIMENT_REVERSAL,
                    urgency=4,
                    confidence=0.8,
                    recommended_exit_price=position.current_price,
                    details=f"Sentiment reversed: {entry_sentiment:.2f} → {current_sentiment:.2f}"
                )
            
            return ExitSignal(should_exit=False, reason=ExitReason.SENTIMENT_REVERSAL, urgency=1, confidence=0.0)
            
        except Exception as e:
            logger.warning(f"Error evaluating sentiment reversal: {e}")
            return ExitSignal(should_exit=False, reason=ExitReason.SENTIMENT_REVERSAL, urgency=1, confidence=0.0)
    
    def _get_current_sentiment(self, symbol: str) -> Optional[float]:
        """Get current sentiment for symbol"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT AVG(sentiment_score) 
                FROM news_sentiment 
                WHERE symbol = ? 
                AND published_date > datetime('now', '-24 hours')
            """
            result = conn.execute(query, (symbol,)).fetchone()
            conn.close()
            return result[0] if result and result[0] is not None else None
        except Exception as e:
            logger.warning(f"Error getting current sentiment: {e}")
            return None
    
    def _get_entry_sentiment(self, position: Position) -> Optional[float]:
        """Get sentiment at time of entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            query = """
                SELECT news_sentiment 
                FROM predictions 
                WHERE id = ?
            """
            result = conn.execute(query, (position.original_prediction_id,)).fetchone()
            conn.close()
            return result[0] if result and result[0] is not None else None
        except Exception as e:
            logger.warning(f"Error getting entry sentiment: {e}")
            return None

class TechnicalBreakdownExit(ExitCondition):
    """Technical breakdown exit condition"""
    
    def __init__(self):
        super().__init__("Technical Breakdown Exit", priority=4)
    
    def evaluate(self, position: Position, current_data: Dict) -> ExitSignal:
        """Exit if technical indicators show breakdown"""
        try:
            # Get technical data from current_data
            rsi = current_data.get('rsi')
            macd_signal = current_data.get('macd_signal')
            price_trend = current_data.get('price_trend')
            
            if not all([rsi is not None, macd_signal, price_trend]):
                return ExitSignal(should_exit=False, reason=ExitReason.TECHNICAL_BREAKDOWN, urgency=1, confidence=0.0)
            
            breakdown_signals = []
            
            # RSI breakdown signals
            if position.position_type == 'BUY':
                if rsi > 80:  # Extremely overbought
                    breakdown_signals.append("RSI overbought (>80)")
                elif rsi > 70 and macd_signal == 'bearish':
                    breakdown_signals.append("RSI overbought + bearish MACD")
            else:  # SELL position
                if rsi < 20:  # Extremely oversold
                    breakdown_signals.append("RSI oversold (<20)")
                elif rsi < 30 and macd_signal == 'bullish':
                    breakdown_signals.append("RSI oversold + bullish MACD")
            
            # Price trend breakdown
            if position.position_type == 'BUY' and price_trend == 'strongly_bearish':
                breakdown_signals.append("Strong bearish price trend")
            elif position.position_type == 'SELL' and price_trend == 'strongly_bullish':
                breakdown_signals.append("Strong bullish price trend")
            
            # Multiple breakdown signals = high urgency exit
            if len(breakdown_signals) >= 2:
                return ExitSignal(
                    should_exit=True,
                    reason=ExitReason.TECHNICAL_BREAKDOWN,
                    urgency=4,
                    confidence=0.9,
                    recommended_exit_price=position.current_price,
                    details=f"Technical breakdown: {', '.join(breakdown_signals)}"
                )
            
            # Single breakdown signal = warning
            elif len(breakdown_signals) == 1:
                return ExitSignal(
                    should_exit=False,
                    reason=ExitReason.TECHNICAL_BREAKDOWN,
                    urgency=3,
                    confidence=0.6,
                    details=f"Technical warning: {breakdown_signals[0]}"
                )
            
            return ExitSignal(should_exit=False, reason=ExitReason.TECHNICAL_BREAKDOWN, urgency=1, confidence=0.0)
            
        except Exception as e:
            logger.warning(f"Error evaluating technical breakdown: {e}")
            return ExitSignal(should_exit=False, reason=ExitReason.TECHNICAL_BREAKDOWN, urgency=1, confidence=0.0)

class ExitStrategyEngine:
    """
    Main Exit Strategy Engine
    
    This is the missing piece that answers: "How does it know when to exit the prediction?"
    """
    
    def __init__(self, db_path: str = "predictions.db"):
        self.db_path = db_path
        self.exit_conditions = [
            StopLossExit(),                           # Priority 5 (highest)
            TechnicalBreakdownExit(),                # Priority 4
            ProfitTargetExit(),                      # Priority 3
            SentimentReversalExit(db_path),          # Priority 3
            TimeBasedExit(max_hold_days=5)           # Priority 2
        ]
        
        logger.info("✅ Exit Strategy Engine initialized with 5 exit conditions")
    
    def evaluate_position_exit(self, position: Position, current_data: Dict) -> ExitSignal:
        """
        Main entry point: Evaluate if a position should be exited
        
        This is THE ANSWER to "how does it know when to exit the prediction"
        """
        logger.info(f"🔍 Evaluating exit conditions for {position.symbol}")
        
        exit_signals = []
        
        # Evaluate all exit conditions
        for condition in self.exit_conditions:
            try:
                signal = condition.evaluate(position, current_data)
                if signal.should_exit or signal.urgency > 1:
                    exit_signals.append((condition, signal))
                    logger.info(f"   {condition.name}: {signal.reason.value} | Urgency: {signal.urgency}")
            except Exception as e:
                logger.warning(f"   Error in {condition.name}: {e}")
        
        # Return the highest priority exit signal
        if exit_signals:
            # Sort by priority (highest first), then by urgency
            exit_signals.sort(key=lambda x: (x[0].priority, x[1].urgency), reverse=True)
            best_condition, best_signal = exit_signals[0]
            
            if best_signal.should_exit:
                logger.info(f"🚪 EXIT RECOMMENDED: {best_signal.reason.value} - {best_signal.details}")
            else:
                logger.info(f"⚠️  EXIT WARNING: {best_signal.reason.value} - {best_signal.details}")
            
            return best_signal
        
        # No exit conditions triggered
        logger.info("✅ No exit conditions triggered - HOLD position")
        return ExitSignal(
            should_exit=False, 
            reason=ExitReason.MANUAL, 
            urgency=1, 
            confidence=0.0,
            details="All exit conditions evaluated - position should be held"
        )
    
    def evaluate_all_positions(self, positions: List[Position], current_data: Dict) -> List[Tuple[Position, ExitSignal]]:
        """Evaluate exit conditions for multiple positions"""
        results = []
        
        logger.info(f"🔍 Evaluating exit conditions for {len(positions)} positions")
        
        for position in positions:
            exit_signal = self.evaluate_position_exit(position, current_data)
            results.append((position, exit_signal))
        
        # Summary
        exit_count = sum(1 for _, signal in results if signal.should_exit)
        warning_count = sum(1 for _, signal in results if not signal.should_exit and signal.urgency > 1)
        
        logger.info(f"📊 Exit evaluation complete: {exit_count} exits, {warning_count} warnings")
        
        return results
    
    def get_exit_conditions_status(self) -> Dict[str, Any]:
        """Get status of all exit conditions"""
        return {
            'conditions': [
                {
                    'name': condition.name,
                    'priority': condition.priority,
                    'type': type(condition).__name__
                }
                for condition in self.exit_conditions
            ],
            'total_conditions': len(self.exit_conditions),
            'engine_status': 'operational'
        }

def create_mock_position(symbol: str = "CBA.AX", days_ago: int = 2) -> Position:
    """Create a mock position for testing"""
    return Position(
        symbol=symbol,
        entry_price=120.50,
        current_price=118.25,  # Small loss
        entry_time=datetime.now() - timedelta(days=days_ago),
        confidence=0.75,
        position_type='BUY',
        shares=100,
        market_context='NEUTRAL',
        original_prediction_id='test_prediction_123'
    )

def create_mock_current_data() -> Dict:
    """Create mock current market data for testing"""
    return {
        'current_time': datetime.now(),
        'rsi': 65.0,
        'macd_signal': 'neutral',
        'price_trend': 'sideways',
        'volume_trend': 0.05,
        'market_sentiment': 0.15
    }

def main():
    """Test the Exit Strategy Engine"""
    print("🧪 Testing Exit Strategy Engine")
    print("=" * 50)
    
    # Initialize engine
    engine = ExitStrategyEngine()
    
    # Create test position
    position = create_mock_position()
    current_data = create_mock_current_data()
    
    print(f"\n📊 Test Position:")
    print(f"   Symbol: {position.symbol}")
    print(f"   Entry Price: ${position.entry_price:.2f}")
    print(f"   Current Price: ${position.current_price:.2f}")
    print(f"   Hold Duration: {(datetime.now() - position.entry_time).days} days")
    print(f"   Confidence: {position.confidence:.1%}")
    
    # Evaluate exit
    exit_signal = engine.evaluate_position_exit(position, current_data)
    
    print(f"\n🎯 Exit Evaluation Result:")
    print(f"   Should Exit: {'YES' if exit_signal.should_exit else 'NO'}")
    print(f"   Reason: {exit_signal.reason.value}")
    print(f"   Urgency: {exit_signal.urgency}/5")
    print(f"   Confidence: {exit_signal.confidence:.1%}")
    print(f"   Details: {exit_signal.details}")
    
    # Test with different scenarios
    print(f"\n🔬 Testing Different Scenarios:")
    
    # Scenario 1: Profitable position
    profitable_position = create_mock_position()
    profitable_position.current_price = 125.00  # 3.7% profit
    signal = engine.evaluate_position_exit(profitable_position, current_data)
    print(f"   Profitable Position: {'EXIT' if signal.should_exit else 'HOLD'} - {signal.reason.value}")
    
    # Scenario 2: Loss position
    loss_position = create_mock_position()
    loss_position.current_price = 117.00  # -2.9% loss
    signal = engine.evaluate_position_exit(loss_position, current_data)
    print(f"   Loss Position: {'EXIT' if signal.should_exit else 'HOLD'} - {signal.reason.value}")
    
    # Scenario 3: Old position
    old_position = create_mock_position(days_ago=6)  # 6 days old
    signal = engine.evaluate_position_exit(old_position, current_data)
    print(f"   Old Position: {'EXIT' if signal.should_exit else 'HOLD'} - {signal.reason.value}")
    
    print(f"\n✅ Exit Strategy Engine test complete!")
    print(f"🎯 This answers: 'How does it know when to exit the prediction?'")

if __name__ == "__main__":
    main()
