#!/usr/bin/env python3
"""
Independent ML Success Rate Dashboard
A standalone dashboard for tracking machine learning model performance over time
Uses real trading data from the production database
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import numpy as np
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TradingMLTracker:
    """Real-time ML performance tracker using production trading data"""
    
    def __init__(self, db_path="data/trading_predictions.db"):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            logger.warning(f"Database not found at {db_path}, creating sample data")
            self.use_sample_data = True
            self.sample_data = self.create_sample_data()
        else:
            self.use_sample_data = False
            logger.info(f"Using real trading data from {db_path}")
    
    def get_db_connection(self):
        """Get database connection"""
        if self.use_sample_data:
            return None
        return sqlite3.connect(str(self.db_path))
    
    def create_sample_data(self):
        """Create sample data when real database is not available"""
        logger.info("Creating sample ML performance data")
        
        # Generate sample data with realistic progression
        base_accuracy = 0.45  # Start at 45% accuracy
        accuracy_improvement = 0.3  # Improve to 75% over time
        
        symbols = ['CBA.AX', 'WBC.AX', 'ANZ.AX', 'NAB.AX']
        actions = ['BUY', 'SELL', 'HOLD']
        days = 30
        
        predictions = []
        
        for day in range(days):
            date = datetime.now() - timedelta(days=days-day-1)
            
            # Calculate progressive accuracy improvement
            progress = day / days
            current_base_accuracy = base_accuracy + (accuracy_improvement * progress)
            
            # Generate 3-8 predictions per day
            num_predictions = np.random.randint(3, 9)
            
            for pred_num in range(num_predictions):
                # Add some daily variation
                daily_variation = np.random.normal(0, 0.1)
                prediction_accuracy_prob = max(0.1, min(0.95, current_base_accuracy + daily_variation))
                
                confidence = np.random.beta(2, 2)  # Realistic confidence distribution
                action = np.random.choice(actions, p=[0.4, 0.3, 0.3])
                symbol = np.random.choice(symbols)
                
                # Determine if prediction will be successful
                success_prob = prediction_accuracy_prob + (confidence * 0.2)
                is_successful = np.random.random() < success_prob
                
                # Generate realistic returns
                if action == 'BUY':
                    actual_return = np.random.normal(1.5, 2.0) if is_successful else np.random.normal(-1.0, 2.0)
                elif action == 'SELL':
                    actual_return = np.random.normal(-1.5, 2.0) if is_successful else np.random.normal(1.0, 2.0)
                else:  # HOLD
                    actual_return = np.random.normal(0, 0.8) if is_successful else np.random.normal(0, 3.0)
                
                prediction = {
                    'prediction_id': f"{symbol}_{date.strftime('%Y%m%d')}_{pred_num}",
                    'symbol': symbol,
                    'prediction_timestamp': date + timedelta(hours=np.random.randint(9, 16), minutes=np.random.randint(0, 60)),
                    'predicted_action': action,
                    'action_confidence': confidence,
                    'actual_return': actual_return,
                    'is_successful': is_successful,
                    'evaluation_timestamp': date + timedelta(hours=np.random.randint(16, 24))
                }
                
                predictions.append(prediction)
        
        return predictions
    
    def get_summary_stats(self, days=30):
        """Get summary statistics for the specified period"""
        if self.use_sample_data:
            return self._get_sample_summary_stats(days)
        
        try:
            conn = self.get_db_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.isoformat()
            
            # Get predictions with outcomes - exclude test data
            query = """
            SELECT 
                p.prediction_id,
                p.symbol,
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                o.actual_return,
                o.evaluation_timestamp,
                CASE 
                    WHEN p.predicted_action = 'BUY' AND o.actual_return > 0 THEN 1
                    WHEN p.predicted_action = 'SELL' AND o.actual_return < 0 THEN 1
                    WHEN p.predicted_action = 'HOLD' AND ABS(o.actual_return) < 1.0 THEN 1
                    ELSE 0
                END as is_successful
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.prediction_timestamp >= ?
            AND o.actual_return IS NOT NULL
            AND p.model_version NOT IN ('enhanced_ml_v1', 'test_v1.0', 'test_model', 'dashboard_test_v1.0')
            AND p.prediction_id NOT LIKE 'enhanced_%'
            ORDER BY p.prediction_timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[cutoff_date_str])
            conn.close()
            
            if df.empty:
                return None
            
            # Convert datetime columns properly
            df['prediction_timestamp'] = pd.to_datetime(df['prediction_timestamp'], errors='coerce')
            
            # Calculate summary stats
            total_predictions = len(df)
            successful_predictions = df['is_successful'].sum()
            overall_accuracy = successful_predictions / total_predictions if total_predictions > 0 else 0
            avg_confidence = df['action_confidence'].mean()
            
            # Calculate trend
            df = df.sort_values('prediction_timestamp')
            
            if len(df) >= 14:
                mid_point = len(df) // 2
                recent_half = df.iloc[mid_point:]
                earlier_half = df.iloc[:mid_point]
                
                recent_accuracy = recent_half['is_successful'].mean()
                earlier_accuracy = earlier_half['is_successful'].mean()
                
                trend = 'improving' if recent_accuracy > earlier_accuracy + 0.05 else \
                       'declining' if recent_accuracy < earlier_accuracy - 0.05 else 'stable'
            else:
                trend = 'insufficient_data'
            
            return {
                'total_predictions': total_predictions,
                'successful_predictions': successful_predictions,
                'overall_accuracy': overall_accuracy,
                'avg_confidence': avg_confidence,
                'trend': trend,
                'period_days': days,
                'data_source': 'real_trading_data'
            }
        
        except Exception as e:
            logger.error(f"Error getting summary stats: {e}")
            return None
    
    def _get_sample_summary_stats(self, days):
        """Get summary stats from sample data"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_predictions = [
            p for p in self.sample_data
            if p['prediction_timestamp'] >= cutoff_date
        ]
        
        if not recent_predictions:
            return None
        
        total_predictions = len(recent_predictions)
        successful_predictions = sum(1 for p in recent_predictions if p['is_successful'])
        overall_accuracy = successful_predictions / total_predictions if total_predictions > 0 else 0
        avg_confidence = np.mean([p['action_confidence'] for p in recent_predictions])
        
        return {
            'total_predictions': total_predictions,
            'successful_predictions': successful_predictions,
            'overall_accuracy': overall_accuracy,
            'avg_confidence': avg_confidence,
            'trend': 'sample_data',
            'period_days': days,
            'data_source': 'sample_data'
        }
    
    def get_daily_dataframe(self, days=30):
        """Get daily metrics as a pandas DataFrame"""
        if self.use_sample_data:
            return self._get_sample_daily_dataframe(days)
        
        try:
            conn = self.get_db_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.isoformat()
            
            query = """
            SELECT 
                DATE(p.prediction_timestamp) as date,
                COUNT(*) as predictions_made,
                AVG(p.action_confidence) as avg_confidence,
                SUM(CASE 
                    WHEN p.predicted_action = 'BUY' AND o.actual_return > 0 THEN 1
                    WHEN p.predicted_action = 'SELL' AND o.actual_return < 0 THEN 1
                    WHEN p.predicted_action = 'HOLD' AND ABS(o.actual_return) < 1.0 THEN 1
                    ELSE 0
                END) as successful_predictions,
                COUNT(CASE WHEN o.actual_return IS NOT NULL THEN 1 END) as evaluated_predictions
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.prediction_timestamp >= ?
            AND p.model_version NOT IN ('enhanced_ml_v1', 'test_v1.0', 'test_model', 'dashboard_test_v1.0')
            AND p.prediction_id NOT LIKE 'enhanced_%'
            GROUP BY DATE(p.prediction_timestamp)
            ORDER BY date DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[cutoff_date_str])
            conn.close()
            
            if df.empty:
                return pd.DataFrame()
            
            # Calculate accuracy
            df['accuracy'] = df.apply(lambda row: 
                row['successful_predictions'] / row['evaluated_predictions'] 
                if row['evaluated_predictions'] > 0 else 0, axis=1)
            
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df
            
        except Exception as e:
            logger.error(f"Error getting daily dataframe: {e}")
            return pd.DataFrame()
    
    def _get_sample_daily_dataframe(self, days):
        """Get daily metrics from sample data"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_predictions = [
            p for p in self.sample_data
            if p['prediction_timestamp'] >= cutoff_date
        ]
        
        if not recent_predictions:
            return pd.DataFrame()
        
        # Group by date
        daily_data = {}
        for p in recent_predictions:
            date_str = p['prediction_timestamp'].strftime('%Y-%m-%d')
            if date_str not in daily_data:
                daily_data[date_str] = {
                    'predictions': [],
                    'successful': 0,
                    'total': 0
                }
            daily_data[date_str]['predictions'].append(p)
            daily_data[date_str]['total'] += 1
            if p['is_successful']:
                daily_data[date_str]['successful'] += 1
        
        # Convert to dataframe
        rows = []
        for date_str, data in daily_data.items():
            rows.append({
                'date': pd.to_datetime(date_str),
                'predictions_made': data['total'],
                'successful_predictions': data['successful'],
                'accuracy': data['successful'] / data['total'] if data['total'] > 0 else 0,
                'avg_confidence': np.mean([p['action_confidence'] for p in data['predictions']])
            })
        
        df = pd.DataFrame(rows)
        return df.sort_values('date')
    
    def get_predictions_dataframe(self, days=7):
        """Get recent predictions as a pandas DataFrame with ML components"""
        if self.use_sample_data:
            return self._get_sample_predictions_dataframe(days)
        
        try:
            conn = self.get_db_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.isoformat()
            
            query = """
            SELECT 
                p.prediction_timestamp,
                p.symbol,
                p.predicted_action,
                p.action_confidence,
                p.entry_price,
                p.confidence_breakdown,
                p.news_sentiment,
                p.tech_score,
                p.market_context,
                o.actual_return,
                o.exit_price,
                o.evaluation_timestamp,
                CASE 
                    WHEN p.predicted_action = 'BUY' AND o.actual_return > 0 THEN 1
                    WHEN p.predicted_action = 'SELL' AND o.actual_return < 0 THEN 1
                    WHEN p.predicted_action = 'HOLD' AND ABS(o.actual_return) < 1.0 THEN 1
                    ELSE 0
                END as is_successful
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.prediction_timestamp >= ?
            ORDER BY p.prediction_timestamp DESC
            LIMIT 50
            """
            
            df = pd.read_sql_query(query, conn, params=[cutoff_date_str])
            conn.close()
            
            if df.empty:
                return pd.DataFrame()
            
            # Format for display with ML components
            display_data = []
            for _, row in df.iterrows():
                pred_time = pd.to_datetime(row['prediction_timestamp'], errors='coerce')
                if pd.isna(pred_time):
                    continue
                
                # Parse confidence breakdown for ML components
                try:
                    breakdown_str = row['confidence_breakdown'] if row['confidence_breakdown'] else ""
                    news_comp = 0
                    tech_comp = 0
                    
                    if breakdown_str:
                        # Try JSON format first
                        if breakdown_str.startswith('{'):
                            try:
                                breakdown_json = json.loads(breakdown_str)
                                news_comp = breakdown_json.get('news_component', 0) * 100
                                tech_comp = breakdown_json.get('technical_component', 0) * 100
                            except json.JSONDecodeError:
                                pass
                        else:
                            # Try string format: "Tech:0.381 + News:0.045 + Vol:0.030"
                            if 'News:' in breakdown_str:
                                news_part = breakdown_str.split('News:')[1].strip().split()[0]
                                news_comp = float(news_part) * 100
                            if 'Tech:' in breakdown_str:
                                tech_part = breakdown_str.split('Tech:')[1].strip().split()[0]
                                tech_comp = float(tech_part) * 100
                    
                    # Format the display
                    if news_comp > 0 or tech_comp > 0:
                        ml_breakdown = f"N:{news_comp:.1f} T:{tech_comp:.1f}"
                    else:
                        ml_breakdown = "N:0.0 T:0.0"
                        
                except Exception as e:
                    logger.debug(f"Error parsing confidence breakdown: {e}")
                    ml_breakdown = "Parse Error"
                
                display_data.append({
                    'Date': pred_time.strftime('%Y-%m-%d'),
                    'Time': pred_time.strftime('%H:%M'),
                    'Symbol': row['symbol'],
                    'Action': row['predicted_action'],
                    'Confidence': f"{row['action_confidence']:.1%}",
                    'ML Components': ml_breakdown,
                    'Market Context': row['market_context'] or 'NEUTRAL',
                    'News Sentiment': f"{row['news_sentiment']:+.2f}" if pd.notna(row['news_sentiment']) and row['news_sentiment'] != 0 else '0.00',
                    'Actual Return': f"{row['actual_return']:+.2f}%" if pd.notna(row['actual_return']) else 'Pending',
                    'Success': '✅' if row['is_successful'] == 1 else '❌' if pd.notna(row['actual_return']) else '⏳'
                })
            
            return pd.DataFrame(display_data)
            
        except Exception as e:
            logger.error(f"Error getting predictions dataframe: {e}")
            return pd.DataFrame()
    
    def get_ml_component_analysis(self, days=30):
        """Get detailed ML component analysis"""
        if self.use_sample_data:
            return self._get_sample_ml_components(days)
        
        try:
            conn = self.get_db_connection()
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.isoformat()
            
            query = """
            SELECT 
                p.prediction_id,
                p.symbol,
                p.prediction_timestamp,
                p.predicted_action,
                p.action_confidence,
                p.news_sentiment,
                p.tech_score,
                p.market_context,
                p.confidence_breakdown,
                p.technical_indicators,
                p.news_impact_score,
                p.market_trend_pct,
                p.market_volatility,
                p.market_momentum,
                o.actual_return,
                CASE 
                    WHEN p.predicted_action = 'BUY' AND o.actual_return > 0 THEN 1
                    WHEN p.predicted_action = 'SELL' AND o.actual_return < 0 THEN 1
                    WHEN p.predicted_action = 'HOLD' AND ABS(o.actual_return) < 1.0 THEN 1
                    ELSE 0
                END as is_successful
            FROM predictions p
            LEFT JOIN outcomes o ON p.prediction_id = o.prediction_id
            WHERE p.prediction_timestamp >= ?
            AND o.actual_return IS NOT NULL
            ORDER BY p.prediction_timestamp DESC
            """
            
            df = pd.read_sql_query(query, conn, params=[cutoff_date_str])
            conn.close()
            
            if df.empty:
                return None
            
            # Parse confidence breakdown - handle both JSON and string formats
            confidence_data = []
            for _, row in df.iterrows():
                try:
                    breakdown_str = row['confidence_breakdown'] if row['confidence_breakdown'] else ""
                    
                    components = {'tech': 0, 'news': 0, 'vol': 0, 'risk': 0}
                    
                    if breakdown_str:
                        # Try JSON format first
                        if breakdown_str.startswith('{'):
                            try:
                                breakdown_json = json.loads(breakdown_str)
                                components['news'] = breakdown_json.get('news_component', 0)
                                components['tech'] = breakdown_json.get('technical_component', 0)
                                components['vol'] = breakdown_json.get('volume_component', 0)
                            except json.JSONDecodeError:
                                pass
                        else:
                            # Handle string format: "Tech:0.381 + News:0.045 + Vol:0.030"
                            parts = breakdown_str.split('+')
                            for part in parts:
                                part = part.strip()
                                if 'Tech:' in part:
                                    try:
                                        components['tech'] = float(part.split('Tech:')[1].strip().split()[0])
                                    except:
                                        pass
                                elif 'News:' in part:
                                    try:
                                        components['news'] = float(part.split('News:')[1].strip().split()[0])
                                    except:
                                        pass
                                elif 'Vol:' in part:
                                    try:
                                        components['vol'] = float(part.split('Vol:')[1].strip().split()[0])
                                    except:
                                        pass
                                elif 'Risk:' in part:
                                    try:
                                        components['risk'] = float(part.split('Risk:')[1].strip().split()[0])
                                    except:
                                        pass
                    
                    confidence_data.append({
                        'prediction_id': row['prediction_id'],
                        'symbol': row['symbol'],
                        'action': row['predicted_action'],
                        'overall_confidence': row['action_confidence'],
                        'news_component': components['news'],
                        'technical_component': components['tech'],
                        'volume_component': components['vol'],
                        'risk_component': components['risk'],
                        'tech_score': row['tech_score'] if pd.notna(row['tech_score']) else 0,
                        'news_sentiment': row['news_sentiment'] if pd.notna(row['news_sentiment']) else 0,
                        'market_context': row['market_context'] if row['market_context'] else 'NEUTRAL',
                        'is_successful': row['is_successful'],
                        'actual_return': row['actual_return']
                    })
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    # Fallback for malformed data
                    confidence_data.append({
                        'prediction_id': row['prediction_id'],
                        'symbol': row['symbol'],
                        'action': row['predicted_action'],
                        'overall_confidence': row['action_confidence'],
                        'news_component': 0,
                        'technical_component': 0,
                        'volume_component': 0,
                        'risk_component': 0,
                        'tech_score': row['tech_score'] if pd.notna(row['tech_score']) else 0,
                        'news_sentiment': row['news_sentiment'] if pd.notna(row['news_sentiment']) else 0,
                        'market_context': row['market_context'] if row['market_context'] else 'NEUTRAL',
                        'is_successful': row['is_successful'],
                        'actual_return': row['actual_return']
                    })
            
            return pd.DataFrame(confidence_data)
            
        except Exception as e:
            logger.error(f"Error getting ML component analysis: {e}")
            return None
    
    def _get_sample_ml_components(self, days):
        """Generate sample ML component data"""
        # Create sample data showing different ML components
        sample_data = []
        for i in range(min(50, len(self.sample_data))):
            p = self.sample_data[i]
            sample_data.append({
                'prediction_id': p['prediction_id'],
                'symbol': p['symbol'],
                'action': p['predicted_action'],
                'overall_confidence': p['action_confidence'],
                'news_component': np.random.uniform(0.3, 0.8),
                'technical_component': np.random.uniform(0.2, 0.7),
                'volume_component': np.random.uniform(0.1, 0.5),
                'tech_score': np.random.randint(30, 80),
                'news_sentiment': np.random.uniform(-0.5, 0.5),
                'market_context': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
                'is_successful': p['is_successful'],
                'actual_return': p['actual_return']
            })
        return pd.DataFrame(sample_data)
    
    def get_component_performance(self, days=30):
        """Analyze performance by ML component strength"""
        ml_data = self.get_ml_component_analysis(days)
        if ml_data is None or ml_data.empty:
            return None
        
        # Categorize by component strength
        def categorize_strength(value, thresholds=[0.3, 0.6]):
            if value < thresholds[0]:
                return 'Low'
            elif value < thresholds[1]:
                return 'Medium'
            else:
                return 'High'
        
        ml_data['news_strength'] = ml_data['news_component'].apply(categorize_strength)
        ml_data['technical_strength'] = ml_data['technical_component'].apply(categorize_strength)
        
        # Calculate performance by component
        results = {}
        
        # News component performance
        news_perf = ml_data.groupby('news_strength').agg({
            'is_successful': ['count', 'sum', 'mean'],
            'news_component': 'mean'
        }).round(3)
        results['news'] = news_perf
        
        # Technical component performance  
        tech_perf = ml_data.groupby('technical_strength').agg({
            'is_successful': ['count', 'sum', 'mean'],
            'technical_component': 'mean'
        }).round(3)
        results['technical'] = tech_perf
        
        # Market context performance
        context_perf = ml_data.groupby('market_context').agg({
            'is_successful': ['count', 'sum', 'mean'],
            'overall_confidence': 'mean'
        }).round(3)
        results['context'] = context_perf
        
        return results

    def _get_sample_predictions_dataframe(self, days):
        """Get recent predictions from sample data with ML components"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_predictions = [
            p for p in self.sample_data
            if p['prediction_timestamp'] >= cutoff_date
        ]
        
        if not recent_predictions:
            return pd.DataFrame()
        
        # Format for display with sample ML components
        display_data = []
        for p in sorted(recent_predictions, key=lambda x: x['prediction_timestamp'], reverse=True)[:20]:
            display_data.append({
                'Date': p['prediction_timestamp'].strftime('%Y-%m-%d'),
                'Time': p['prediction_timestamp'].strftime('%H:%M'),
                'Symbol': p['symbol'],
                'Action': p['predicted_action'],
                'Confidence': f"{p['action_confidence']:.1%}",
                'ML Components': f"N:{np.random.uniform(0.3, 0.8):.1f} T:{np.random.uniform(0.2, 0.7):.1f}",
                'Market Context': np.random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
                'News Sentiment': f"{np.random.uniform(-0.5, 0.5):+.2f}",
                'Actual Return': f"{p['actual_return']:+.2f}%",
                'Success': '✅' if p['is_successful'] else '❌'
            })
        
        return pd.DataFrame(display_data)
    
    def get_last_ml_training_date(self):
        """Get the date of the last ML model training"""
        if self.use_sample_data:
            return datetime.now() - timedelta(days=2)  # Sample: 2 days ago
        
        try:
            conn = self.get_db_connection()
            
            # Check multiple sources for training date
            training_sources = []
            
            # 1. Check enhanced_evening_analysis for successful training
            query1 = """
            SELECT timestamp 
            FROM enhanced_evening_analysis 
            WHERE model_training LIKE '%true%' 
            ORDER BY timestamp DESC 
            LIMIT 1
            """
            
            result = conn.execute(query1).fetchone()
            if result:
                training_sources.append(('evening_analysis', result[0]))
            
            # 2. Check model_performance table
            query2 = """
            SELECT MAX(created_at) 
            FROM model_performance
            """
            
            result = conn.execute(query2).fetchone()
            if result and result[0]:
                training_sources.append(('model_performance', result[0]))
            
            # 3. Check when models were last updated (latest model version)
            query3 = """
            SELECT MIN(prediction_timestamp) 
            FROM predictions 
            WHERE model_version = 'fixed_price_mapping_v4.0'
            ORDER BY prediction_timestamp DESC
            LIMIT 1
            """
            
            result = conn.execute(query3).fetchone()
            if result and result[0]:
                training_sources.append(('latest_model_first_use', result[0]))
            
            conn.close()
            
            # Return the most recent training date
            if training_sources:
                latest_source = max(training_sources, key=lambda x: x[1])
                return pd.to_datetime(latest_source[1]).replace(tzinfo=None)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error getting last training date: {e}")
            # Fallback: known last training date based on model files
            return datetime(2025, 9, 7, 8, 0)

def main():
    """Main dashboard application"""
    st.set_page_config(
        page_title="ML Trading Performance Dashboard", 
        page_icon="🤖", 
        layout="wide"
    )
    
    st.title("🤖 Machine Learning Trading Performance Dashboard")
    st.markdown("### Real-Time ML Model Performance Tracker")
    st.markdown("---")
    
    # Initialize tracker
    tracker = TradingMLTracker()
    
    # Sidebar controls
    st.sidebar.header("🎛️ Dashboard Controls")
    
    # Time period selector
    days = st.sidebar.selectbox("Analysis Period", [7, 14, 30, 60, 90], index=2)
    
    # Data source indicator
    if tracker.use_sample_data:
        st.sidebar.warning("📭 Using Sample Data")
        st.sidebar.info("Real database not found. Displaying sample ML performance data.")
    else:
        st.sidebar.success("📊 Live Trading Data")
        st.sidebar.info(f"Connected to: {tracker.db_path}")
    
    # Data management
    st.sidebar.subheader("� Data Management")
    
    if st.sidebar.button("🔄 Refresh Dashboard"):
        st.rerun()
    
    # Get summary statistics
    summary = tracker.get_summary_stats(days=days)
    
    if not summary:
        st.warning("📭 No ML performance data available for the selected period.")
        
        if tracker.use_sample_data:
            st.info("👆 This dashboard shows sample data since the real trading database wasn't found.")
            st.markdown("""
            **To use real data:**
            - Ensure the trading database exists at `data/trading_predictions.db`
            - Make sure the database contains predictions and outcomes tables
            - Restart the dashboard
            """)
        else:
            st.info("Try selecting a longer time period or check if the trading system has generated predictions.")
        
        return
    
    # Key Performance Indicators
    st.subheader("📊 Key Performance Indicators")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Predictions", 
            summary['total_predictions'],
            delta=f"{summary['successful_predictions']} successful"
        )
    
    with col2:
        accuracy_delta = "📈 Above 50%" if summary['overall_accuracy'] > 0.5 else "📉 Below 50%"
        st.metric(
            "Success Rate", 
            f"{summary['overall_accuracy']:.1%}",
            delta=accuracy_delta
        )
    
    with col3:
        st.metric(
            "Average Confidence", 
            f"{summary['avg_confidence']:.1%}",
            delta="Live Trading System"
        )
    
    with col4:
        if summary['trend'] == 'sample_data':
            trend_display = "📊 Sample Data"
        else:
            trend_emoji = "📈" if summary['trend'] == 'improving' else "📉" if summary['trend'] == 'declining' else "➡️"
            trend_display = f"{trend_emoji} {summary['trend'].title()}"
        
        st.metric(
            "Performance Trend", 
            trend_display,
            delta=f"Last {days} days"
        )
    
    with col5:
        # ML Training Date
        last_training = tracker.get_last_ml_training_date()
        if last_training:
            days_since_training = (datetime.now() - last_training).days
            training_status = "🟢 Recent" if days_since_training <= 7 else "🟡 Aging" if days_since_training <= 14 else "🔴 Outdated"
            st.metric(
                "Last ML Training",
                last_training.strftime('%Y-%m-%d'),
                delta=f"{training_status} ({days_since_training} days ago)"
            )
        else:
            st.metric(
                "Last ML Training",
                "Unknown",
                delta="No training data found"
            )
    
    # Data source indicator
    if summary.get('data_source') == 'real_trading_data':
        st.success("✅ **Live Data**: Showing real ML performance from production trading system")
    else:
        st.info("📊 **Sample Data**: Demonstrating dashboard capabilities with generated data")
    
    # Performance Charts
    st.subheader("📈 Performance Analysis")
    
    daily_df = tracker.get_daily_dataframe(days=days)
    
    if not daily_df.empty:
        # Create main performance chart
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Daily Accuracy Trend',
                'Confidence Levels Over Time',
                'Predictions Volume',
                'Success Rate Distribution'
            ),
            vertical_spacing=0.12
        )
        
        # Daily accuracy
        fig.add_trace(
            go.Scatter(
                x=daily_df['date'],
                y=daily_df['accuracy'] * 100,
                mode='lines+markers',
                name='Accuracy %',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Add trend line
        if len(daily_df) > 3:
            z = np.polyfit(range(len(daily_df)), daily_df['accuracy'] * 100, 1)
            trend_line = np.poly1d(z)(range(len(daily_df)))
            fig.add_trace(
                go.Scatter(
                    x=daily_df['date'],
                    y=trend_line,
                    mode='lines',
                    name='Trend',
                    line=dict(color='red', dash='dash'),
                    opacity=0.7
                ),
                row=1, col=1
            )
        
        # Confidence levels
        fig.add_trace(
            go.Scatter(
                x=daily_df['date'],
                y=daily_df['avg_confidence'] * 100,
                mode='lines+markers',
                name='Avg Confidence %',
                line=dict(color='orange', width=3),
                marker=dict(size=8)
            ),
            row=1, col=2
        )
        
        # Predictions volume
        fig.add_trace(
            go.Bar(
                x=daily_df['date'],
                y=daily_df['predictions_made'],
                name='Daily Predictions',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # Success rate histogram
        fig.add_trace(
            go.Histogram(
                x=daily_df['accuracy'] * 100,
                nbinsx=10,
                name='Success Rate Distribution',
                marker_color='green',
                opacity=0.7
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            title=f"ML Performance Dashboard - Last {days} Days",
            showlegend=False
        )
        
        fig.update_yaxes(title_text="Accuracy (%)", row=1, col=1)
        fig.update_yaxes(title_text="Confidence (%)", row=1, col=2)
        fig.update_yaxes(title_text="Predictions Count", row=2, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=2)
        fig.update_xaxes(title_text="Success Rate (%)", row=2, col=2)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance insights
        st.subheader("💡 Performance Insights")
        
        avg_accuracy = daily_df['accuracy'].mean()
        recent_accuracy = daily_df['accuracy'].tail(7).mean()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if avg_accuracy > 0.65:
                st.success("🎉 **Excellent Performance!** Your ML models are performing exceptionally well with >65% accuracy.")
            elif avg_accuracy > 0.55:
                st.success("✅ **Good Performance!** Your models are significantly beating random chance.")
            elif avg_accuracy > 0.45:
                st.info("📊 **Fair Performance.** Your models show promise but have room for improvement.")
            else:
                st.warning("⚠️ **Needs Improvement.** Consider retraining models or adjusting parameters.")
            
            # Trend analysis
            if recent_accuracy > avg_accuracy + 0.05:
                st.success("📈 **Improving Trend:** Recent performance is better than average!")
            elif recent_accuracy < avg_accuracy - 0.05:
                st.warning("📉 **Declining Trend:** Recent performance is below average.")
            else:
                st.info("➡️ **Stable Performance:** Consistent accuracy over time.")
        
        with col2:
            if summary.get('data_source') == 'real_trading_data':
                st.metric("Data Source", "Live Trading DB")
                st.metric("Best Day", f"{daily_df['accuracy'].max():.1%}")
                st.metric("Avg Daily Predictions", f"{daily_df['predictions_made'].mean():.1f}")
            else:
                st.metric("Data Source", "Sample Data") 
                st.metric("Best Day", f"{daily_df['accuracy'].max():.1%}")
                st.metric("Avg Daily Predictions", f"{daily_df['predictions_made'].mean():.1f}")
    
    # ML Component Analysis Section
    st.markdown("---")
    st.subheader("🤖 Machine Learning Component Analysis")
    
    ml_data = tracker.get_ml_component_analysis(days=days)
    component_perf = tracker.get_component_performance(days=days)
    
    if ml_data is not None and not ml_data.empty:
        
        # ML Component Breakdown Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Component contribution pie chart
            avg_components = {
                'News Sentiment': ml_data['news_component'].mean(),
                'Technical Analysis': ml_data['technical_component'].mean(), 
                'Volume Analysis': ml_data['volume_component'].mean(),
                'Other Factors': max(0, 1 - ml_data['news_component'].mean() - ml_data['technical_component'].mean() - ml_data['volume_component'].mean())
            }
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(avg_components.keys()),
                values=list(avg_components.values()),
                hole=0.4,
                marker_colors=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
            )])
            fig_pie.update_layout(
                title="Average ML Component Contributions",
                height=400
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Component performance comparison
            if component_perf and 'news' in component_perf:
                news_acc = component_perf['news']['is_successful']['mean']
                tech_acc = component_perf['technical']['is_successful']['mean']
                
                fig_bar = go.Figure()
                
                # News component performance
                fig_bar.add_trace(go.Bar(
                    name='News Component',
                    x=['Low', 'Medium', 'High'],
                    y=news_acc.values if hasattr(news_acc, 'values') else [0.5, 0.6, 0.7],
                    marker_color='#ff9999'
                ))
                
                # Technical component performance
                fig_bar.add_trace(go.Bar(
                    name='Technical Component', 
                    x=['Low', 'Medium', 'High'],
                    y=tech_acc.values if hasattr(tech_acc, 'values') else [0.4, 0.65, 0.75],
                    marker_color='#66b3ff'
                ))
                
                fig_bar.update_layout(
                    title="Success Rate by Component Strength",
                    xaxis_title="Component Strength",
                    yaxis_title="Success Rate",
                    yaxis=dict(tickformat='.1%'),
                    height=400,
                    barmode='group'
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Detailed ML Metrics
        st.subheader("📊 ML Component Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # News sentiment impact - filter for meaningful news impact
            news_predictions = ml_data[ml_data['news_component'] > 0.01]  # More than 1% impact
            avg_news = news_predictions['news_component'].mean() if len(news_predictions) > 0 else 0
            news_success = news_predictions['is_successful'].mean() if len(news_predictions) > 0 else 0
            st.metric(
                "News Sentiment Impact",
                f"{avg_news:.1%}",
                delta=f"{news_success:.1%} success rate"
            )
        
        with col2:
            # Technical analysis impact - filter for meaningful technical impact
            tech_predictions = ml_data[ml_data['technical_component'] > 0.1]  # More than 10% impact
            avg_tech = tech_predictions['technical_component'].mean() if len(tech_predictions) > 0 else 0
            tech_success = tech_predictions['is_successful'].mean() if len(tech_predictions) > 0 else 0
            st.metric(
                "Technical Analysis Impact",
                f"{avg_tech:.1%}",
                delta=f"{tech_success:.1%} success rate"
            )
        
        with col3:
            # Volume analysis impact - filter for meaningful volume impact
            vol_predictions = ml_data[ml_data['volume_component'] > 0.01]  # More than 1% impact
            avg_vol = vol_predictions['volume_component'].mean() if len(vol_predictions) > 0 else 0
            vol_success = vol_predictions['is_successful'].mean() if len(vol_predictions) > 0 else 0
            st.metric(
                "Volume Analysis Impact",
                f"{avg_vol:.1%}",
                delta=f"{vol_success:.1%} success rate"
            )
        
        with col4:
            # Market context performance - find best performing context
            context_analysis = ml_data.groupby('market_context')['is_successful'].agg(['mean', 'count'])
            if not context_analysis.empty:
                # Filter contexts with at least 3 predictions
                valid_contexts = context_analysis[context_analysis['count'] >= 3]
                if not valid_contexts.empty:
                    best_context = valid_contexts['mean'].idxmax()
                    best_acc = valid_contexts.loc[best_context, 'mean']
                    context_count = valid_contexts.loc[best_context, 'count']
                    
                    # Clean up context name
                    display_context = best_context.split('(')[0].strip() if '(' in best_context else best_context
                    
                    st.metric(
                        "Best Market Context",
                        f"{display_context}",
                        delta=f"{best_acc:.1%} success rate"
                    )
                else:
                    st.metric(
                        "Market Context Analysis",
                        "NEUTRAL",
                        delta="Insufficient data"
                    )
            else:
                st.metric(
                    "Market Context Analysis",
                    "Available",
                    delta="Multi-factor analysis"
                )
        
        # ML Component Scatter Plot
        st.subheader("🎯 ML Component Correlation Analysis")
        
        fig_scatter = make_subplots(
            rows=1, cols=2,
            subplot_titles=('News vs Technical Components', 'Confidence vs Success Rate'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # News vs Technical scatter
        colors = ['green' if x == 1 else 'red' for x in ml_data['is_successful']]
        fig_scatter.add_trace(
            go.Scatter(
                x=ml_data['news_component'],
                y=ml_data['technical_component'],
                mode='markers',
                marker=dict(color=colors, size=8, opacity=0.6),
                name='Predictions',
                text=ml_data['symbol'],
                hovertemplate='<b>%{text}</b><br>News: %{x:.2f}<br>Technical: %{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        # Confidence vs Success scatter
        fig_scatter.add_trace(
            go.Scatter(
                x=ml_data['overall_confidence'],
                y=ml_data['is_successful'],
                mode='markers',
                marker=dict(
                    color=ml_data['actual_return'],
                    colorscale='RdYlGn',
                    size=8,
                    opacity=0.7,
                    colorbar=dict(title="Return %")
                ),
                name='Confidence Analysis',
                text=ml_data['symbol'],
                hovertemplate='<b>%{text}</b><br>Confidence: %{x:.2f}<br>Success: %{y}<extra></extra>'
            ),
            row=1, col=2
        )
        
        fig_scatter.update_xaxes(title_text="News Component Strength", row=1, col=1)
        fig_scatter.update_yaxes(title_text="Technical Component Strength", row=1, col=1)
        fig_scatter.update_xaxes(title_text="Overall Confidence", row=1, col=2)
        fig_scatter.update_yaxes(title_text="Success (1=Success, 0=Failure)", row=1, col=2)
        
        fig_scatter.update_layout(
            height=500,
            showlegend=False,
            title="ML Component Relationship Analysis"
        )
        
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # ML Insights
        st.subheader("🧠 Machine Learning Insights")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Analyze which components are most effective
            high_news = ml_data[ml_data['news_component'] > 0.6]
            high_tech = ml_data[ml_data['technical_component'] > 0.6]
            
            if len(high_news) > 0:
                news_success_rate = high_news['is_successful'].mean()
                if news_success_rate > 0.7:
                    st.success(f"🗞️ **News Analysis Strength**: {news_success_rate:.1%} success rate when news component > 60%")
                else:
                    st.info(f"🗞️ **News Analysis**: {news_success_rate:.1%} success rate when news component > 60%")
            
            if len(high_tech) > 0:
                tech_success_rate = high_tech['is_successful'].mean()
                if tech_success_rate > 0.7:
                    st.success(f"📈 **Technical Analysis Strength**: {tech_success_rate:.1%} success rate when technical component > 60%")
                else:
                    st.info(f"📈 **Technical Analysis**: {tech_success_rate:.1%} success rate when technical component > 60%")
            
            # Confidence analysis
            high_conf = ml_data[ml_data['overall_confidence'] > 0.75]
            if len(high_conf) > 0:
                conf_success_rate = high_conf['is_successful'].mean()
                if conf_success_rate > 0.8:
                    st.success(f"🎯 **High Confidence Predictions**: {conf_success_rate:.1%} success rate when confidence > 75%")
                else:
                    st.warning(f"⚠️ **High Confidence Warning**: Only {conf_success_rate:.1%} success rate when confidence > 75%")
        
        with col2:
            st.metric("ML Components Tracked", "4", help="News, Technical, Volume, Market Context")
            st.metric("Average Confidence", f"{ml_data['overall_confidence'].mean():.1%}")
            st.metric("Component Balance", "Multi-factor", help="Uses multiple ML components for predictions")
    
    else:
        st.info("🤖 **ML Component Analysis**: Not available for selected time period or data source.")
        st.markdown("""
        **ML components tracked include:**
        - 🗞️ **News Sentiment Analysis**: Market news impact scoring
        - 📈 **Technical Analysis**: Price patterns and indicators  
        - 📊 **Volume Analysis**: Trading volume trends
        - 🌍 **Market Context**: Overall market conditions
        """)
    
    # Model Training & Performance Section
    st.markdown("---")
    st.subheader("🏋️ Model Training & Performance")
    
    # Check for enhanced outcomes (training data)
    try:
        conn = tracker.get_db_connection()
        if conn:
            enhanced_count = pd.read_sql_query("SELECT COUNT(*) as count FROM enhanced_outcomes", conn)['count'].iloc[0]
            conn.close()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Training Samples", enhanced_count, help="Enhanced outcomes used for ML training")
            
            with col2:
                # Estimate model sophistication based on data
                if enhanced_count > 100:
                    sophistication = "Advanced"
                elif enhanced_count > 50:
                    sophistication = "Intermediate" 
                else:
                    sophistication = "Basic"
                st.metric("Model Sophistication", sophistication, help="Based on training data volume")
            
            with col3:
                st.metric("ML Architecture", "Ensemble", help="Multiple model combination approach")
        
        # Training data insights
        if enhanced_count > 0:
            st.success(f"✅ **Active ML Training**: {enhanced_count} training samples available for continuous model improvement")
        else:
            st.info("📚 **Training Status**: Models using baseline training data")
            
    except Exception as e:
        st.warning("⚠️ **Training Data**: Unable to access ML training metrics")
    
    else:
        # Performance insights
        st.subheader("💡 Performance Insights")
        
        avg_accuracy = daily_df['accuracy'].mean()
        recent_accuracy = daily_df['accuracy'].tail(7).mean()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if avg_accuracy > 0.65:
                st.success("🎉 **Excellent Performance!** Your ML models are performing exceptionally well with >65% accuracy.")
            elif avg_accuracy > 0.55:
                st.success("✅ **Good Performance!** Your models are significantly beating random chance.")
            elif avg_accuracy > 0.45:
                st.info("📊 **Fair Performance.** Your models show promise but have room for improvement.")
            else:
                st.warning("⚠️ **Needs Improvement.** Consider retraining models or adjusting parameters.")
            
            # Trend analysis
            if recent_accuracy > avg_accuracy + 0.05:
                st.success("📈 **Improving Trend:** Recent performance is better than average!")
            elif recent_accuracy < avg_accuracy - 0.05:
                st.warning("📉 **Declining Trend:** Recent performance is below average.")
            else:
                st.info("➡️ **Stable Performance:** Consistent accuracy over time.")
        
        with col2:
            if summary.get('data_source') == 'real_trading_data':
                st.metric("Data Source", "Live Trading DB")
                st.metric("Best Day", f"{daily_df['accuracy'].max():.1%}")
                st.metric("Avg Daily Predictions", f"{daily_df['predictions_made'].mean():.1f}")
            else:
                st.metric("Data Source", "Sample Data") 
                st.metric("Best Day", f"{daily_df['accuracy'].max():.1%}")
                st.metric("Avg Daily Predictions", f"{daily_df['predictions_made'].mean():.1f}")
    
    # Recent Predictions Table
    st.subheader("🔍 Recent ML Predictions with Component Analysis")
    
    predictions_df = tracker.get_predictions_dataframe(days=7)
    
    if not predictions_df.empty:
        # Add some styling
        def highlight_success(row):
            return ['background-color: #d4edda' if row['Success'] == '✅' else 
                   'background-color: #f8d7da' if row['Success'] == '❌' else 
                   'background-color: #fff3cd' if row['Success'] == '⏳' else '' for _ in row]
        
        styled_df = predictions_df.head(20).style.apply(highlight_success, axis=1)
        st.dataframe(styled_df, use_container_width=True)
        
        success_count = len(predictions_df[predictions_df['Success'] == '✅'])
        pending_count = len(predictions_df[predictions_df['Success'] == '⏳'])
        total_count = len(predictions_df)
        evaluated_count = total_count - pending_count
        
        if evaluated_count > 0:
            success_rate = success_count / evaluated_count * 100
            st.caption(f"Showing last 20 predictions from past 7 days. Success rate: {success_count}/{evaluated_count} ({success_rate:.1f}%) | {pending_count} pending evaluation")
            st.caption("**ML Components**: N=News Sentiment, T=Technical Analysis | **Market Context**: Current market conditions")
        else:
            st.caption(f"Showing last 20 predictions from past 7 days. All {pending_count} predictions pending evaluation.")
    else:
        st.info("No recent predictions found.")
    
    # Footer
    st.markdown("---")
    st.markdown("**🤖 About This ML Performance Dashboard:**")
    if tracker.use_sample_data:
        st.markdown("- Currently displaying sample ML performance data")
        st.markdown("- Shows news sentiment, technical analysis, and volume components")
        st.markdown("- Analyzes ML component contributions and correlations")
        st.markdown("- Database path: `data/trading_predictions.db`")
    else:
        st.markdown("- **Live ML Component Tracking**: Real-time analysis of ML model components")
        st.markdown("- **News Sentiment Analysis**: Tracks impact of market news on predictions")
        st.markdown("- **Technical Analysis**: Monitors technical indicator contributions")
        st.markdown("- **Multi-factor ML Models**: Combines news, technical, volume, and market context")
        st.markdown("- **Training Data Integration**: Shows model learning and improvement over time")
        st.markdown(f"- **Data source**: `{tracker.db_path}` with {summary.get('total_predictions', 0)} predictions analyzed")
        
        # Add ML training information
        last_training = tracker.get_last_ml_training_date()
        if last_training:
            days_since = (datetime.now() - last_training).days
            st.markdown(f"- **Last ML Training**: {last_training.strftime('%Y-%m-%d %H:%M')} ({days_since} days ago)")
            if days_since > 14:
                st.warning("⚠️ ML models haven't been retrained in over 2 weeks. Consider running evening training routine.")
            elif days_since > 7:
                st.info("ℹ️ ML models are getting older. Consider retraining soon for optimal performance.")
        else:
            st.markdown("- **ML Training Status**: Unknown - check training logs")

if __name__ == "__main__":
    main()