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
        
    def get_table_schema(self, table_name):
        """Get table schema information for future-proof queries"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
                if not cursor.fetchone():
                    return None
                
                # Get column info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [row[1] for row in cursor.fetchall()]
                return columns
        except Exception:
            return None
    
    def build_safe_query(self, table_name, required_columns, optional_columns, order_by_candidates):
        """Build a schema-safe SQL query"""
        schema = self.get_table_schema(table_name)
        if not schema:
            return None
            
        # Start with required columns that exist
        select_columns = []
        for col in required_columns:
            if col['name'] in schema:
                select_columns.append(col.get('alias', col['name']))
        
        # Add optional columns that exist
        for col in optional_columns:
            if col in schema:
                select_columns.append(col)
        
        if not select_columns:
            return None
            
        # Find a suitable ORDER BY column
        order_by = None
        for candidate in order_by_candidates:
            if candidate in schema:
                order_by = candidate
                break
        
        query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
        if order_by:
            query += f" ORDER BY {order_by} DESC"
        query += " LIMIT 50"
        
        return query
        
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
        """Get predictions table data with schema-safe query"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check what columns exist
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(predictions)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Build query with available columns
                base_columns = ['symbol']
                
                # Add timestamp column
                if 'prediction_timestamp' in columns:
                    base_columns.append('datetime(prediction_timestamp) as prediction_time')
                elif 'timestamp' in columns:
                    base_columns.append('datetime(timestamp) as prediction_time')
                
                # Add other important columns if they exist
                optional_columns = {
                    'predicted_action': 'predicted_action',
                    'action_confidence': 'action_confidence as confidence',
                    'confidence': 'confidence',
                    'entry_price': 'entry_price',
                    'predicted_direction': 'predicted_direction',
                    'predicted_magnitude': 'predicted_magnitude',
                    'model_version': 'model_version'
                }
                
                for col, alias in optional_columns.items():
                    if col in columns:
                        base_columns.append(alias)
                
                query = f"""
                    SELECT {', '.join(base_columns)}
                    FROM predictions 
                    ORDER BY {('prediction_timestamp' if 'prediction_timestamp' in columns else 'timestamp')} DESC 
                    LIMIT 50
                """
                
                df = pd.read_sql_query(query, conn)
                return self.format_dataframe_as_text(df, "📊 PREDICTIONS TABLE (Latest 50)")
                
        except Exception as e:
            return f"📊 PREDICTIONS TABLE (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_enhanced_features_data(self):
        """Get enhanced features table data with schema-safe query"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check what columns exist
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(enhanced_features)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Build query with available columns
                base_columns = ['symbol']
                
                # Add timestamp column (check for variations)
                if 'timestamp' in columns:
                    base_columns.append('datetime(timestamp) as feature_time')
                elif 'feature_time' in columns:
                    base_columns.append('datetime(feature_time) as feature_time')
                elif 'created_at' in columns:
                    base_columns.append('datetime(created_at) as feature_time')
                
                # Add other important columns if they exist
                optional_columns = [
                    'current_price', 'price_change_1d', 'price_change_5d',
                    'volume_ratio', 'volatility_20d', 'rsi', 'bollinger_upper',
                    'bollinger_lower', 'macd_signal', 'sentiment_score',
                    'confidence', 'news_count'
                ]
                
                for col in optional_columns:
                    if col in columns:
                        base_columns.append(col)
                
                query = f"""
                    SELECT {', '.join(base_columns)}
                    FROM enhanced_features 
                    ORDER BY {('timestamp' if 'timestamp' in columns else 'feature_time' if 'feature_time' in columns else 'created_at')} DESC 
                    LIMIT 50
                """
                
                df = pd.read_sql_query(query, conn)
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
                df = pd.read_sql_query("""
                    SELECT 
                        symbol,
                        datetime(prediction_timestamp) as prediction_time,
                        entry_price,
                        exit_price_1h,
                        exit_price_4h,
                        exit_price_1d,
                        return_pct,
                        optimal_action,
                        confidence_score,
                        price_direction_1h,
                        price_direction_4h,
                        price_direction_1d
                    FROM enhanced_outcomes 
                    ORDER BY prediction_timestamp DESC 
                    LIMIT 50
                """, conn)
                
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
        """Get technical analysis data with schema-safe query"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Check if table exists and what columns it has
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='enhanced_morning_analysis'")
                if not cursor.fetchone():
                    return f"🔧 TECHNICAL ANALYSIS DATA (Latest 50)\n{'=' * 40}\nTable 'enhanced_morning_analysis' does not exist\n"
                
                cursor.execute("PRAGMA table_info(enhanced_morning_analysis)")
                columns = [row[1] for row in cursor.fetchall()]
                
                # Build query with available columns
                base_columns = []
                
                # Add timestamp column
                if 'timestamp' in columns:
                    base_columns.append('datetime(timestamp) as analysis_time')
                elif 'analysis_timestamp' in columns:
                    base_columns.append('datetime(analysis_timestamp) as analysis_time')
                elif 'created_at' in columns:
                    base_columns.append('datetime(created_at) as analysis_time')
                
                # Add other columns if they exist
                optional_columns = [
                    'analysis_type', 'market_hours', 'banks_analyzed',
                    'overall_sentiment', 'ml_predictions', 'technical_signals',
                    'recommendations', 'data_quality_scores', 'symbol',
                    'sma_20', 'sma_50', 'rsi', 'macd'
                ]
                
                for col in optional_columns:
                    if col in columns:
                        base_columns.append(col)
                
                if not base_columns:
                    return f"🔧 TECHNICAL ANALYSIS DATA (Latest 50)\n{'=' * 40}\nNo recognizable columns found\n"
                
                timestamp_col = 'timestamp' if 'timestamp' in columns else 'analysis_timestamp' if 'analysis_timestamp' in columns else 'created_at'
                
                query = f"""
                    SELECT {', '.join(base_columns)}
                    FROM enhanced_morning_analysis 
                    ORDER BY {timestamp_col} DESC 
                    LIMIT 50
                """
                
                df = pd.read_sql_query(query, conn)
                return self.format_dataframe_as_text(df, "🔧 TECHNICAL ANALYSIS DATA (Latest 50)")
                
        except Exception as e:
            return f"🔧 TECHNICAL ANALYSIS DATA (Latest 50)\n{'=' * 40}\nError: {str(e)}\n"
    
    def get_model_performance_data(self):
        """Get model performance metrics"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("""
                    SELECT 
                        model_version,
                        model_type,
                        datetime(training_date) as train_date,
                        direction_accuracy_1h,
                        direction_accuracy_4h,
                        direction_accuracy_1d,
                        precision_score,
                        recall_score,
                        f1_score,
                        training_samples
                    FROM model_performance_enhanced 
                    ORDER BY training_date DESC 
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
                    WHERE timestamp > datetime('now', '-1 day')
                """)
                feature_count = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM outcomes 
                    WHERE evaluation_timestamp > datetime('now', '-1 day')
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
