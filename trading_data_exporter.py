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
        
        content = ["📋 DATABASE SUMMARY"]
        content.append("-" * 30)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    content.append(f"{table:<30} {count:>8} records")
                    
        except Exception as e:
            content.append(f"Error: {str(e)}")
            
        return content
    
    def get_predictions_data(self):
        """Get predictions table data"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(prediction_timestamp) as prediction_time,
                        predicted_action,
                        action_confidence as confidence,
                        entry_price,
                        predicted_direction,
                        predicted_magnitude,
                        model_version
                    FROM predictions 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return self.format_dataframe_as_text(df, "📊 PREDICTIONS TABLE (Latest 50)")
                
        except Exception as e:
            return f"📊 PREDICTIONS TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
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
                
                return self.format_dataframe_as_text(df, "🔍 ENHANCED FEATURES TABLE (Latest 50)")
                
        except Exception as e:
            return f"🔍 ENHANCED FEATURES TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
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
                
                return self.format_dataframe_as_text(df, "💰 OUTCOMES TABLE (Latest 50)")
                
        except Exception as e:
            return f"💰 OUTCOMES TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_enhanced_outcomes_data(self):
        """Get enhanced outcomes table data with schema-safe query"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check what columns exist in enhanced_outcomes
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(enhanced_outcomes)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Build query with available columns
                base_query = """
                    SELECT 
                        symbol,
                        datetime(prediction_timestamp) as prediction_time,
                        entry_price"""
                
                optional_columns = []
                if 'exit_price_1d' in columns:
                    optional_columns.append('exit_price_1d')
                if 'return_1d' in columns:
                    optional_columns.append('return_1d')
                if 'actual_return_1d' in columns:
                    optional_columns.append('actual_return_1d')
                if 'exit_price_5d' in columns:
                    optional_columns.append('exit_price_5d')
                if 'return_5d' in columns:
                    optional_columns.append('return_5d')
                if 'actual_return_5d' in columns:
                    optional_columns.append('actual_return_5d')
                
                if optional_columns:
                    query = base_query + ",\n                        " + ",\n                        ".join(optional_columns)
                else:
                    query = base_query
                    
                query += """
                    FROM enhanced_outcomes 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 50
                """
                
                df = pd.read_sql_query(query, conn)
                return self.format_dataframe_as_text(df, "🎯 ENHANCED OUTCOMES TABLE (Latest 50)")
                
        except Exception as e:
            return f"🎯 ENHANCED OUTCOMES TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
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
                
                return self.format_dataframe_as_text(df, "📰 SENTIMENT FEATURES TABLE (Latest 50)")
                
        except Exception as e:
            return f"📰 SENTIMENT FEATURES TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_performance_metrics(self):
        """Calculate performance metrics"""
        
        content = ["📈 PERFORMANCE METRICS"]
        content.append("-" * 30)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Win rate calculation
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_trades,
                        SUM(CASE WHEN actual_return > 0 THEN 1 ELSE 0 END) as winning_trades
                    FROM outcomes 
                    WHERE actual_return IS NOT NULL
                """)
                result = cursor.fetchone()
                
                if result and result[0] > 0:
                    win_rate = (result[1] / result[0]) * 100
                    total_trades = result[0]
                else:
                    win_rate = 0
                    total_trades = 0
                
                # Average return
                cursor.execute("""
                    SELECT AVG(actual_return) 
                    FROM outcomes 
                    WHERE actual_return IS NOT NULL
                """)
                result = cursor.fetchone()
                avg_return = result[0] if result and result[0] else 0
                
                # Action distribution
                cursor.execute("""
                    SELECT predicted_action, COUNT(*) 
                    FROM predictions 
                    GROUP BY predicted_action
                """)
                actions = dict(cursor.fetchall())
                
                content.append(f"Total Trades:              {total_trades}")
                content.append(f"Win Rate:               {win_rate:.1f}%")
                content.append(f"Average Return:        {avg_return:.2f}%")
                content.append("")
                content.append("Action Distribution:")
                for action, count in actions.items():
                    content.append(f"  {action}: {count}")
                
        except Exception as e:
            content.append(f"Error: {str(e)}")
            
        return content
    
    def get_technical_analysis_data(self):
        """Get technical analysis data from enhanced_morning_analysis"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(analysis_timestamp) as analysis_time,
                        sma_20,
                        sma_50,
                        rsi,
                        macd,
                        bollinger_upper,
                        bollinger_lower,
                        support_level,
                        resistance_level,
                        trend_direction,
                        strength_score
                    FROM enhanced_morning_analysis 
                    ORDER BY analysis_timestamp DESC 
                    LIMIT 50
                """, conn)
                
                return self.format_dataframe_as_text(df, "🔧 TECHNICAL ANALYSIS DATA (Latest 50)")
                
        except Exception as e:
            return f"🔧 TECHNICAL ANALYSIS DATA (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_model_performance_data(self):
        """Get model performance metrics"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        model_name,
                        datetime(evaluation_date) as eval_date,
                        accuracy,
                        precision_score,
                        recall,
                        f1_score,
                        auc_score,
                        training_samples,
                        test_samples
                    FROM model_performance_enhanced 
                    ORDER BY evaluation_date DESC 
                    LIMIT 20
                """, conn)
                
                return self.format_dataframe_as_text(df, "📈 MODEL PERFORMANCE METRICS (Latest 20)")
                
        except Exception as e:
            return f"📈 MODEL PERFORMANCE METRICS (Latest 20)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_model_training_data(self):
        """Get model training information"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        model_name,
                        datetime(training_date) as train_date,
                        training_duration,
                        feature_count,
                        sample_count,
                        validation_score,
                        hyperparameters
                    FROM model_training_log 
                    ORDER BY training_date DESC 
                    LIMIT 20
                """, conn)
                
                return self.format_dataframe_as_text(df, "🧠 MODEL TRAINING LOG (Latest 20)")
                
        except Exception as e:
            return f"🧠 MODEL TRAINING LOG (Latest 20)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_activity_summary(self):
        """Get recent activity summary"""
        
        content = ["📅 RECENT ACTIVITY SUMMARY"]
        content.append("-" * 40)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Last 24 hours activity
                cursor.execute("""
                    SELECT 
                        COUNT(*) as predictions,
                        COUNT(DISTINCT symbol) as symbols
                    FROM predictions 
                    WHERE prediction_timestamp > datetime('now', '-1 day')
                """)
                pred_stats = cursor.fetchone()
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM enhanced_features 
                    WHERE feature_time > datetime('now', '-1 day')
                """)
                feature_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM outcomes 
                    WHERE outcome_timestamp > datetime('now', '-1 day')
                """)
                outcome_count = cursor.fetchone()[0]
                
                content.append("Last 24 Hours Activity:")
                content.append(f"  Predictions:          {pred_stats[0] if pred_stats else 0}")
                content.append(f"  Features:            {feature_count}")
                content.append(f"  Outcomes:             {outcome_count}")
                
        except Exception as e:
            content.append(f"Error: {str(e)}")
            
        return content

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
        """Export all trading data to a comprehensive text file"""
        content = []
        
        # Header
        content.append("📊 COMPREHENSIVE TRADING SYSTEM DATA EXPORT")
        content.append("=" * 60)
        content.append(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"Database: {self.db_path}")
        content.append("")
        
        # Database summary
        content.extend(self.get_database_summary())
        content.append("")
        
        # Performance metrics
        content.extend(self.get_performance_metrics())
        content.append("")
        
        # MORNING ANALYSIS SECTIONS
        content.append("🌅 MORNING ANALYSIS SECTIONS")
        content.append("=" * 60)
        content.append("")
        
        predictions_text = self.get_predictions_data()
        content.extend(predictions_text.split('\n'))
        content.append("")
        
        features_text = self.get_enhanced_features_data()
        content.extend(features_text.split('\n'))
        content.append("")
        
        sentiment_text = self.get_sentiment_features_data()
        content.extend(sentiment_text.split('\n'))
        content.append("")
        
        technical_text = self.get_technical_analysis_data()
        content.extend(technical_text.split('\n'))
        content.append("")
        
        # EVENING ANALYSIS SECTIONS
        content.append("🌆 EVENING ANALYSIS SECTIONS")
        content.append("=" * 60)
        content.append("")
        
        outcomes_text = self.get_outcomes_data()
        content.extend(outcomes_text.split('\n'))
        content.append("")
        
        enhanced_outcomes_text = self.get_enhanced_outcomes_data()
        content.extend(enhanced_outcomes_text.split('\n'))
        content.append("")
        
        model_perf_text = self.get_model_performance_data()
        content.extend(model_perf_text.split('\n'))
        content.append("")
        
        model_train_text = self.get_model_training_data()
        content.extend(model_train_text.split('\n'))
        content.append("")
        
        # Activity summary
        content.extend(self.get_activity_summary())
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
        
        # Also create a standard filename for easy copying
        standard_filename = "latest_trading_data_export.txt"
        with open(standard_filename, 'w', encoding='utf-8') as f:
            f.write(full_content)
        print(f"📋 Also saved as: {standard_filename}")
        
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
