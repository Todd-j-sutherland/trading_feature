#!/usr/bin/env python3
"""
Comprehensive Trading Data Export

Exports all dashboard data to a readable text file for analysis.
Replicates the comprehensive dashboard's tables in text format.
"""

import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import json

class TradingDataExporter:
    """Export comprehensive trading data to text format"""
    
    def __init__(self, db_path: str = "data/trading_predictions.db"):
        self.db_path = Path(db_path)
        self.output_file = f"trading_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
    def get_database_summary(self):
        """Get overview of all tables and their record counts"""
        
        summary = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    summary[table] = count
                    
        except Exception as e:
            summary['error'] = str(e)
            
        return summary
    
    def get_predictions_data(self):
        """Get predictions table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        prediction_id,
                        symbol,
                        datetime(prediction_timestamp) as prediction_time,
                        predicted_action,
                        predicted_direction,
                        predicted_magnitude,
                        action_confidence as confidence_score,
                        entry_price,
                        optimal_action,
                        datetime(created_at) as created_time
                    FROM predictions 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return df
                
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def get_enhanced_features_data(self):
        """Get enhanced features table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(timestamp) as feature_time,
                        current_price,
                        price_change_1d,
                        price_change_5d,
                        volume_ratio,
                        volatility_20d,
                        rsi,
                        bollinger_upper,
                        bollinger_lower,
                        macd_signal,
                        sentiment_score,
                        confidence,
                        news_count
                    FROM enhanced_features 
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return df
                
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def get_outcomes_data(self):
        """Get outcomes table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        o.outcome_id,
                        o.prediction_id,
                        p.symbol,
                        datetime(o.evaluation_timestamp) as evaluation_time,
                        o.actual_return,
                        o.actual_direction,
                        o.entry_price,
                        o.exit_price,
                        p.predicted_action,
                        p.action_confidence as confidence_score
                    FROM outcomes o
                    LEFT JOIN predictions p ON o.prediction_id = p.prediction_id
                    ORDER BY o.evaluation_timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return df
                
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def get_enhanced_outcomes_data(self):
        """Get enhanced outcomes table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(prediction_timestamp) as prediction_time,
                        entry_price,
                        exit_price_1d,
                        exit_price_3d,
                        exit_price_5d,
                        return_1d,
                        return_3d,
                        return_5d
                    FROM enhanced_outcomes 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return df
                
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def get_sentiment_features_data(self):
        """Get sentiment features table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(timestamp) as sentiment_time,
                        sentiment_score,
                        confidence,
                        news_count,
                        reddit_sentiment,
                        event_score
                    FROM enhanced_features 
                    WHERE sentiment_score IS NOT NULL
                    ORDER BY timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return df
                
        except Exception as e:
            return pd.DataFrame({'error': [str(e)]})
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        
        metrics = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Win rate from outcomes
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN actual_return > 0 THEN 1 ELSE 0 END) as wins
                    FROM outcomes 
                    WHERE actual_return IS NOT NULL
                """)
                result = cursor.fetchone()
                if result and result[0] > 0:
                    metrics['win_rate'] = (result[1] / result[0]) * 100
                    metrics['total_trades'] = result[0]
                else:
                    metrics['win_rate'] = 0
                    metrics['total_trades'] = 0
                
                # Average return
                cursor.execute("""
                    SELECT AVG(actual_return) 
                    FROM outcomes 
                    WHERE actual_return IS NOT NULL
                """)
                result = cursor.fetchone()
                metrics['avg_return'] = result[0] if result and result[0] else 0
                
                # Action distribution
                cursor.execute("""
                    SELECT predicted_action, COUNT(*) 
                    FROM predictions 
                    GROUP BY predicted_action
                """)
                actions = dict(cursor.fetchall())
                metrics['action_distribution'] = actions
                
        except Exception as e:
            metrics['error'] = str(e)
            
        return metrics
    
    def format_dataframe_as_text(self, df, title, max_width=120):
        """Format a pandas DataFrame as readable text"""
        
        if df.empty:
            return f"\n{title}\n{'=' * len(title)}\nNo data available\n"
        
        if 'error' in df.columns:
            return f"\n{title}\n{'=' * len(title)}\nError: {df['error'].iloc[0]}\n"
        
        # Format the dataframe
        text = f"\n{title}\n{'=' * len(title)}\n"
        text += f"Records: {len(df)}\n\n"
        
        # Convert to string with better formatting
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', max_width)
        pd.set_option('display.max_colwidth', 20)
        
        text += str(df.to_string(index=False))
        text += "\n"
        
        return text
    
    def export_comprehensive_data(self):
        """Export all trading data to text file"""
        
        print(f"🚀 EXPORTING COMPREHENSIVE TRADING DATA")
        print("=" * 50)
        
        # Start building the export content
        content = []
        
        # Header
        content.append("📊 COMPREHENSIVE TRADING SYSTEM DATA EXPORT")
        content.append("=" * 60)
        content.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Database: {self.db_path}")
        content.append("")
        
        # Database Summary
        print("📋 Getting database summary...")
        summary = self.get_database_summary()
        content.append("📋 DATABASE SUMMARY")
        content.append("-" * 30)
        for table, count in summary.items():
            content.append(f"{table:25} {count:>10} records")
        content.append("")
        
        # Performance Metrics
        print("📈 Calculating performance metrics...")
        metrics = self.get_performance_metrics()
        content.append("📈 PERFORMANCE METRICS")
        content.append("-" * 30)
        content.append(f"Total Trades:     {metrics.get('total_trades', 0):>10}")
        content.append(f"Win Rate:         {metrics.get('win_rate', 0):>9.1f}%")
        content.append(f"Average Return:   {metrics.get('avg_return', 0):>9.2f}%")
        content.append("")
        
        if 'action_distribution' in metrics:
            content.append("Action Distribution:")
            for action, count in metrics['action_distribution'].items():
                content.append(f"  {action:10} {count:>5} trades")
        content.append("")
        
        # Predictions Data
        print("📊 Exporting predictions data...")
        predictions_df = self.get_predictions_data()
        content.append(self.format_dataframe_as_text(
            predictions_df, 
            "📊 PREDICTIONS TABLE (Latest 50)"
        ))
        
        # Enhanced Features Data
        print("🔍 Exporting enhanced features data...")
        features_df = self.get_enhanced_features_data()
        content.append(self.format_dataframe_as_text(
            features_df, 
            "🔍 ENHANCED FEATURES TABLE (Latest 50)"
        ))
        
        # Outcomes Data
        print("💰 Exporting outcomes data...")
        outcomes_df = self.get_outcomes_data()
        content.append(self.format_dataframe_as_text(
            outcomes_df, 
            "💰 OUTCOMES TABLE (Latest 50)"
        ))
        
        # Enhanced Outcomes Data
        print("🎯 Exporting enhanced outcomes data...")
        enhanced_outcomes_df = self.get_enhanced_outcomes_data()
        content.append(self.format_dataframe_as_text(
            enhanced_outcomes_df, 
            "🎯 ENHANCED OUTCOMES TABLE (Latest 50)"
        ))
        
        # Sentiment Features Data
        print("📰 Exporting sentiment features data...")
        sentiment_df = self.get_sentiment_features_data()
        content.append(self.format_dataframe_as_text(
            sentiment_df, 
            "📰 SENTIMENT FEATURES TABLE (Latest 50)"
        ))
        
        # Recent Activity Summary
        content.append("📅 RECENT ACTIVITY SUMMARY")
        content.append("-" * 40)
        
        # Last 24 hours activity
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Recent predictions
                cursor.execute("""
                    SELECT COUNT(*) FROM predictions 
                    WHERE datetime(prediction_timestamp) > datetime('now', '-24 hours')
                """)
                recent_predictions = cursor.fetchone()[0]
                
                # Recent features
                cursor.execute("""
                    SELECT COUNT(*) FROM enhanced_features 
                    WHERE datetime(timestamp) > datetime('now', '-24 hours')
                """)
                recent_features = cursor.fetchone()[0]
                
                # Recent outcomes
                cursor.execute("""
                    SELECT COUNT(*) FROM outcomes 
                    WHERE datetime(evaluation_timestamp) > datetime('now', '-24 hours')
                """)
                recent_outcomes = cursor.fetchone()[0]
                
                content.append(f"Last 24 Hours Activity:")
                content.append(f"  Predictions:      {recent_predictions:>5}")
                content.append(f"  Features:         {recent_features:>5}")
                content.append(f"  Outcomes:         {recent_outcomes:>5}")
                
        except Exception as e:
            content.append(f"Error getting recent activity: {e}")
        
        content.append("")
        
        # Footer
        content.append("=" * 60)
        content.append("📊 END OF TRADING SYSTEM DATA EXPORT")
        content.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append("=" * 60)
        
        # Write to file
        full_content = "\n".join(content)
        
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        print(f"✅ Export completed: {self.output_file}")
        print(f"📄 File size: {len(full_content):,} characters")
        print(f"📊 Total sections: {len([c for c in content if c.startswith('📊') or c.startswith('🔍')])}")
        
        return self.output_file

def main():
    """Main function to export comprehensive trading data"""
    
    # Local export
    local_exporter = TradingDataExporter("data/trading_predictions.db")
    local_file = local_exporter.export_comprehensive_data()
    
    print(f"\n📋 LOCAL DATA EXPORT COMPLETED")
    print(f"   File: {local_file}")
    
    # Also create a remote export command
    print(f"\n🌐 TO EXPORT REMOTE DATA:")
    print(f"   scp trading_data_exporter.py root@170.64.199.151:/root/test/")
    print(f"   ssh root@170.64.199.151 'cd /root/test && python3 trading_data_exporter.py'")
    print(f"   scp root@170.64.199.151:/root/test/trading_data_export_*.txt .")

if __name__ == "__main__":
    main()
