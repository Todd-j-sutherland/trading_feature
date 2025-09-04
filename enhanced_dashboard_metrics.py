#!/usr/bin/env python3
"""
Enhanced Dashboard Metrics
Additional metrics and queries for comprehensive_table_dashboard.py
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class EnhancedDashboardMetrics:
    """Enhanced metrics for the trading dashboard"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = db_path
    
    def get_database_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def query_to_dataframe(self, query: str) -> pd.DataFrame:
        """Execute query and return as DataFrame"""
        with self.get_database_connection() as conn:
            return pd.read_sql_query(query, conn)
    
    def get_prediction_distribution_metrics(self) -> Dict:
        """Get detailed prediction distribution for last 7 days"""
        
        query = """
        SELECT 
            predicted_action,
            COUNT(*) as count,
            ROUND(AVG(action_confidence), 4) as avg_confidence,
            ROUND(MIN(action_confidence), 4) as min_confidence,
            ROUND(MAX(action_confidence), 4) as max_confidence,
            ROUND(AVG(entry_price), 2) as avg_entry_price,
            COUNT(DISTINCT symbol) as unique_symbols
        FROM predictions 
        WHERE DATE(prediction_timestamp) >= DATE('now', '-7 days')
        GROUP BY predicted_action
        ORDER BY count DESC
        """
        
        df = self.query_to_dataframe(query)
        return {
            'distribution_data': df,
            'total_predictions': df['count'].sum() if not df.empty else 0,
            'action_types': len(df) if not df.empty else 0
        }
    
    def get_success_rate_by_action(self) -> Dict:
        """Get success rates by predicted action"""
        
        query = """
        SELECT 
            p.predicted_action,
            COUNT(*) as total_predictions,
            COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) as successful_predictions,
            ROUND(COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
            ROUND(AVG(o.actual_return), 4) as avg_return,
            ROUND(AVG(p.action_confidence), 4) as avg_confidence_for_successful
        FROM predictions p
        JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE DATE(p.prediction_timestamp) >= DATE('now', '-7 days')
        GROUP BY p.predicted_action
        ORDER BY success_rate_pct DESC
        """
        
        df = self.query_to_dataframe(query)
        return {
            'success_data': df,
            'overall_success_rate': (df['successful_predictions'].sum() / df['total_predictions'].sum() * 100) if not df.empty and df['total_predictions'].sum() > 0 else 0
        }
    
    def get_ig_markets_price_freshness(self) -> Dict:
        """Check IG Markets price data freshness"""
        
        query = """
        SELECT 
            symbol,
            prediction_timestamp,
            entry_price,
            ROUND((julianday('now') - julianday(prediction_timestamp)) * 24, 2) as hours_ago,
            CASE 
                WHEN (julianday('now') - julianday(prediction_timestamp)) * 24 < 1 THEN 'Fresh'
                WHEN (julianday('now') - julianday(prediction_timestamp)) * 24 < 4 THEN 'Recent'
                WHEN (julianday('now') - julianday(prediction_timestamp)) * 24 < 24 THEN 'Stale'
                ELSE 'Very Stale'
            END as freshness_status
        FROM predictions 
        WHERE DATE(prediction_timestamp) >= DATE('now', '-1 days')
        ORDER BY prediction_timestamp DESC
        LIMIT 20
        """
        
        df = self.query_to_dataframe(query)
        
        # Calculate freshness statistics
        freshness_stats = {}
        if not df.empty:
            freshness_stats = df['freshness_status'].value_counts().to_dict()
        
        return {
            'price_data': df,
            'freshness_stats': freshness_stats,
            'latest_price_age_hours': df['hours_ago'].iloc[0] if not df.empty else None
        }
    
    def get_daily_performance_trends(self) -> Dict:
        """Get daily performance trends for last 30 days"""
        
        query = """
        SELECT 
            DATE(p.prediction_timestamp) as trade_date,
            COUNT(*) as total_predictions,
            COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) as successful_predictions,
            ROUND(COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
            ROUND(AVG(o.actual_return), 4) as avg_return,
            ROUND(AVG(p.action_confidence), 4) as avg_confidence,
            COUNT(DISTINCT p.symbol) as symbols_traded
        FROM predictions p
        JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE DATE(p.prediction_timestamp) >= DATE('now', '-30 days')
        GROUP BY DATE(p.prediction_timestamp)
        ORDER BY trade_date DESC
        """
        
        df = self.query_to_dataframe(query)
        
        # Calculate trend statistics
        trend_stats = {}
        if not df.empty and len(df) > 1:
            recent_success = df.head(7)['success_rate_pct'].mean()
            older_success = df.tail(7)['success_rate_pct'].mean()
            trend_stats = {
                'recent_7_day_avg': round(recent_success, 2),
                'older_7_day_avg': round(older_success, 2),
                'trend_direction': 'Improving' if recent_success > older_success else 'Declining'
            }
        
        return {
            'daily_performance': df,
            'trend_analysis': trend_stats,
            'total_trading_days': len(df) if not df.empty else 0
        }
    
    def get_symbol_performance_breakdown(self) -> Dict:
        """Get performance breakdown by symbol"""
        
        query = """
        SELECT 
            p.symbol,
            COUNT(*) as total_predictions,
            COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) as successful_predictions,
            ROUND(COUNT(CASE WHEN o.actual_return > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate_pct,
            ROUND(AVG(o.actual_return), 4) as avg_return,
            ROUND(AVG(p.action_confidence), 4) as avg_confidence,
            ROUND(AVG(p.entry_price), 2) as avg_entry_price,
            MAX(p.prediction_timestamp) as latest_prediction
        FROM predictions p
        JOIN outcomes o ON p.prediction_id = o.prediction_id
        WHERE DATE(p.prediction_timestamp) >= DATE('now', '-14 days')
        GROUP BY p.symbol
        ORDER BY success_rate_pct DESC, total_predictions DESC
        """
        
        df = self.query_to_dataframe(query)
        
        return {
            'symbol_performance': df,
            'best_performing_symbol': df.iloc[0]['symbol'] if not df.empty else None,
            'total_symbols': len(df) if not df.empty else 0
        }
    
    def get_system_health_metrics(self) -> Dict:
        """Get comprehensive system health metrics"""
        
        # Recent prediction count
        recent_pred_query = """
        SELECT COUNT(*) as count 
        FROM predictions 
        WHERE prediction_timestamp >= datetime('now', '-2 hours')
        """
        
        # Recent outcome evaluation count
        recent_outcome_query = """
        SELECT COUNT(*) as count 
        FROM outcomes 
        WHERE evaluation_timestamp >= datetime('now', '-2 hours')
        """
        
        # Database size approximation
        table_count_query = """
        SELECT COUNT(*) as count 
        FROM sqlite_master 
        WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """
        
        recent_predictions = self.query_to_dataframe(recent_pred_query)['count'].iloc[0]
        recent_outcomes = self.query_to_dataframe(recent_outcome_query)['count'].iloc[0]
        table_count = self.query_to_dataframe(table_count_query)['count'].iloc[0]
        
        # System status determination
        system_status = "Healthy"
        if recent_predictions == 0:
            system_status = "No Recent Predictions"
        elif recent_outcomes == 0:
            system_status = "Evaluation Lag"
        
        return {
            'recent_predictions_2h': recent_predictions,
            'recent_outcomes_2h': recent_outcomes,
            'total_tables': table_count,
            'system_status': system_status,
            'last_check': datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    
    def get_comprehensive_dashboard_data(self) -> Dict:
        """Get all enhanced metrics for dashboard"""
        
        return {
            'prediction_distribution': self.get_prediction_distribution_metrics(),
            'success_rates': self.get_success_rate_by_action(),
            'price_freshness': self.get_ig_markets_price_freshness(),
            'daily_trends': self.get_daily_performance_trends(),
            'symbol_breakdown': self.get_symbol_performance_breakdown(),
            'system_health': self.get_system_health_metrics(),
            'generated_at': datetime.now().isoformat()
        }

# Sample usage for testing
if __name__ == "__main__":
    # Test the enhanced metrics
    metrics = EnhancedDashboardMetrics()
    
    print("🧪 Testing Enhanced Dashboard Metrics")
    print("=" * 50)
    
    # Test prediction distribution
    pred_dist = metrics.get_prediction_distribution_metrics()
    print(f"📊 Total recent predictions: {pred_dist['total_predictions']}")
    
    # Test success rates
    success_rates = metrics.get_success_rate_by_action()
    print(f"📈 Overall success rate: {success_rates['overall_success_rate']:.2f}%")
    
    # Test system health
    health = metrics.get_system_health_metrics()
    print(f"🔋 System status: {health['system_status']}")
    
    print("✅ Enhanced metrics test completed")
