#!/usr/bin/env python3
"""
Profit Measurement System
Advanced profit tracking and minimum profit threshold monitoring
"""

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfitTracker:
    """Advanced profit tracking and analysis system"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = db_path
        self.default_position_size = 1000.0  # $1000 default position
        self.trading_fees = 10.0  # $10 per trade (round trip)
        self.slippage_pct = 0.001  # 0.1% slippage
        
        # Risk management thresholds
        self.max_daily_loss_pct = -2.0      # -2% max daily loss
        self.min_weekly_profit_pct = 1.0    # +1% min weekly profit
        self.min_monthly_profit_pct = 5.0   # +5% min monthly profit
        self.max_drawdown_pct = -5.0        # -5% max drawdown
        self.target_sharpe_ratio = 1.5      # >1.5 Sharpe ratio target
        
    def create_profit_tracking_table(self):
        """Create profit tracking table if it doesn't exist"""
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS profit_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prediction_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            trade_date DATE NOT NULL,
            entry_price REAL NOT NULL,
            exit_price REAL,
            position_size REAL DEFAULT 1000.0,
            shares_traded REAL,
            gross_profit REAL,
            trading_fees REAL DEFAULT 10.0,
            slippage_cost REAL,
            net_profit REAL,
            profit_percentage REAL,
            holding_period_hours REAL,
            roi_annualized REAL,
            trade_status TEXT DEFAULT 'OPEN',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (prediction_id) REFERENCES predictions(prediction_id)
        );
        """
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(create_table_sql)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_profit_tracking_symbol ON profit_tracking(symbol)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_profit_tracking_date ON profit_tracking(trade_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_profit_tracking_prediction ON profit_tracking(prediction_id)")
            
        logger.info("✅ Profit tracking table created/verified")
    
    def calculate_position_profit(self, prediction_id: str, exit_price: float = None, 
                                position_size: float = None) -> Dict:
        """Calculate profit for a specific trading position"""
        
        if position_size is None:
            position_size = self.default_position_size
            
        # Get prediction data
        with sqlite3.connect(self.db_path) as conn:
            query = """
            SELECT p.symbol, p.entry_price, p.predicted_action, p.prediction_timestamp,
                   o.actual_return, o.evaluation_timestamp, o.exit_price
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.prediction_id = ?
            """
            result = conn.execute(query, (prediction_id,)).fetchone()
            
        if not result:
            return {'error': 'Prediction not found'}
        
        symbol, entry_price, action, entry_time, actual_return, eval_time, db_exit_price = result
        
        # Use provided exit price or database exit price
        if exit_price is None:
            exit_price = db_exit_price
            
        if exit_price is None:
            return {'error': 'No exit price available'}
        
        # Calculate trade metrics
        shares_traded = position_size / entry_price
        gross_profit = (exit_price - entry_price) * shares_traded
        
        # Apply fees and slippage
        slippage_cost = position_size * self.slippage_pct
        total_fees = self.trading_fees + slippage_cost
        net_profit = gross_profit - total_fees
        
        # Calculate percentages
        profit_percentage = (net_profit / position_size) * 100
        
        # Calculate holding period
        holding_period_hours = 0
        if entry_time and eval_time:
            entry_dt = datetime.fromisoformat(entry_time.replace('Z', '+00:00'))
            eval_dt = datetime.fromisoformat(eval_time.replace('Z', '+00:00'))
            holding_period_hours = (eval_dt - entry_dt).total_seconds() / 3600
        
        # Calculate annualized ROI
        roi_annualized = 0
        if holding_period_hours > 0:
            days_held = holding_period_hours / 24
            roi_annualized = ((1 + profit_percentage/100) ** (365/days_held) - 1) * 100
        
        return {
            'prediction_id': prediction_id,
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': position_size,
            'shares_traded': round(shares_traded, 4),
            'gross_profit': round(gross_profit, 2),
            'trading_fees': self.trading_fees,
            'slippage_cost': round(slippage_cost, 2),
            'net_profit': round(net_profit, 2),
            'profit_percentage': round(profit_percentage, 4),
            'holding_period_hours': round(holding_period_hours, 2),
            'roi_annualized': round(roi_annualized, 2),
            'predicted_action': action
        }
    
    def record_profit_trade(self, profit_data: Dict):
        """Record a completed trade in profit tracking table"""
        
        insert_sql = """
        INSERT OR REPLACE INTO profit_tracking 
        (prediction_id, symbol, trade_date, entry_price, exit_price, position_size,
         shares_traded, gross_profit, trading_fees, slippage_cost, net_profit,
         profit_percentage, holding_period_hours, roi_annualized, trade_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'CLOSED')
        """
        
        trade_date = datetime.now().date()
        
        values = (
            profit_data['prediction_id'],
            profit_data['symbol'],
            trade_date,
            profit_data['entry_price'],
            profit_data['exit_price'],
            profit_data['position_size'],
            profit_data['shares_traded'],
            profit_data['gross_profit'],
            profit_data['trading_fees'],
            profit_data['slippage_cost'],
            profit_data['net_profit'],
            profit_data['profit_percentage'],
            profit_data['holding_period_hours'],
            profit_data['roi_annualized']
        )
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(insert_sql, values)
            
        logger.info(f"✅ Recorded profit trade: {profit_data['symbol']} = ${profit_data['net_profit']}")
    
    def get_daily_profit_summary(self, target_date: str = None) -> Dict:
        """Get daily profit summary and check against minimum thresholds"""
        
        if target_date is None:
            target_date = datetime.now().date()
        
        query = """
        SELECT 
            COUNT(*) as total_trades,
            SUM(net_profit) as total_profit,
            AVG(net_profit) as avg_profit_per_trade,
            SUM(position_size) as total_invested,
            COUNT(CASE WHEN net_profit > 0 THEN 1 END) as winning_trades,
            COUNT(CASE WHEN net_profit < 0 THEN 1 END) as losing_trades,
            MAX(net_profit) as best_trade,
            MIN(net_profit) as worst_trade
        FROM profit_tracking 
        WHERE trade_date = ? AND trade_status = 'CLOSED'
        """
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, (target_date,)).fetchone()
        
        if not result or result[0] == 0:
            return {
                'date': str(target_date),
                'total_trades': 0,
                'total_profit': 0,
                'profit_percentage': 0,
                'meets_minimum': True,  # No trades = no loss
                'status': 'NO_TRADES'
            }
        
        total_trades, total_profit, avg_profit, total_invested, winning, losing, best, worst = result
        
        # Calculate daily return percentage
        daily_return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        # Check against minimum threshold
        meets_minimum = daily_return_pct >= self.max_daily_loss_pct
        
        status = "HEALTHY"
        if daily_return_pct < self.max_daily_loss_pct:
            status = "LOSS_LIMIT_EXCEEDED"
        elif daily_return_pct < 0:
            status = "DAILY_LOSS"
        elif daily_return_pct > 2.0:
            status = "EXCELLENT_DAY"
        
        return {
            'date': str(target_date),
            'total_trades': total_trades,
            'total_profit': round(total_profit, 2),
            'profit_percentage': round(daily_return_pct, 4),
            'avg_profit_per_trade': round(avg_profit, 2),
            'win_rate': round((winning / total_trades * 100), 2) if total_trades > 0 else 0,
            'winning_trades': winning,
            'losing_trades': losing,
            'best_trade': round(best, 2),
            'worst_trade': round(worst, 2),
            'meets_minimum': meets_minimum,
            'threshold': self.max_daily_loss_pct,
            'status': status
        }
    
    def get_weekly_profit_summary(self) -> Dict:
        """Get weekly profit summary and check minimum targets"""
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=7)
        
        query = """
        SELECT 
            SUM(net_profit) as total_profit,
            SUM(position_size) as total_invested,
            COUNT(*) as total_trades,
            COUNT(CASE WHEN net_profit > 0 THEN 1 END) as winning_trades
        FROM profit_tracking 
        WHERE trade_date > ? AND trade_date <= ? AND trade_status = 'CLOSED'
        """
        
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(query, (start_date, end_date)).fetchone()
        
        total_profit, total_invested, total_trades, winning_trades = result or (0, 0, 0, 0)
        
        # Calculate weekly return
        weekly_return_pct = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        # Check against minimum target
        meets_target = weekly_return_pct >= self.min_weekly_profit_pct
        
        return {
            'period': f"{start_date} to {end_date}",
            'total_profit': round(total_profit, 2),
            'weekly_return_pct': round(weekly_return_pct, 4),
            'total_trades': total_trades,
            'win_rate': round((winning_trades / total_trades * 100), 2) if total_trades > 0 else 0,
            'meets_target': meets_target,
            'target': self.min_weekly_profit_pct,
            'status': 'ON_TARGET' if meets_target else 'BELOW_TARGET'
        }
    
    def get_risk_metrics(self) -> Dict:
        """Calculate risk-adjusted return metrics"""
        
        # Get last 30 days of trades
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        query = """
        SELECT profit_percentage, trade_date
        FROM profit_tracking 
        WHERE trade_date > ? AND trade_date <= ? AND trade_status = 'CLOSED'
        ORDER BY trade_date
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        
        if df.empty:
            return {'error': 'No trade data available for risk calculation'}
        
        returns = df['profit_percentage'].values
        
        # Calculate metrics
        avg_return = np.mean(returns)
        return_std = np.std(returns, ddof=1) if len(returns) > 1 else 0
        sharpe_ratio = (avg_return / return_std) if return_std > 0 else 0
        
        # Calculate maximum drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = np.min(drawdowns)
        
        return {
            'avg_daily_return_pct': round(avg_return, 4),
            'volatility_pct': round(return_std, 4),
            'sharpe_ratio': round(sharpe_ratio, 4),
            'max_drawdown_pct': round(max_drawdown, 4),
            'total_trades': len(returns),
            'meets_sharpe_target': sharpe_ratio >= self.target_sharpe_ratio,
            'drawdown_acceptable': max_drawdown >= self.max_drawdown_pct
        }
    
    def get_comprehensive_profit_dashboard_data(self) -> Dict:
        """Get all profit data for dashboard display"""
        
        return {
            'daily_summary': self.get_daily_profit_summary(),
            'weekly_summary': self.get_weekly_profit_summary(),
            'risk_metrics': self.get_risk_metrics(),
            'system_thresholds': {
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'min_weekly_profit_pct': self.min_weekly_profit_pct,
                'min_monthly_profit_pct': self.min_monthly_profit_pct,
                'target_sharpe_ratio': self.target_sharpe_ratio,
                'max_drawdown_pct': self.max_drawdown_pct
            },
            'generated_at': datetime.now().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    profit_tracker = ProfitTracker()
    
    print("🧪 Testing Profit Tracking System")
    print("=" * 50)
    
    # Create table
    profit_tracker.create_profit_tracking_table()
    
    # Get dashboard data
    dashboard_data = profit_tracker.get_comprehensive_profit_dashboard_data()
    
    print(f"📊 Daily Summary: {dashboard_data['daily_summary']['status']}")
    print(f"📈 Weekly Performance: {dashboard_data['weekly_summary']['status']}")
    
    if 'error' not in dashboard_data['risk_metrics']:
        risk = dashboard_data['risk_metrics']
        print(f"📉 Risk Metrics: Sharpe {risk['sharpe_ratio']}, Drawdown {risk['max_drawdown_pct']}%")
    
    print("✅ Profit tracking system test completed")
