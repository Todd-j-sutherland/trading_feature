#!/usr/bin/env python3
"""
Trading Outcome Tracker
Records actual trading results for ML training
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TradingOutcomeTracker:
    """Tracks trading signals and their outcomes"""
    
    def __init__(self, ml_pipeline):
        self.ml_pipeline = ml_pipeline
        self.active_trades = {}
        self.trades_file = 'data/active_trades.json'
        self.load_active_trades()
    
    def record_signal(self, symbol: str, signal_data: Dict):
        """Record a trading signal for tracking"""
        trade_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.active_trades[trade_id] = {
            'symbol': symbol,
            'signal_timestamp': datetime.now().isoformat(),
            'signal_type': signal_data.get('signal', 'UNKNOWN'),
            'sentiment_score': signal_data.get('overall_sentiment', 0),
            'confidence': signal_data.get('confidence', 0),
            'ml_prediction': signal_data.get('ml_prediction', {}),
            'feature_id': signal_data.get('ml_feature_id'),
            'entry_price': None,
            'executed': False
        }
        
        self.save_active_trades()
        return trade_id
    
    def update_trade_execution(self, trade_id: str, execution_data: Dict):
        """Update trade with execution details"""
        if trade_id in self.active_trades:
            self.active_trades[trade_id].update({
                'entry_price': execution_data.get('entry_price'),
                'entry_timestamp': execution_data.get('entry_timestamp', datetime.now().isoformat()),
                'position_size': execution_data.get('position_size'),
                'executed': True
            })
            self.save_active_trades()
    
    def close_trade(self, trade_id: str, exit_data: Dict):
        """Close a trade and record outcome"""
        if trade_id not in self.active_trades:
            logger.warning(f"Trade {trade_id} not found")
            return
        
        trade = self.active_trades[trade_id]
        
        # Calculate outcome
        outcome_data = {
            'symbol': trade['symbol'],
            'signal_timestamp': trade['signal_timestamp'],
            'signal_type': trade['signal_type'],
            'entry_price': trade['entry_price'],
            'exit_price': exit_data['price'],
            'exit_timestamp': exit_data['timestamp'],
            'max_drawdown': exit_data.get('max_drawdown', 0)
        }
        
        # Record to ML pipeline
        if trade.get('feature_id'):
            self.ml_pipeline.record_trading_outcome(
                trade['feature_id'], 
                outcome_data
            )
        
        # Remove from active trades
        del self.active_trades[trade_id]
        self.save_active_trades()
        
        logger.info(f"Trade {trade_id} closed and recorded")
    
    def check_stale_trades(self, days: int = 30):
        """Check for trades that should be closed"""
        cutoff_date = datetime.now() - timedelta(days=days)
        stale_trades = []
        
        for trade_id, trade in self.active_trades.items():
            trade_date = datetime.fromisoformat(trade['signal_timestamp'])
            if trade_date < cutoff_date:
                stale_trades.append(trade_id)
        
        return stale_trades
    
    def save_active_trades(self):
        """Save active trades to file"""
        os.makedirs(os.path.dirname(self.trades_file), exist_ok=True)
        with open(self.trades_file, 'w') as f:
            json.dump(self.active_trades, f, indent=2)
    
    def load_active_trades(self):
        """Load active trades from file"""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    self.active_trades = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.active_trades = {}
    
    def get_active_trades_summary(self) -> Dict:
        """Get summary of active trades"""
        return {
            'total_active': len(self.active_trades),
            'executed_trades': sum(1 for t in self.active_trades.values() if t.get('executed', False)),
            'pending_trades': sum(1 for t in self.active_trades.values() if not t.get('executed', False)),
            'oldest_trade': min(
                (datetime.fromisoformat(t['signal_timestamp']) for t in self.active_trades.values()),
                default=None
            ),
            'symbols': list(set(t['symbol'] for t in self.active_trades.values()))
        }
