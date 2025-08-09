#!/usr/bin/env python3
"""
ASX Banks Trading Sentiment Dashboard - Streamlined Version
Real-time sentiment analysis and ML predictions for Australian bank stocks
"""

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Configuration
DATABASE_PATH = "data/trading_unified.db"
ASX_BANKS = ['CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX']

class DatabaseError(Exception):
    pass

class DataError(Exception):
    pass

def get_database_connection() -> sqlite3.Connection:
    """Get connection to the unified trading database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL") 
        conn.execute("PRAGMA cache_size=10000")
        conn.execute("PRAGMA temp_store=memory")
        return conn
    except Exception as e:
        raise DatabaseError(f"Could not connect to database {DATABASE_PATH}: {e}")

def fetch_enhanced_ml_training_metrics() -> Dict:
    """Fetch enhanced ML training metrics with historical performance"""
    try:
        conn = get_database_connection()
        
        # Prefer the unified performance table; fall back to legacy only if present
        has_mpe = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='model_performance_enhanced'"
        ).fetchone()
        table_name = 'model_performance_enhanced' if has_mpe else 'ml_training_history'
        
        if table_name == 'ml_training_history':
            has_legacy = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ml_training_history'"
            ).fetchone()
            if not has_legacy:
                conn.close()
                return {
                    'status': 'NO_DATA',
                    'training_samples': 0,
                    'direction_accuracy_4h': 0.0,
                    'last_training': None,
                    'samples_threshold': 100,
                    'accuracy_threshold': 0.65
                }
        
        # Discover columns to choose the right ordering/time field
        col_info_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        col_names = [r[1] for r in col_info_rows] if col_info_rows else []
        time_col = 'created_at' if 'created_at' in col_names else ('timestamp' if 'timestamp' in col_names else None)
        order_clause = f"ORDER BY {time_col} DESC" if time_col else "ORDER BY rowid DESC"
        
        # Get latest training metrics
        cursor = conn.execute(f"""
            SELECT * FROM {table_name}
            {order_clause}
            LIMIT 1
        """)
        latest_row = cursor.fetchone()
        
        if not latest_row:
            conn.close()
            return {
                'status': 'NO_DATA',
                'training_samples': 0,
                'direction_accuracy_4h': 0.0,
                'last_training': None,
                'samples_threshold': 100,
                'accuracy_threshold': 0.65
            }
        
        latest_columns = [desc[0] for desc in cursor.description]
        metrics_dict = dict(zip(latest_columns, latest_row))
        
        # Get historical performance for progression tracking
        cursor = conn.execute(f"""
            SELECT * FROM {table_name}
            {order_clause}
            LIMIT 10
        """)
        historical_rows = cursor.fetchall()
        historical_cols = [desc[0] for desc in cursor.description]
        historical_performance = [dict(zip(historical_cols, r)) for r in historical_rows]
        
        conn.close()
        
        # Enhanced metrics with status
        samples = metrics_dict.get('training_samples') or metrics_dict.get('samples') or 0
        accuracy = metrics_dict.get('direction_accuracy_4h') or metrics_dict.get('average_direction_accuracy') or 0.0
        
        if samples >= 100 and accuracy >= 0.70:
            status = 'EXCELLENT'
        elif samples >= 50 and accuracy >= 0.65:
            status = 'GOOD'
        elif samples >= 20:
            status = 'NEEDS_IMPROVEMENT'
        else:
            status = 'NO_DATA'
        
        return {
            'status': status,
            'training_samples': samples,
            'direction_accuracy_4h': accuracy,
            'last_training': metrics_dict.get(time_col) if time_col else None,
            'samples_threshold': 100,
            'accuracy_threshold': 0.65,
            'historical_performance': historical_performance
        }
        
    except Exception as e:
        st.warning(f"Could not fetch enhanced ML metrics: {e}")
        return {
            'status': 'NO_DATA',
            'training_samples': 0,
            'direction_accuracy_4h': 0.0,
            'last_training': None
        }

def fetch_current_sentiment_scores() -> pd.DataFrame:
    """Fetch the most recent sentiment scores for all banks"""
    try:
        conn = get_database_connection()
        
        query = """
        SELECT 
            ef.symbol,
            ef.sentiment_score,
            ef.confidence,
            ef.news_count,
            ef.reddit_sentiment,
            ef.volatility_20d,
            ef.current_price,
            ef.timestamp,
            ef.rsi,
            ef.macd_line,
            ef.price_vs_sma20
        FROM enhanced_features ef
        WHERE ef.id IN (
            SELECT MAX(id) FROM enhanced_features 
            WHERE symbol IN ('CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX')
            GROUP BY symbol
        )
        ORDER BY ef.symbol
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            raise DataError("No current sentiment data available")
            
        return df
        
    except Exception as e:
        st.error(f"Error fetching current sentiment: {e}")
        return pd.DataFrame()

def compute_component_attribution(days: int = 30) -> Dict:
    """Calculate ACTUAL component contribution to successful trades"""
    try:
        conn = get_database_connection()
        symbols_list = ",".join([f"'{s}'" for s in ASX_BANKS])
        
        # Get completed trades with component data
        query = f"""
        SELECT 
            ef.sentiment_score,
            ef.rsi,
            ef.macd_line,
            ef.reddit_sentiment,
            eo.optimal_action,
            eo.return_pct,
            CASE WHEN eo.return_pct > 0 THEN 1 ELSE 0 END as is_winner
        FROM enhanced_features ef
        INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.timestamp >= datetime('now', '-{days} days')
          AND ef.symbol IN ({symbols_list})
          AND eo.return_pct IS NOT NULL
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {}
        
        total_trades = len(df)
        winning_trades = df[df['is_winner'] == 1]
        losing_trades = df[df['is_winner'] == 0]
        
        # Calculate component alignment with winners
        attribution = {}
        
        if len(winning_trades) > 0:
            # News sentiment alignment
            news_aligned_wins = len(winning_trades[
                ((winning_trades['sentiment_score'] > 0.1) & (winning_trades['optimal_action'] == 'BUY')) |
                ((winning_trades['sentiment_score'] < -0.1) & (winning_trades['optimal_action'] == 'SELL'))
            ])
            attribution['news_win_rate'] = news_aligned_wins / len(winning_trades) * 100
            
            # Technical alignment (RSI oversold for buys, overbought for sells)
            tech_aligned_wins = len(winning_trades[
                ((winning_trades['rsi'] < 35) & (winning_trades['optimal_action'] == 'BUY')) |
                ((winning_trades['rsi'] > 65) & (winning_trades['optimal_action'] == 'SELL'))
            ])
            attribution['tech_win_rate'] = tech_aligned_wins / len(winning_trades) * 100
            
            # MACD alignment
            macd_aligned_wins = len(winning_trades[
                ((winning_trades['macd_line'] > 0) & (winning_trades['optimal_action'] == 'BUY')) |
                ((winning_trades['macd_line'] < 0) & (winning_trades['optimal_action'] == 'SELL'))
            ])
            attribution['macd_win_rate'] = macd_aligned_wins / len(winning_trades) * 100
            
            # Social sentiment alignment (where available)
            social_data = winning_trades.dropna(subset=['reddit_sentiment'])
            if len(social_data) > 0:
                social_aligned_wins = len(social_data[
                    ((social_data['reddit_sentiment'] > 0.1) & (social_data['optimal_action'] == 'BUY')) |
                    ((social_data['reddit_sentiment'] < -0.1) & (social_data['optimal_action'] == 'SELL'))
                ])
                attribution['social_win_rate'] = social_aligned_wins / len(social_data) * 100
                attribution['social_coverage'] = len(social_data) / len(winning_trades) * 100
            else:
                attribution['social_win_rate'] = 0
                attribution['social_coverage'] = 0
        
        # Multi-component alignment analysis
        if len(df) > 0:
            # Count trades where 3+ components aligned
            df['components_aligned'] = 0
            
            # News component
            df.loc[
                ((df['sentiment_score'] > 0.1) & (df['optimal_action'] == 'BUY')) |
                ((df['sentiment_score'] < -0.1) & (df['optimal_action'] == 'SELL')),
                'components_aligned'
            ] += 1
            
            # Technical component
            df.loc[
                ((df['rsi'] < 35) & (df['optimal_action'] == 'BUY')) |
                ((df['rsi'] > 65) & (df['optimal_action'] == 'SELL')),
                'components_aligned'
            ] += 1
            
            # MACD component
            df.loc[
                ((df['macd_line'] > 0) & (df['optimal_action'] == 'BUY')) |
                ((df['macd_line'] < 0) & (df['optimal_action'] == 'SELL')),
                'components_aligned'
            ] += 1
            
            # Social component (where available)
            social_mask = df['reddit_sentiment'].notna()
            df.loc[
                social_mask & (
                    ((df['reddit_sentiment'] > 0.1) & (df['optimal_action'] == 'BUY')) |
                    ((df['reddit_sentiment'] < -0.1) & (df['optimal_action'] == 'SELL'))
                ),
                'components_aligned'
            ] += 1
            
            # Calculate win rates by component alignment
            attribution['multi_component_analysis'] = {}
            for i in range(5):  # 0-4 components aligned
                subset = df[df['components_aligned'] == i]
                if len(subset) > 0:
                    win_rate = subset['is_winner'].mean() * 100
                    attribution['multi_component_analysis'][f'{i}_components'] = {
                        'trades': len(subset),
                        'win_rate': win_rate
                    }
        
        attribution.update({
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'overall_win_rate': len(winning_trades) / total_trades * 100 if total_trades > 0 else 0,
            'period_days': days
        })
        
        return attribution
        
    except Exception as e:
        st.warning(f"Could not compute component attribution: {e}")
        return {}


def compute_overview_metrics(days: int = 14) -> Dict:
    """Compute overview metrics for News, Social, ML, and Technical pillars"""
    try:
        conn = get_database_connection()
        symbols_list = ",".join([f"'{s}'" for s in ASX_BANKS])

        # Aggregate from enhanced_features for last N days
        agg = conn.execute(f"""
            SELECT 
                COUNT(*) as predictions,
                SUM(news_count) as total_news,
                AVG(sentiment_score) as avg_sentiment,
                AVG(confidence) as avg_confidence,
                AVG(CASE WHEN reddit_sentiment IS NOT NULL THEN reddit_sentiment END) as avg_reddit,
                COUNT(CASE WHEN reddit_sentiment IS NOT NULL THEN 1 END) as reddit_count,
                AVG(event_score) as avg_event_score,
                AVG(rsi) as avg_rsi,
                AVG(macd_line) as avg_macd,
                AVG(price_vs_sma20) as avg_price_vs_sma20,
                AVG(bollinger_width) as avg_bbw,
                AVG(market_momentum) as avg_momentum
            FROM enhanced_features ef
            WHERE ef.timestamp >= datetime('now', '-{days} days')
              AND ef.symbol IN ({symbols_list})
        """).fetchone()
        predictions = agg[0] or 0
        total_news = agg[1] or 0
        avg_sentiment = float(agg[2] or 0.0)
        avg_confidence = float(agg[3] or 0.0)
        avg_reddit = float(agg[4] or 0.0)
        reddit_count = int(agg[5] or 0)
        avg_event_score = float(agg[6] or 0.0)
        avg_rsi = float(agg[7] or 0.0)
        avg_macd = float(agg[8] or 0.0)
        avg_price_vs_sma20 = float(agg[9] or 0.0)
        avg_bbw = float(agg[10] or 0.0)
        avg_momentum = float(agg[11] or 0.0)

        # Outcomes over last N days
        outc = conn.execute(f"""
            SELECT 
                COUNT(*) as outcomes_completed,
                AVG(CASE WHEN return_pct > 0 THEN 1.0 ELSE 0.0 END) as win_rate,
                AVG(return_pct) as avg_return
            FROM enhanced_outcomes eo
            INNER JOIN enhanced_features ef ON ef.id = eo.feature_id
            WHERE ef.timestamp >= datetime('now', '-{days} days')
              AND ef.symbol IN ({symbols_list})
              AND eo.return_pct IS NOT NULL
        """).fetchone()
        outcomes_completed = outc[0] or 0
        win_rate = float(outc[1] or 0.0)
        avg_return = float(outc[2] or 0.0)

        # Latest ML training metrics
        ml_metrics = fetch_enhanced_ml_training_metrics()

        conn.close()

        # Social coverage percentage
        social_coverage = (reddit_count / predictions) * 100 if predictions else 0.0

        return {
            'period_days': days,
            'news': {
                'avg_sentiment': avg_sentiment,
                'avg_confidence': avg_confidence,
                'total_news': int(total_news),
                'avg_event_score': avg_event_score
            },
            'social': {
                'avg_reddit_sentiment': avg_reddit,
                'coverage_pct': social_coverage
            },
            'technical': {
                'avg_rsi': avg_rsi,
                'avg_macd': avg_macd,
                'avg_price_vs_sma20': avg_price_vs_sma20,
                'avg_bollinger_width': avg_bbw,
                'avg_momentum': avg_momentum
            },
            'ml': {
                'predictions': int(predictions),
                'outcomes_completed': int(outcomes_completed),
                'win_rate': win_rate,
                'avg_return': avg_return,
                'training_samples': ml_metrics.get('training_samples', 0),
                'direction_accuracy_4h': ml_metrics.get('direction_accuracy_4h', 0.0),
                'last_training': ml_metrics.get('last_training'),
                'status': ml_metrics.get('status', 'NO_DATA')
            }
        }
    except Exception as e:
        st.warning(f"Could not compute overview metrics: {e}")
        return {}


def render_training_data_health():
    """Visualize training data quality and coverage"""
    st.subheader("🔍 Training Data Health Monitor")
    
    try:
        conn = get_database_connection()
        
        # Data recency analysis
        recency_query = """
        SELECT 
            COUNT(*) as total_samples,
            COUNT(CASE WHEN timestamp >= datetime('now', '-30 days') THEN 1 END) as recent_30d,
            COUNT(CASE WHEN timestamp >= datetime('now', '-60 days') THEN 1 END) as recent_60d,
            MIN(timestamp) as oldest_data,
            MAX(timestamp) as newest_data
        FROM enhanced_features
        """
        recency_data = conn.execute(recency_query).fetchone()
        
        # Data balance analysis
        balance_query = """
        SELECT 
            COUNT(*) as total_outcomes,
            COUNT(CASE WHEN return_pct > 0 THEN 1 END) as winning_trades,
            COUNT(CASE WHEN return_pct < 0 THEN 1 END) as losing_trades,
            COUNT(CASE WHEN optimal_action = 'BUY' THEN 1 END) as buy_signals,
            COUNT(CASE WHEN optimal_action = 'SELL' THEN 1 END) as sell_signals,
            COUNT(CASE WHEN optimal_action = 'HOLD' THEN 1 END) as hold_signals
        FROM enhanced_outcomes
        WHERE return_pct IS NOT NULL
        """
        balance_data = conn.execute(balance_query).fetchone()
        
        # Coverage by symbol
        coverage_query = """
        SELECT 
            symbol,
            COUNT(*) as samples,
            COUNT(CASE WHEN timestamp >= datetime('now', '-30 days') THEN 1 END) as recent_samples
        FROM enhanced_features
        WHERE symbol IN ('CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX')
        GROUP BY symbol
        ORDER BY samples DESC
        """
        coverage_data = conn.execute(coverage_query).fetchall()
        
        # Feature completeness
        completeness_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(CASE WHEN reddit_sentiment IS NOT NULL THEN 1 END) as has_social,
            COUNT(CASE WHEN news_count > 0 THEN 1 END) as has_news,
            COUNT(CASE WHEN rsi IS NOT NULL THEN 1 END) as has_technical
        FROM enhanced_features
        WHERE timestamp >= datetime('now', '-30 days')
        """
        completeness = conn.execute(completeness_query).fetchone()
        
        conn.close()
        
        # Display health metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if recency_data:
                recent_pct = (recency_data[1] / recency_data[0] * 100) if recency_data[0] > 0 else 0
                color = "normal" if recent_pct > 60 else "inverse"
                st.metric(
                    "Data Freshness", 
                    f"{recent_pct:.0f}%",
                    delta=f"{recency_data[1]} of {recency_data[0]} samples from last 30d",
                    delta_color=color
                )
        
        with col2:
            if balance_data and balance_data[0] > 0:
                win_pct = (balance_data[1] / balance_data[0] * 100)
                balance_score = 100 - abs(50 - win_pct)  # Perfect balance = 50% wins
                st.metric(
                    "Class Balance",
                    f"{balance_score:.0f}/100",
                    delta=f"{win_pct:.0f}% wins, {100-win_pct:.0f}% losses"
                )
        
        with col3:
            if coverage_data:
                min_samples = min([row[1] for row in coverage_data])
                avg_samples = sum([row[1] for row in coverage_data]) / len(coverage_data)
                st.metric(
                    "Coverage Balance",
                    f"{min_samples} min",
                    delta=f"Avg: {avg_samples:.0f} samples per bank"
                )
        
        with col4:
            if completeness:
                feature_completeness = (
                    (completeness[1] / completeness[0]) * 0.2 +  # Social 20%
                    (completeness[2] / completeness[0]) * 0.5 +  # News 50%
                    (completeness[3] / completeness[0]) * 0.3    # Technical 30%
                ) * 100
                st.metric(
                    "Feature Quality",
                    f"{feature_completeness:.0f}/100",
                    delta="Weighted completeness score"
                )
        
        # Red flags section
        red_flags = []
        if recency_data and recency_data[1] / recency_data[0] < 0.5:
            red_flags.append("⚠️ Training data older than 60 days")
        if balance_data and balance_data[0] > 0:
            win_rate = balance_data[1] / balance_data[0]
            if win_rate > 0.8 or win_rate < 0.2:
                red_flags.append(f"⚠️ Imbalanced classes ({win_rate*100:.0f}% wins)")
        if completeness and completeness[1] / completeness[0] < 0.4:
            red_flags.append("⚠️ Missing social data for >60% of samples")
        
        if red_flags:
            st.warning("**Data Quality Issues:**\n" + "\n".join(red_flags))
        else:
            st.success("✅ Training data quality looks good!")
        
        # Detailed breakdown
        with st.expander("📊 Detailed Data Health Analysis", expanded=False):
            if coverage_data:
                st.markdown("**Sample Distribution by Bank:**")
                for symbol, total, recent in coverage_data:
                    st.write(f"- {symbol}: {total} total samples ({recent} recent)")
            
            if balance_data:
                st.markdown(f"""
                **Signal Distribution:**
                - Buy Signals: {balance_data[3]}
                - Sell Signals: {balance_data[4]} 
                - Hold Signals: {balance_data[5]}
                - Win/Loss Ratio: {balance_data[1]}W / {balance_data[2]}L
                """)
        
    except Exception as e:
        st.error(f"Could not load training data health: {e}")


def render_performance_tracker():
    """Track predictions vs actual outcomes in real-time"""
    st.subheader("📊 Real-time Performance Tracker")
    
    try:
        conn = get_database_connection()
        
        # Get recent predictions with outcomes
        query = """
        SELECT 
            ef.symbol,
            ef.timestamp,
            ef.sentiment_score,
            ef.current_price as predicted_price,
            eo.optimal_action as prediction,
            eo.confidence_score,
            eo.return_pct as actual_return,
            eo.price_direction_1d as predicted_direction,
            CASE 
                WHEN eo.return_pct > 0 THEN 'UP'
                WHEN eo.return_pct < 0 THEN 'DOWN'
                ELSE 'FLAT'
            END as actual_direction
        FROM enhanced_features ef
        INNER JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.timestamp >= datetime('now', '-7 days')
          AND eo.return_pct IS NOT NULL
        ORDER BY ef.timestamp DESC
        LIMIT 20
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            st.warning("No recent prediction outcomes available")
            return
        
        # Performance summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Direction accuracy
        direction_matches = (df['predicted_direction'] == df['actual_direction']).sum()
        direction_total = len(df.dropna(subset=['predicted_direction', 'actual_direction']))
        direction_accuracy = (direction_matches / direction_total * 100) if direction_total > 0 else 0
        
        with col1:
            st.metric(
                "Direction Accuracy",
                f"{direction_accuracy:.0f}%",
                delta=f"{direction_matches}/{direction_total} correct"
            )
        
        # Confidence calibration
        high_conf = df[df['confidence_score'] > 0.7]
        if len(high_conf) > 0:
            high_conf_accuracy = (high_conf['predicted_direction'] == high_conf['actual_direction']).mean() * 100
        else:
            high_conf_accuracy = 0
        
        with col2:
            st.metric(
                "High Conf Accuracy",
                f"{high_conf_accuracy:.0f}%",
                delta=f"When confidence >70%"
            )
        
        # Average return when correct
        correct_predictions = df[df['predicted_direction'] == df['actual_direction']]
        if len(correct_predictions) > 0:
            avg_correct_return = correct_predictions['actual_return'].mean() * 100
        else:
            avg_correct_return = 0
        
        with col3:
            st.metric(
                "Avg Return (Correct)",
                f"{avg_correct_return:+.1f}%",
                delta="When direction right"
            )
        
        # Win rate
        wins = (df['actual_return'] > 0).sum()
        win_rate = (wins / len(df) * 100) if len(df) > 0 else 0
        
        with col4:
            st.metric(
                "Win Rate",
                f"{win_rate:.0f}%",
                delta=f"{wins}/{len(df)} profitable"
            )
        
        # Recent predictions table
        st.markdown("### 📋 Recent Prediction Outcomes")
        
        if not df.empty:
            display_df = df.copy()
            
            # Format timestamp
            display_df['Date'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%m-%d')
            
            # Direction match indicator
            display_df['Match'] = display_df.apply(lambda row: 
                '✓' if row['predicted_direction'] == row['actual_direction'] else '✗', axis=1
            )
            
            # Format confidence
            display_df['Confidence'] = (display_df['confidence_score'] * 100).round(0).astype(str) + '%'
            
            # Format return
            display_df['Return'] = display_df['actual_return'].apply(lambda x: f"{x*100:+.1f}%" if pd.notna(x) else "N/A")
            
            # Outcome indicator
            display_df['Outcome'] = display_df['actual_return'].apply(lambda x: 
                '✅' if x > 0.01 else '❌' if x < -0.01 else '⚪' if pd.notna(x) else '❓'
            )
            
            # Select display columns
            display_cols = ['Date', 'symbol', 'prediction', 'predicted_direction', 'actual_direction', 'Match', 'Confidence', 'Return', 'Outcome']
            display_names = ['Date', 'Bank', 'Action', 'Pred Dir', 'Actual Dir', 'Match?', 'Confidence', 'Return', 'Result']
            
            final_display = display_df[display_cols]
            final_display.columns = display_names
            
            st.dataframe(final_display, use_container_width=True, hide_index=True)
        
        # Confidence calibration analysis
        with st.expander("🎯 Confidence Calibration Analysis", expanded=False):
            if not df.empty:
                # Group by confidence ranges
                df['conf_bucket'] = pd.cut(df['confidence_score'], 
                                         bins=[0, 0.5, 0.7, 0.8, 1.0], 
                                         labels=['<50%', '50-70%', '70-80%', '>80%'])
                
                calibration = df.groupby('conf_bucket').agg({
                    'predicted_direction': 'count',
                    'actual_return': lambda x: (x > 0).mean() * 100
                }).round(1)
                calibration.columns = ['Predictions', 'Win Rate %']
                
                st.markdown("**Confidence vs Actual Performance:**")
                st.dataframe(calibration)
                
                st.markdown("""
                **Ideal Calibration:**
                - When confidence is 70%, accuracy should be ~70%
                - When confidence is 80%, accuracy should be ~80%
                - Large gaps indicate overconfidence or underconfidence
                """)
    
    except Exception as e:
        st.error(f"Could not load performance tracker: {e}")


def render_ml_progress_timeline():
    """Show ML model evolution and its impact on trading outcomes"""
    st.subheader("🚀 ML Model Evolution & Impact")
    
    try:
        conn = get_database_connection()
        
        # Get historical ML performance data
        ml_history = conn.execute("""
            SELECT 
                model_version,
                training_samples,
                direction_accuracy_4h,
                created_at,
                strftime('%Y-%m-%d', created_at) as date
            FROM model_performance_enhanced
            ORDER BY created_at ASC
        """).fetchall()
        
        conn.close()
        
        if not ml_history:
            st.warning("No ML training history available")
            return
        
        # Convert to DataFrame for easier manipulation
        df_ml = pd.DataFrame(ml_history, columns=[
            'model_version', 'training_samples', 'direction_accuracy_4h', 
            'created_at', 'date'
        ])
        
        # Create timeline visualization
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 Training Progress")
            
            # Training samples growth
            fig_samples = px.line(
                df_ml, 
                x='date', 
                y='training_samples',
                title='Training Samples Growth',
                markers=True
            )
            fig_samples.update_layout(height=300)
            st.plotly_chart(fig_samples, use_container_width=True)
            
            # Show key milestones
            latest = df_ml.iloc[-1]
            first = df_ml.iloc[0]
            
            samples_growth = latest['training_samples'] - first['training_samples']
            st.metric(
                "Sample Growth", 
                f"+{samples_growth}",
                delta=f"From {first['training_samples']} to {latest['training_samples']}"
            )
        
        with col2:
            st.markdown("### 🎯 Accuracy Evolution")
            
            # Accuracy improvement
            fig_accuracy = px.line(
                df_ml, 
                x='date', 
                y='direction_accuracy_4h',
                title='Model Accuracy Over Time',
                markers=True
            )
            fig_accuracy.add_hline(
                y=0.70, 
                line_dash="dash", 
                line_color="green",
                annotation_text="Target: 70%"
            )
            fig_accuracy.update_layout(height=300)
            st.plotly_chart(fig_accuracy, use_container_width=True)
            
            # Show accuracy progression
            accuracy_change = latest['direction_accuracy_4h'] - first['direction_accuracy_4h']
            st.metric(
                "Accuracy Change", 
                f"{accuracy_change:+.1%}",
                delta=f"From {first['direction_accuracy_4h']:.1%} to {latest['direction_accuracy_4h']:.1%}"
            )
        
        # Performance correlation analysis
        st.markdown("### 🔄 Model Performance vs Trading Outcomes")
        
        # Get actual trading performance for each model version
        attribution = compute_component_attribution(days=60)
        
        if attribution:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Current Win Rate", 
                    f"{attribution.get('overall_win_rate', 0):.1f}%",
                    help="Overall win rate from completed trades"
                )
            
            with col2:
                current_accuracy = latest['direction_accuracy_4h'] * 100
                st.metric(
                    "Model Accuracy", 
                    f"{current_accuracy:.1f}%",
                    help="Latest training accuracy"
                )
            
            with col3:
                # Simple correlation indicator
                correlation_strength = "Strong" if abs(attribution.get('overall_win_rate', 0) - current_accuracy) < 10 else "Weak"
                st.metric(
                    "Accuracy-Performance Correlation",
                    correlation_strength,
                    help="How well model accuracy predicts actual returns"
                )
        
        # Model version timeline
        with st.expander("📋 Detailed Model History", expanded=False):
            for i, row in df_ml.iterrows():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.write(f"**{row['model_version']}**")
                with col2:
                    st.write(f"Samples: {row['training_samples']}")
                with col3:
                    st.write(f"Accuracy: {row['direction_accuracy_4h']:.1%}")
                with col4:
                    st.write(f"Date: {row['date']}")
                
                if i < len(df_ml) - 1:
                    st.divider()
        
    except Exception as e:
        st.error(f"Could not load ML progress timeline: {e}")


def render_component_attribution():
    """Show which components actually led to winning trades"""
    st.subheader("🎯 Component Attribution Analysis")
    
    attribution = compute_component_attribution(days=30)
    
    if not attribution:
        st.warning("No component attribution data available")
        return
    
    # Main attribution metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📰 News Alignment",
            f"{attribution.get('news_win_rate', 0):.0f}%",
            help="% of winning trades where news sentiment aligned with action"
        )
    
    with col2:
        st.metric(
            "📈 Technical Alignment", 
            f"{attribution.get('tech_win_rate', 0):.0f}%",
            help="% of winning trades where RSI supported the action"
        )
    
    with col3:
        st.metric(
            "🔄 MACD Alignment",
            f"{attribution.get('macd_win_rate', 0):.0f}%", 
            help="% of winning trades where MACD aligned with action"
        )
    
    with col4:
        if attribution.get('social_coverage', 0) > 20:  # Only show if decent coverage
            st.metric(
                "💬 Social Alignment",
                f"{attribution.get('social_win_rate', 0):.0f}%",
                help="% of winning trades where social sentiment aligned"
            )
        else:
            st.metric(
                "💬 Social Coverage", 
                f"{attribution.get('social_coverage', 0):.0f}%",
                help="% of trades with social sentiment data"
            )
    
    # Multi-component analysis
    st.markdown("### 🎯 Multi-Component Signal Strength")
    
    multi_analysis = attribution.get('multi_component_analysis', {})
    if multi_analysis:
        # Create visualization of win rates by component count
        component_data = []
        for key, value in multi_analysis.items():
            component_count = int(key.split('_')[0])
            component_data.append({
                'Components Aligned': component_count,
                'Trades': value['trades'],
                'Win Rate (%)': value['win_rate']
            })
        
        if component_data:
            df_components = pd.DataFrame(component_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart of win rates
                fig = px.bar(
                    df_components,
                    x='Components Aligned',
                    y='Win Rate (%)',
                    title='Win Rate by Component Alignment',
                    text='Win Rate (%)'
                )
                fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Trade count by alignment
                fig2 = px.bar(
                    df_components,
                    x='Components Aligned', 
                    y='Trades',
                    title='Number of Trades by Alignment',
                    text='Trades'
                )
                fig2.update_traces(texttemplate='%{text}', textposition='outside')
                fig2.update_layout(height=300)
                st.plotly_chart(fig2, use_container_width=True)
            
            # Key insights
            best_alignment = df_components.loc[df_components['Win Rate (%)'].idxmax()]
            st.info(
                f"**Key Insight**: {best_alignment['Components Aligned']} components aligned "
                f"shows {best_alignment['Win Rate (%)']:.1f}% win rate "
                f"({best_alignment['Trades']} trades)"
            )
    
    # Summary insights
    with st.expander("📊 Attribution Insights", expanded=False):
        st.markdown(f"""
        **Analysis Period**: Last {attribution['period_days']} days
        
        **Trade Summary:**
        - Total Completed Trades: {attribution['total_trades']}
        - Winning Trades: {attribution['winning_trades']}
        - Overall Win Rate: {attribution['overall_win_rate']:.1f}%
        
        **Component Performance:**
        - News sentiment aligned with {attribution.get('news_win_rate', 0):.0f}% of winners
        - Technical indicators aligned with {attribution.get('tech_win_rate', 0):.0f}% of winners  
        - MACD signals aligned with {attribution.get('macd_win_rate', 0):.0f}% of winners
        - Social data available for {attribution.get('social_coverage', 0):.0f}% of trades
        
        **This shows which components actually contribute to successful outcomes, 
        not just theoretical weights.**
        """)


def render_system_overview(enhanced_metrics: Dict, days_back: int = 14):
    """Render explanatory overview for News, Social, ML, and Technical pillars"""
    overview = compute_overview_metrics(days_back)
    if not overview:
        return

    st.markdown("### 📚 System Component Analysis")
    
    # Create detailed explanations for each component
    col1, col2 = st.columns(2)
    
    with col1:
        with st.expander("📰 News Sentiment - How it Works", expanded=False):
            st.markdown("""
            **Professional News Analysis**
            - Uses FinBERT (Financial BERT) model for accurate financial sentiment
            - Processes headlines from major financial news sources
            - Analyzes earnings reports, market commentary, analyst upgrades/downgrades
            
            **Confidence Scoring**
            - Each news item receives a confidence score (0-1)
            - Higher confidence = more reliable sentiment signal
            - Weighted by news source credibility and content clarity
            
            **Key Metrics:**
            - **Sentiment Score**: -1.0 (very negative) to +1.0 (very positive)
            - **Volume Tracking**: Number of news articles processed
            - **Event Impact**: Special events (earnings, dividends) get higher weights
            
            **Combined Impact**: News sentiment contributes 30% to final trading signals
            """)
        
        with st.expander("🤖 Machine Learning - Model Details", expanded=False):
            st.markdown("""
            **RandomForest Models**
            - Ensemble of 100+ decision trees
            - Handles non-linear relationships in market data
            - Robust against overfitting with built-in feature selection
            
            **LSTM Neural Networks**
            - Long Short-Term Memory networks for sequential data
            - Captures temporal patterns in price movements
            - Learns from historical price and sentiment sequences
            
            **Multi-timeframe Prediction**
            - **1 Hour**: Short-term momentum plays
            - **4 Hour**: Intraday swing trades  
            - **1 Day**: Position trades and overnight holds
            
            **Key Metrics:**
            - **Predictions**: Number of ML evaluations made
            - **Outcomes**: Completed trades with known results
            - **Training Samples**: Historical data points used for training
            - **Success Rate**: 70%+ directional accuracy on backtests
            
            **Combined Impact**: ML models contribute 30% to final trading signals
            """)
    
    with col2:
        with st.expander("📱 Social Sentiment - Community Intelligence", expanded=False):
            st.markdown("""
            **Reddit Discussions**
            - Monitors r/AusFinance, r/ASX_Bets for retail sentiment
            - Natural language processing on discussion threads
            - Filters out spam and identifies genuine market opinions
            
            **MarketAux Integration**
            - Professional social sentiment aggregation service
            - Combines Twitter, Reddit, financial forums
            - Real-time sentiment tracking across social platforms
            
            **Social Media Trends**
            - Hashtag analysis for ASX bank mentions
            - Sentiment momentum tracking
            - Early detection of viral financial content
            
            **Key Metrics:**
            - **Coverage**: Percentage of predictions with social data
            - **Reddit Sentiment**: Average community sentiment (-1 to +1)
            - **Social Volume**: Number of social mentions tracked
            
            **Combined Impact**: Social sentiment contributes 20% to final signals
            """)
        
        with st.expander("📈 Technical Analysis - Market Mechanics", expanded=False):
            st.markdown("""
            **RSI (Relative Strength Index)**
            - Measures overbought (>70) and oversold (<30) conditions
            - 14-period momentum oscillator
            - Key reversal signal when extreme levels reached
            
            **MACD (Moving Average Convergence Divergence)**
            - 12-day EMA minus 26-day EMA with 9-day signal line
            - Bullish when MACD crosses above signal line
            - Measures trend changes and momentum shifts
            
            **Bollinger Bands**
            - 20-period moving average with 2 standard deviation bands
            - Price touching upper band = potential resistance
            - Price touching lower band = potential support
            
            **Moving Averages (SMA 20/50/200)**
            - **SMA20**: Short-term trend (1 month)
            - **SMA50**: Medium-term trend (2.5 months)  
            - **SMA200**: Long-term trend (10 months)
            - Golden Cross (SMA50 > SMA200) = bullish signal
            
            **Volume & Momentum Analysis**
            - Volume spikes confirm price movements
            - Market momentum measures buying/selling pressure
            
            **Combined Impact**: Technical analysis contributes 20% to final signals
            """)
    
    # Enhanced definitions
    with st.expander("📊 Key Terms & Definitions", expanded=False):
        st.markdown("""
        **Trading Metrics:**
        - **Predictions**: ML feature records evaluated (each bank/day combination)
        - **Outcomes**: Completed trades with realized profit/loss
        - **Training Samples**: Historical examples used to train ML models
        - **Win Rate**: Percentage of profitable completed trades
        - **Success Rate**: Model's directional accuracy (up/down/flat prediction)
        
        **Sentiment Scores:**
        - **Range**: -1.0 (very bearish) to +1.0 (very bullish)
        - **Neutral**: -0.1 to +0.1 (no strong directional bias)
        - **Confidence**: 0.0 to 1.0 (model certainty in prediction)
        
        **Combined Signals:**
        - **Strong Buy/Sell**: 3+ indicators align with high confidence
        - **Hold**: Mixed signals or low confidence predictions
        - **Overall Score**: Weighted combination of all four components
        """)

    st.markdown(f"### 📊 Combined System Overview (last {overview['period_days']} days)")
    col_news, col_social, col_ml, col_tech = st.columns(4)

    with col_news:
        st.metric("News Sentiment", f"{overview['news']['avg_sentiment']:.2f}")
        st.caption(f"Confidence: {overview['news']['avg_confidence']:.2f} • News: {overview['news']['total_news']}")
    with col_social:
        st.metric("Social Sentiment", f"{overview['social']['avg_reddit_sentiment']:.2f}")
        st.caption(f"Coverage: {overview['social']['coverage_pct']:.1f}%")
    with col_ml:
        st.metric("ML Success Rate", f"{overview['ml']['direction_accuracy_4h']:.1%}")
        st.caption(f"Pred: {overview['ml']['predictions']} • Outc: {overview['ml']['outcomes_completed']}")
    with col_tech:
        st.metric("Momentum (avg)", f"{overview['technical']['avg_momentum']:.2f}")
        st.caption(f"RSI: {overview['technical']['avg_rsi']:.1f} • SMA20 Δ: {overview['technical']['avg_price_vs_sma20']:.3f}")

    # Enhanced combined interpretation with detailed breakdown
    with st.container():
        st.markdown("### 🎯 Combined Signal Analysis")
        
        try:
            # Calculate component scores
            news_score = max(0.0, min(1.0, (overview['news']['avg_sentiment'] + 1) / 2))
            social_score = max(0.0, min(1.0, (overview['social']['avg_reddit_sentiment'] + 1) / 2)) * (overview['social']['coverage_pct'] / 100 if overview['social']['coverage_pct'] else 0.5)
            ml_score = max(0.0, min(1.0, overview['ml']['direction_accuracy_4h']))
            tech_score = max(0.0, min(1.0, 0.5 + overview['technical']['avg_momentum']))
            
            # Weighted combination (ML and News get higher weights)
            combined = 0.35 * ml_score + 0.30 * news_score + 0.20 * tech_score + 0.15 * social_score
            
            # Determine overall market bias
            if combined >= 0.65:
                label = "🟢 Strong Bullish"
                recommendation = "Consider long positions with high confidence"
            elif combined >= 0.55:
                label = "📈 Bullish"
                recommendation = "Moderate bullish bias - selective long positions"
            elif combined >= 0.45:
                label = "🟡 Neutral"
                recommendation = "Mixed signals - wait for clearer direction"
            elif combined >= 0.35:
                label = "📉 Bearish"
                recommendation = "Moderate bearish bias - defensive positioning"
            else:
                label = "🔴 Strong Bearish"
                recommendation = "Consider short positions or cash holdings"
            
            # Display combined result
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Overall Market Bias", label)
                st.metric("Combined Score", f"{combined:.3f}/1.000")
            
            with col2:
                st.markdown("**Component Contributions:**")
                col_a, col_b, col_c, col_d = st.columns(4)
                with col_a:
                    st.metric("🤖 ML Weight", f"{ml_score:.2f}", delta=f"35% impact")
                with col_b:
                    st.metric("📰 News Weight", f"{news_score:.2f}", delta=f"30% impact")  
                with col_c:
                    st.metric("📈 Tech Weight", f"{tech_score:.2f}", delta=f"20% impact")
                with col_d:
                    st.metric("📱 Social Weight", f"{social_score:.2f}", delta=f"15% impact")
                
                st.info(f"**Trading Insight:** {recommendation}")
            
            # Show signal strength breakdown
            with st.expander("🔍 Detailed Signal Strength Analysis", expanded=False):
                st.markdown("**How the combined score is calculated:**")
                st.markdown(f"""
                - **Machine Learning**: {ml_score:.3f} × 35% = {ml_score * 0.35:.3f}
                - **News Sentiment**: {news_score:.3f} × 30% = {news_score * 0.30:.3f}  
                - **Technical Analysis**: {tech_score:.3f} × 20% = {tech_score * 0.20:.3f}
                - **Social Sentiment**: {social_score:.3f} × 15% = {social_score * 0.15:.3f}
                
                **Total Combined Score**: {combined:.3f}
                
                **Signal Strength Ranges:**
                - 0.65+ = Strong Bullish (High conviction trades)
                - 0.55-0.64 = Bullish (Moderate long bias) 
                - 0.45-0.54 = Neutral (Wait for better signals)
                - 0.35-0.44 = Bearish (Moderate short bias)
                - <0.35 = Strong Bearish (High conviction defensive)
                """)
                
                # Show recent performance context
                if overview['ml']['outcomes_completed'] > 0:
                    st.markdown(f"""
                    **Recent Performance Context:**
                    - ML Success Rate: {overview['ml']['direction_accuracy_4h']:.1%}
                    - Win Rate: {overview['ml']['win_rate']:.1%} 
                    - Average Return: {overview['ml']['avg_return']*100:.1f}%
                    - Predictions Made: {overview['ml']['predictions']}
                    - Completed Outcomes: {overview['ml']['outcomes_completed']}
                    """)
        
        except Exception as e:
            st.warning(f"Could not calculate combined signals: {e}")

# ============================================================================
# STREAMLINED DASHBOARD SECTIONS
# ============================================================================

def render_streamlined_ml_summary():
    """
    ENHANCED: ML Summary with progress timeline, component attribution, and improved positions table
    """
    st.subheader("🤖 ML Trading System Summary")
    
    # Get ML metrics
    try:
        enhanced_metrics = fetch_enhanced_ml_training_metrics()
    except Exception as e:
        st.error(f"Could not load ML metrics: {e}")
        return
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    if enhanced_metrics:
        with col1:
            status = enhanced_metrics['status']
            status_colors = {'EXCELLENT': '🟢', 'GOOD': '🟡', 'NEEDS_IMPROVEMENT': '🟠', 'NO_DATA': '🔴'}
            st.metric("System Status", f"{status_colors.get(status, '⚪')} {status}")
        
        with col2:
            st.metric("Success Rate", f"{enhanced_metrics['direction_accuracy_4h']:.1%}")
        
        with col3:
            st.metric("Training Samples", f"{enhanced_metrics.get('training_samples', 0)}")
        
        with col4:
            last = enhanced_metrics.get('last_training')
            if last:
                # Parse timestamp and show relative time
                try:
                    from datetime import datetime
                    last_dt = datetime.fromisoformat(last.replace('Z', '+00:00').replace('T', ' '))
                    hours_ago = (datetime.now() - last_dt).total_seconds() / 3600
                    if hours_ago < 24:
                        time_str = f"{hours_ago:.1f}h ago"
                    else:
                        time_str = f"{hours_ago/24:.1f}d ago"
                except:
                    time_str = "Recent"
            else:
                time_str = "N/A"
            st.metric("Last Training", time_str)

    # NEW: ML Progress Timeline (Priority #3 from upgrade guide)
    render_ml_progress_timeline()
    
    # NEW: Component Attribution Analysis (Priority #2 from upgrade guide)  
    render_component_attribution()
    
    # Enhanced explanatory overview with actual performance data
    render_system_overview(enhanced_metrics, days_back=14)
    
    # Master positions table (Priority #4 from upgrade guide)
    st.markdown("### 📊 Master Trading Positions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        days_back = st.selectbox("Time Period", [7, 14, 30, 60, 90], index=2, help="Number of days to look back")
    with col2:
        show_completed_only = st.checkbox("Completed trades only", value=False, help="Show only trades with outcomes")
    with col3:
        exclude_holds = st.checkbox("Exclude HOLD positions", value=True, help="Filter out HOLD positions")
    
    try:
        conn = get_database_connection()
        
        # Enhanced query with component data (from upgrade guide recommendations)
        symbols_list = ",".join([f"'{s}'" for s in ASX_BANKS])
        where_clauses = [
            f"ef.timestamp >= datetime('now', '-{days_back} days')",
            f"ef.symbol IN ({symbols_list})"
        ]
        if show_completed_only:
            where_clauses.append("eo.return_pct IS NOT NULL")
        if exclude_holds:
            where_clauses.append("COALESCE(eo.optimal_action, 'ANALYZE') != 'HOLD'")
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
        SELECT 
            ef.symbol,
            ef.timestamp as signal_date,
            COALESCE(eo.optimal_action, 'ANALYZE') as ml_action,
            COALESCE(eo.confidence_score, ef.confidence, 0.5) as confidence,
            COALESCE(eo.entry_price, ef.current_price) as entry_price,
            eo.exit_price_1d,
            eo.return_pct,
            ef.current_price,
            ef.sentiment_score,
            ef.rsi,
            ef.macd_line,
            ef.reddit_sentiment,
            -- Component alignment flags
            CASE WHEN ef.sentiment_score > 0.1 AND eo.optimal_action = 'BUY' THEN '✓'
                 WHEN ef.sentiment_score < -0.1 AND eo.optimal_action = 'SELL' THEN '✓'
                 ELSE '✗' END as news_signal,
            CASE WHEN ef.rsi < 35 AND eo.optimal_action = 'BUY' THEN '✓'
                 WHEN ef.rsi > 65 AND eo.optimal_action = 'SELL' THEN '✓'
                 ELSE '✗' END as tech_signal,
            CASE WHEN ef.macd_line > 0 AND eo.optimal_action = 'BUY' THEN '✓'
                 WHEN ef.macd_line < 0 AND eo.optimal_action = 'SELL' THEN '✓'
                 ELSE '✗' END as macd_signal,
            CASE WHEN ef.reddit_sentiment > 0.1 AND eo.optimal_action = 'BUY' THEN '✓'
                 WHEN ef.reddit_sentiment < -0.1 AND eo.optimal_action = 'SELL' THEN '✓'
                 WHEN ef.reddit_sentiment IS NULL THEN '-'
                 ELSE '✗' END as social_signal
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE {where_sql}
        ORDER BY ef.timestamp DESC
        """
        
        df_positions = pd.read_sql_query(query, conn)
        conn.close()

        # Apply the simplified position status logic (Priority #1 from upgrade guide)
        if not df_positions.empty:
            def get_position_status(row):
                """Clear, simple position status as recommended in upgrade guide"""
                
                # If no entry price → Prediction only
                if pd.isnull(row.get('entry_price')) or row.get('entry_price') == 0:
                    return None, 'PREDICTION', '🔮'
                
                # If has return_pct → Closed position
                if pd.notnull(row.get('return_pct')):
                    try:
                        return_val = float(row['return_pct'])
                        status_icon = '✅' if return_val > 0 else '❌'
                        return return_val, 'CLOSED', status_icon
                    except (ValueError, TypeError):
                        return None, 'CLOSED', '⚪'
                
                # If has entry but no return → Active position
                if pd.notnull(row.get('current_price')):
                    try:
                        entry_p = float(row['entry_price'])
                        current_p = float(row['current_price'])
                        unrealized = (current_p - entry_p) / entry_p
                        return unrealized, 'ACTIVE', f"🔄"
                    except (ValueError, TypeError, ZeroDivisionError):
                        return None, 'ACTIVE', '🔄'
                
                return None, 'UNKNOWN', '❓'
            
            # Apply processing to each row using the new simplified status logic
            processed_data = df_positions.apply(get_position_status, axis=1)
            df_positions['calculated_return'] = [x[0] for x in processed_data]
            df_positions['position_status_detailed'] = [x[1] for x in processed_data]
            df_positions['status_icon'] = [x[2] for x in processed_data]
            
            # Format and display the positions table
            display_positions = df_positions.copy()
            
            # Format timestamps
            display_positions['entry_time'] = pd.to_datetime(display_positions['signal_date']).dt.strftime('%m-%d %H:%M')
            
            # Format prices (safely handle non-numeric values)
            for col in ['entry_price', 'current_price']:
                if col in display_positions.columns:
                    def safe_format_price(x):
                        try:
                            if pd.notna(x):
                                val = float(x)
                                return f"${val:.2f}"
                            return "N/A"
                        except (ValueError, TypeError):
                            return "N/A"
                    
                    display_positions[col] = display_positions[col].apply(safe_format_price)
            
            # Format confidence (safely handle non-numeric values)
            if 'confidence' in display_positions.columns:
                def safe_format_confidence(x):
                    try:
                        if pd.notna(x):
                            val = float(x)
                            return f"{val*100:.1f}%"
                        return "N/A"
                    except (ValueError, TypeError):
                        return "N/A"
                
                display_positions['confidence'] = display_positions['confidence'].apply(safe_format_confidence)
            
            # Format returns with proper status indicators
            def format_return_with_status(row):
                status = row.get('position_status_detailed', 'UNKNOWN')
                ret = row.get('calculated_return')
                
                if status == 'PENDING':
                    return "📊 Prediction Only"
                elif status == 'ACTIVE':
                    if pd.notna(ret):
                        ret_pct = ret * 100
                        if ret_pct > 1:
                            return f"🔄 +{ret_pct:.1f}% (Unrealized)"
                        elif ret_pct < -1:
                            return f"🔄 {ret_pct:.1f}% (Unrealized)"
                        else:
                            return f"🔄 {ret_pct:.1f}% (Unrealized)"
                    return "🔄 Active Position"
                elif status == 'COMPLETED':
                    if pd.notna(ret):
                        ret_pct = ret * 100
                        if ret_pct > 0.1:
                            return f"✅ +{ret_pct:.1f}%"
                        elif ret_pct < -0.1:
                            return f"❌ {ret_pct:.1f}%"
                        else:
                            return f"⚪ {ret_pct:.1f}%"
                    return "⚪ Completed"
                return "❓ Unknown"
            
            display_positions['status'] = display_positions.apply(format_return_with_status, axis=1)
            
            # Fix exit price display - show N/A for active positions, actual exit price for completed
            def format_exit_price(row):
                status = row.get('position_status_detailed', 'UNKNOWN')
                exit_price = row.get('exit_price_1d')
                
                if status == 'COMPLETED' and pd.notna(exit_price):
                    # Robustly handle numeric or already-formatted strings
                    try:
                        val = float(str(exit_price).replace('$', '').replace(',', '').strip())
                        return f"${val:.2f}"
                    except Exception:
                        return str(exit_price) if pd.notna(exit_price) else "N/A"
                elif status == 'ACTIVE':
                    return "Active"
                elif status == 'PENDING':
                    return "No Position"
                else:
                    return "N/A"
            
            display_positions['exit_price_formatted'] = display_positions.apply(format_exit_price, axis=1)
            
            # Format sentiment scores
            if 'sentiment_score' in display_positions.columns:
                display_positions['sentiment'] = display_positions['sentiment_score'].apply(
                    lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
                )
            
            # Format RSI with signals
            if 'rsi' in display_positions.columns:
                def format_rsi(rsi):
                    if pd.notna(rsi):
                        if rsi > 70:
                            return f"🔴 {rsi:.1f}"
                        elif rsi < 30:
                            return f"🟢 {rsi:.1f}"
                        else:
                            return f"🟡 {rsi:.1f}"
                    return "N/A"
                display_positions['rsi_signal'] = display_positions['rsi'].apply(format_rsi)
            
            # Select and rename columns for display
            display_cols = ['symbol', 'entry_time', 'ml_action', 'confidence', 'entry_price']
            col_names = ['Bank', 'Entry Time', 'ML Action', 'Confidence', 'Entry Price']
            
            # Use formatted exit price instead of raw exit_price_1d
            if 'exit_price_formatted' in display_positions.columns:
                display_cols.append('exit_price_formatted')
                col_names.append('Exit Price')
            
            if 'current_price' in display_positions.columns:
                display_cols.append('current_price')
                col_names.append('Current Price')
            
            if 'status' in display_positions.columns:
                display_cols.append('status')
                col_names.append('Return/Status')
            
            if 'sentiment' in display_positions.columns:
                display_cols.append('sentiment')
                col_names.append('Sentiment')
            
            if 'rsi_signal' in display_positions.columns:
                display_cols.append('rsi_signal')
                col_names.append('RSI Signal')
            
            final_display = display_positions[display_cols]
            final_display.columns = col_names
            
            # Add enhanced summary stats based on position status
            if len(display_positions) > 0:
                total_records = len(display_positions)
                
                # Count by status type
                completed = (display_positions['position_status_detailed'] == 'COMPLETED').sum()
                active = (display_positions['position_status_detailed'] == 'ACTIVE').sum()
                pending = (display_positions['position_status_detailed'] == 'PENDING').sum()
                
                # Calculate win rate from completed positions only
                win_rate = 0
                avg_return = 0
                if completed > 0:
                    completed_returns = display_positions[
                        display_positions['position_status_detailed'] == 'COMPLETED'
                    ]['calculated_return']
                    wins = (completed_returns > 0).sum()
                    win_rate = (wins / completed) * 100
                    avg_return = completed_returns.mean() * 100
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", total_records)
                    st.caption(f"Predictions + Positions")
                with col2:
                    st.metric("Position Status", f"📊{pending} 🔄{active} ✅{completed}")
                    st.caption("Pending | Active | Completed")
                with col3:
                    if completed > 0:
                        st.metric("Win Rate", f"{win_rate:.1f}%")
                        st.caption(f"From {completed} completed trades")
                    else:
                        st.metric("Win Rate", "N/A")
                        st.caption("No completed trades yet")
                with col4:
                    if completed > 0:
                        st.metric("Avg Return", f"{avg_return:.1f}%")
                        st.caption("Completed trades only")
                    else:
                        st.metric("Avg Return", "N/A") 
                        st.caption("No completed trades yet")
            
            st.dataframe(final_display, use_container_width=True, hide_index=True)
            
            # Add explanation for position statuses
            with st.expander("📋 Position Status Guide", expanded=False):
                st.markdown("""
                **Understanding Position Types:**
                
                **📊 Prediction Only** - ML analysis generated but no actual position taken
                - Exit Price: "No Position" 
                - Status: Shows this is just a prediction/recommendation
                
                **🔄 Active Position** - Real position currently held
                - Exit Price: "Active" (position still open)
                - Status: Shows unrealized P&L based on current market price
                - These update in real-time as market prices change
                
                **✅/❌ Completed Position** - Position closed with final outcome  
                - Exit Price: Actual exit price from when position was closed
                - Status: Final realized return (profit/loss)
                - These are historical and don't change
                
                **Why some positions show "N/A" for exit prices:**
                - Recent predictions (like Aug 8th) are just ML recommendations
                - The system generates predictions but doesn't automatically execute trades
                - Only when a trade is actually executed do you get entry/exit prices
                - Some older entries may be data processing artifacts
                
                **Return Calculation Logic:**
                - **Completed**: Uses actual entry/exit prices from trade execution
                - **Active**: Calculates unrealized return vs current market price  
                - **Prediction Only**: No return calculation (no position held)
                """)
        else:
            st.info("No positions found for the selected filters.")
            
    except Exception as e:
        st.error(f"Error loading positions: {e}")


def render_streamlined_sentiment_metrics():
    """
    STREAMLINED: Important sentiment metrics only
    """
    st.subheader("📊 Sentiment Analysis Overview")
    
    try:
        sentiment_df = fetch_current_sentiment_scores()
        
        if sentiment_df.empty:
            st.warning("No sentiment data available")
            return
        
        # Key sentiment metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_sentiment = sentiment_df['sentiment_score'].mean()
            sentiment_emoji = "📈" if avg_sentiment > 0.1 else "📉" if avg_sentiment < -0.1 else "➡️"
            st.metric("Overall Sentiment", f"{sentiment_emoji} {avg_sentiment:.2f}")
        
        with col2:
            avg_confidence = sentiment_df['confidence'].mean()
            st.metric("Avg Confidence", f"{avg_confidence:.1%}")
        
        with col3:
            total_news = sentiment_df['news_count'].sum()
            st.metric("News Articles", f"{int(total_news)}")
        
        with col4:
            volatile_stocks = (sentiment_df['volatility_20d'] > sentiment_df['volatility_20d'].quantile(0.7)).sum()
            st.metric("High Volatility", f"{volatile_stocks} stocks")
        
        # Sentiment by symbol
        st.markdown("### 🏦 Bank Sentiment Breakdown")
        
        # Create a clean summary table
        summary_df = sentiment_df.copy()
        summary_df['sentiment_direction'] = summary_df['sentiment_score'].apply(
            lambda x: "🟢 Bullish" if x > 0.1 else "🔴 Bearish" if x < -0.1 else "🟡 Neutral"
        )
        summary_df['confidence_pct'] = (summary_df['confidence'] * 100).round(1).astype(str) + '%'
        summary_df['sentiment_score'] = summary_df['sentiment_score'].round(3)
        
        display_df = summary_df[['symbol', 'sentiment_direction', 'sentiment_score', 'confidence_pct', 'news_count']]
        display_df.columns = ['Bank', 'Direction', 'Score', 'Confidence', 'News Count']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Could not load sentiment data: {e}")


def render_streamlined_news_sentiment():
    """
    STREAMLINED: News sentiment important metrics
    """
    st.subheader("📰 News Sentiment Analysis")
    
    try:
        conn = get_database_connection()
        
        # Get recent news sentiment data
        query = """
        SELECT 
            symbol,
            sentiment_score,
            confidence,
            news_count,
            timestamp
        FROM enhanced_features
        WHERE timestamp >= datetime('now', '-7 days')
        AND news_count > 0
        ORDER BY timestamp DESC
        """
        
        news_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if news_df.empty:
            st.warning("No news sentiment data available")
            return
        
        # Key news metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_articles = news_df['news_count'].sum()
            st.metric("Total Articles (7d)", f"{int(total_articles)}")
        
        with col2:
            avg_news_sentiment = news_df['sentiment_score'].mean()
            news_trend = "📈" if avg_news_sentiment > 0 else "📉" if avg_news_sentiment < 0 else "➡️"
            st.metric("News Trend", f"{news_trend} {avg_news_sentiment:.2f}")
        
        with col3:
            high_impact_news = (news_df['confidence'] > 0.7).sum()
            st.metric("High Impact News", f"{high_impact_news}")
        
        with col4:
            latest_update = news_df['timestamp'].max()
            hours_ago = (pd.Timestamp.now() - pd.to_datetime(latest_update)).total_seconds() / 3600
            update_str = f"{hours_ago:.1f}h ago" if hours_ago < 24 else f"{hours_ago/24:.1f}d ago"
            st.metric("Last Update", update_str)
        
        # News volume chart
        st.markdown("### 📈 News Volume Trend (7 Days)")
        daily_news = news_df.groupby(news_df['timestamp'].str[:10])['news_count'].sum().reset_index()
        daily_news.columns = ['Date', 'Articles']
        
        fig = px.bar(daily_news, x='Date', y='Articles', title='Daily News Article Volume')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Could not load news sentiment data: {e}")


def render_streamlined_social_sentiment():
    """
    STREAMLINED: Social sentiment important metrics  
    """
    st.subheader("📱 Social Sentiment Analysis")
    
    try:
        conn = get_database_connection()
        
        # Get recent social sentiment data
        query = """
        SELECT 
            symbol,
            reddit_sentiment,
            sentiment_score,
            timestamp
        FROM enhanced_features
        WHERE timestamp >= datetime('now', '-7 days')
        AND reddit_sentiment IS NOT NULL
        ORDER BY timestamp DESC
        """
        
        social_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if social_df.empty:
            st.warning("No social sentiment data available")
            return
        
        # Key social metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_reddit = social_df['reddit_sentiment'].mean()
            reddit_trend = "📈" if avg_reddit > 0.1 else "📉" if avg_reddit < -0.1 else "➡️"
            st.metric("Reddit Sentiment", f"{reddit_trend} {avg_reddit:.2f}")
        
        with col2:
            social_vs_news_corr = social_df[['reddit_sentiment', 'sentiment_score']].corr().iloc[0,1]
            st.metric("News-Social Sync", f"{social_vs_news_corr:.2f}")
        
        with col3:
            volatile_social = (social_df['reddit_sentiment'].std() > 0.3).sum() if len(social_df) > 1 else 0
            st.metric("Social Volatility", "High" if volatile_social > 0 else "Low")
        
        with col4:
            social_entries = len(social_df)
            st.metric("Social Data Points", f"{social_entries}")
        
        # Social vs News comparison
        st.markdown("### 📊 Social vs News Sentiment")
        
        comparison_df = social_df.groupby('symbol').agg({
            'reddit_sentiment': 'mean',
            'sentiment_score': 'mean'
        }).round(3).reset_index()
        
        comparison_df.columns = ['Bank', 'Social Sentiment', 'News Sentiment']
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Could not load social sentiment data: {e}")


def render_streamlined_technical_analysis():
    """
    STREAMLINED: Technical analysis important metrics
    """
    st.subheader("📈 Technical Analysis Overview")
    
    try:
        conn = get_database_connection()
        
        # Get recent technical data
        query = """
        SELECT 
            symbol,
            rsi,
            macd_line,
            price_vs_sma20,
            volatility_20d,
            current_price,
            timestamp
        FROM enhanced_features
        WHERE timestamp >= datetime('now', '-1 days')
        ORDER BY timestamp DESC
        LIMIT 7
        """
        
        tech_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if tech_df.empty:
            st.warning("No technical analysis data available")
            return
        
        # Key technical metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_rsi = tech_df['rsi'].mean()
            rsi_signal = "🔴 Overbought" if avg_rsi > 70 else "🟢 Oversold" if avg_rsi < 30 else "🟡 Neutral"
            st.metric("Avg RSI", f"{rsi_signal} ({avg_rsi:.1f})")
        
        with col2:
            bullish_macd = (tech_df['macd_line'] > 0).sum()
            st.metric("Bullish MACD", f"{bullish_macd}/{len(tech_df)} banks")
        
        with col3:
            above_sma = (tech_df['price_vs_sma20'] > 0).sum()
            st.metric("Above SMA20", f"{above_sma}/{len(tech_df)} banks")
        
        with col4:
            high_vol = (tech_df['volatility_20d'] > tech_df['volatility_20d'].quantile(0.7)).sum()
            st.metric("High Volatility", f"{high_vol} banks")
        
        # Technical signals table
        st.markdown("### 🎯 Technical Signals by Bank")
        
        # Create technical signals
        def get_technical_signal(row):
            signals = []
            if row['rsi'] > 70:
                signals.append("🔴 RSI High")
            elif row['rsi'] < 30:
                signals.append("🟢 RSI Low")
            else:
                signals.append("🟡 RSI Mid")
            
            if row['macd_line'] > 0:
                signals.append("📈 MACD+")
            else:
                signals.append("📉 MACD-")
                
            if row['price_vs_sma20'] > 0.02:
                signals.append("⬆️ Above SMA")
            elif row['price_vs_sma20'] < -0.02:
                signals.append("⬇️ Below SMA")
            else:
                signals.append("➡️ Near SMA")
                
            return " | ".join(signals)
        
        tech_df['technical_signals'] = tech_df.apply(get_technical_signal, axis=1)
        tech_df['rsi'] = tech_df['rsi'].round(1)
        tech_df['current_price'] = tech_df['current_price'].round(2)
        tech_df['volatility_20d'] = (tech_df['volatility_20d'] * 100).round(1).astype(str) + '%'
        
        display_df = tech_df[['symbol', 'current_price', 'rsi', 'volatility_20d', 'technical_signals']]
        display_df.columns = ['Bank', 'Price', 'RSI', 'Volatility', 'Signals']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    except Exception as e:
        st.error(f"Could not load technical analysis data: {e}")


def render_streamlined_next_day_predictions():
    """
    STREAMLINED: Next Day Predictions with key insights
    """
    st.subheader("🔮 Next Day Predictions")
    
    try:
        conn = get_database_connection()
        
        # Get latest prediction data for each bank
        query = """
        SELECT 
            ef.symbol,
            ef.sentiment_score,
            ef.confidence,
            ef.rsi,
            eo.optimal_action,
            eo.confidence_score as ml_confidence,
            eo.price_direction_1d,
            eo.price_magnitude_1d,
            ef.current_price,
            ef.timestamp
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.id IN (
            SELECT MAX(id) FROM enhanced_features 
            WHERE symbol IN ('CBA.AX', 'ANZ.AX', 'WBC.AX', 'NAB.AX', 'MQG.AX', 'QBE.AX', 'SUN.AX')
            GROUP BY symbol
        )
        ORDER BY ef.symbol
        """
        
        predictions_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if predictions_df.empty:
            st.warning("No prediction data available")
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            buy_signals = (predictions_df['optimal_action'] == 'BUY').sum()
            st.metric("Buy Signals", f"{buy_signals}/{len(predictions_df)}")
        
        with col2:
            sell_signals = (predictions_df['optimal_action'] == 'SELL').sum()
            st.metric("Sell Signals", f"{sell_signals}/{len(predictions_df)}")
        
        with col3:
            high_conf_predictions = (predictions_df['ml_confidence'] > 0.7).sum()
            st.metric("High Confidence", f"{high_conf_predictions}")
        
        with col4:
            bullish_sentiment = (predictions_df['sentiment_score'] > 0.1).sum()
            st.metric("Bullish Sentiment", f"{bullish_sentiment}")
        
        # Predictions table
        st.markdown("### 🎯 Individual Bank Predictions")
        
        # Create prediction summary
        def create_prediction_summary(row):
            # Combine all factors into a prediction strength
            factors = []
            
            # Sentiment factor
            sentiment = row['sentiment_score'] or 0
            if sentiment > 0.1:
                factors.append("📈 Positive News")
            elif sentiment < -0.1:
                factors.append("📉 Negative News")
            
            # Technical factor
            rsi = row['rsi'] or 50
            if rsi > 70:
                factors.append("🔴 Overbought")
            elif rsi < 30:
                factors.append("🟢 Oversold")
            
            # ML factor
            if row['ml_confidence'] and row['ml_confidence'] > 0.6:
                factors.append(f"🤖 {row['optimal_action']}")
            
            return " | ".join(factors) if factors else "🟡 Neutral"
        
        predictions_df['prediction_summary'] = predictions_df.apply(create_prediction_summary, axis=1)
        predictions_df['ml_confidence_pct'] = (predictions_df['ml_confidence'] * 100).round(1).astype(str) + '%'
        predictions_df['sentiment_score'] = predictions_df['sentiment_score'].round(3)
        predictions_df['current_price'] = predictions_df['current_price'].round(2)
        
        # Expected price direction
        predictions_df['price_outlook'] = predictions_df.apply(lambda row: 
            f"📈 +{row['price_magnitude_1d']:.1%}" if row['price_direction_1d'] == 'UP' 
            else f"📉 -{row['price_magnitude_1d']:.1%}" if row['price_direction_1d'] == 'DOWN' 
            else "➡️ Flat" if row['price_direction_1d'] else "❓ Unknown", axis=1
        )
        
        display_df = predictions_df[[
            'symbol', 'optimal_action', 'ml_confidence_pct', 'price_outlook', 
            'current_price', 'prediction_summary'
        ]]
        display_df.columns = [
            'Bank', 'ML Action', 'Confidence', 'Price Outlook', 'Current Price', 'Key Factors'
        ]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Action recommendations
        with st.expander("🚀 Action Recommendations", expanded=False):
            high_conf_buys = predictions_df[
                (predictions_df['optimal_action'] == 'BUY') & 
                (predictions_df['ml_confidence'] > 0.7)
            ]
            
            high_conf_sells = predictions_df[
                (predictions_df['optimal_action'] == 'SELL') & 
                (predictions_df['ml_confidence'] > 0.7)
            ]
            
            if not high_conf_buys.empty:
                st.markdown("**🟢 Strong Buy Candidates:**")
                for _, stock in high_conf_buys.iterrows():
                    st.write(f"• **{stock['symbol']}** - {stock['ml_confidence_pct']} confidence - {stock['prediction_summary']}")
            
            if not high_conf_sells.empty:
                st.markdown("**🔴 Strong Sell Candidates:**")
                for _, stock in high_conf_sells.iterrows():
                    st.write(f"• **{stock['symbol']}** - {stock['ml_confidence_pct']} confidence - {stock['prediction_summary']}")
            
            if high_conf_buys.empty and high_conf_sells.empty:
                st.info("No high-confidence trading signals at this time. Monitor for changes.")
        
    except Exception as e:
        st.error(f"Could not load predictions: {e}")


def render_unified_positions_area():
    """
    STREAMLINED: ML Predictions & Backtesting Results Display
    """
    st.subheader("🎯 ML Trading Predictions & Results")
    
    # Explanation section
    with st.expander("📋 Understanding This Data", expanded=False):
        st.markdown("""
        **What You're Seeing:**
        
        **📊 ML Predictions** - Machine Learning analysis generates trading signals (BUY/SELL/HOLD) based on:
        - 📰 **News Sentiment** (30% weight) - FinBERT analysis of financial news
        - 🤖 **ML Models** (35% weight) - RandomForest + LSTM ensemble predictions  
        - 📈 **Technical Analysis** (20% weight) - RSI, MACD, Bollinger Bands
        - 💬 **Social Sentiment** (15% weight) - Reddit financial discussions
        
        **Prediction Outcomes:**
        - **📊 Prediction Only** - Recent ML analysis, outcome pending
        - **✅ Strong Win (+5%+)** - Backtested prediction achieved >5% return
        - **🟢 Small Win** - Backtested prediction achieved 0-5% return
        - **🔴 Small Loss** - Backtested prediction lost 0-5%
        - **❌ Strong Loss (-5%+)** - Backtested prediction lost >5%
        
        **Note:** These are ML backtesting results, not live trading positions. Entry/Exit prices show historical price points used for performance validation.
        """)
        
    
    try:
        conn = get_database_connection()
        
        # Get comprehensive ML predictions and backtested results
        query = """
        SELECT 
            ef.symbol,
            ef.timestamp,
            
            -- All sentiment metrics
            ef.sentiment_score as news_sentiment,
            ef.confidence as news_confidence,
            ef.reddit_sentiment as social_sentiment,
            
            -- Technical metrics
            ef.rsi,
            ef.macd_line,
            ef.price_vs_sma20,
            ef.current_price,
            ef.volatility_20d,
            
            -- ML predictions
            eo.optimal_action as ml_action,
            eo.confidence_score as ml_confidence,
            eo.price_direction_1d as ml_direction,
            
            -- Backtested position results (use best available exit price)
            eo.entry_price,
            COALESCE(eo.exit_price_1d, eo.exit_price_4h, eo.exit_price_1h) as exit_price,
            eo.return_pct,
            
            -- Position categorization (these are all ML backtested predictions)
            CASE 
                WHEN eo.return_pct IS NULL THEN '📊 Prediction Only'
                WHEN eo.return_pct > 0.05 THEN '✅ Strong Win (+5%+)'
                WHEN eo.return_pct > 0 THEN '🟢 Small Win'
                WHEN eo.return_pct < -0.05 THEN '❌ Strong Loss (-5%+)'
                WHEN eo.return_pct < 0 THEN '🔴 Small Loss'
                ELSE '⚪ Break-even'
            END as prediction_outcome
            
        FROM enhanced_features ef
        LEFT JOIN enhanced_outcomes eo ON ef.id = eo.feature_id
        WHERE ef.timestamp >= datetime('now', '-14 days')
        ORDER BY ef.timestamp DESC
        LIMIT 50
        """
        
        unified_df = pd.read_sql_query(query, conn)
        conn.close()
        
        if unified_df.empty:
            st.warning("No unified position data available")
            return
        
        # Summary metrics for ML backtesting results
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            predictions_only = (unified_df['prediction_outcome'] == '📊 Prediction Only').sum()
            total_predictions = len(unified_df)
            st.metric("Total ML Predictions", f"{total_predictions}", f"{predictions_only} pending outcome")
        
        with col2:
            winning_predictions = unified_df['prediction_outcome'].str.contains('Win', na=False).sum()
            completed_predictions = (unified_df['return_pct'].notna()).sum()
            success_rate = (winning_predictions / completed_predictions * 100) if completed_predictions > 0 else 0
            st.metric("ML Success Rate", f"{success_rate:.1f}%", f"{winning_predictions}/{completed_predictions}")
        
        with col3:
            if unified_df['ml_confidence'].notna().any():
                avg_ml_confidence = unified_df['ml_confidence'].mean()
                if pd.notna(avg_ml_confidence):
                    st.metric("Avg ML Confidence", f"{avg_ml_confidence:.1%}")
                else:
                    st.metric("Avg ML Confidence", "N/A")
            else:
                st.metric("Avg ML Confidence", "N/A")
        
        with col4:
            if unified_df['return_pct'].notna().any():
                avg_return = unified_df['return_pct'].mean() * 100
                if pd.notna(avg_return):
                    st.metric("Avg Return", f"{avg_return:.2f}%")
                else:
                    st.metric("Avg Return", "N/A")
            else:
                st.metric("Avg Return", "N/A")
        
        # ML Predictions & Backtesting Results
        st.markdown("### 📊 ML Predictions & Backtesting Results")
        
        # Create combined signal strength
        def calculate_signal_strength(row):
            strength = 0
            signals = []
            
            # News sentiment strength
            if abs(row['news_sentiment'] or 0) > 0.1:
                strength += 1
                sentiment_dir = "📈" if row['news_sentiment'] > 0 else "📉"
                signals.append(f"{sentiment_dir} News")
            
            # Technical strength
            if (row['rsi'] or 0) > 70 or (row['rsi'] or 0) < 30:
                strength += 1
                rsi_signal = "🔴" if row['rsi'] > 70 else "🟢"
                signals.append(f"{rsi_signal} RSI")
            
            # ML strength
            if (row['ml_confidence'] or 0) > 0.7:
                strength += 1
                signals.append("🤖 ML")
            
            return f"{strength}/3 - {' '.join(signals[:3])}" if signals else f"{strength}/3"
        
        unified_df['combined_strength'] = unified_df.apply(calculate_signal_strength, axis=1)
        unified_df['timestamp'] = pd.to_datetime(unified_df['timestamp']).dt.strftime('%m-%d %H:%M')
        unified_df['current_price'] = unified_df['current_price'].round(2)
        unified_df['news_sentiment'] = unified_df['news_sentiment'].round(3)
        unified_df['rsi'] = unified_df['rsi'].round(1)
        
        # Format prices and returns for display (safe formatting)
        def safe_format_price_display(x):
            try:
                if pd.notna(x):
                    return f"${float(x):.2f}"
                return "N/A"
            except (ValueError, TypeError):
                return "N/A"
        
        def safe_format_return_display(x):
            try:
                if pd.notna(x):
                    return f"{float(x)*100:.2f}%"
                return "N/A"
            except (ValueError, TypeError):
                return "N/A"
        
        unified_df['entry_display'] = unified_df['entry_price'].apply(safe_format_price_display)
        unified_df['exit_display'] = unified_df['exit_price'].apply(safe_format_price_display)
        unified_df['return_display'] = unified_df['return_pct'].apply(safe_format_return_display)
        
        display_df = unified_df[[
            'symbol', 'timestamp', 'ml_action', 'combined_strength', 
            'entry_display', 'exit_display', 'return_display', 'prediction_outcome'
        ]]
        display_df.columns = [
            'Bank', 'Prediction Time', 'ML Action', 'Signal Strength', 
            'Entry Price', 'Exit Price', 'Return', 'Outcome'
        ]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # ML Performance Insights
        with st.expander("🔍 ML Prediction Insights", expanded=False):
            # Best performing predictions
            strong_wins = unified_df[unified_df['prediction_outcome'].str.contains('Strong Win', na=False)]
            if not strong_wins.empty:
                st.markdown("**🎯 Best ML Predictions (>5% return):**")
                for _, pos in strong_wins.head(3).iterrows():
                    try:
                        return_pct = pos['return_pct'] * 100 if pd.notna(pos['return_pct']) else 0
                        symbol = pos['symbol'] or 'Unknown'
                        action = pos['ml_action'] or 'N/A'
                        st.write(f"• **{symbol}**: {action} → {return_pct:.1f}% return")
                    except (ValueError, TypeError):
                        st.write(f"• **{pos['symbol']}**: Data error")
            
            # Recent predictions awaiting results
            pending_predictions = unified_df[unified_df['prediction_outcome'] == '📊 Prediction Only']
            if not pending_predictions.empty:
                st.markdown(f"**📊 Recent Predictions Awaiting Results:** {len(pending_predictions)} predictions")
                
            # Performance by action type
            completed_with_action = unified_df[
                (unified_df['return_pct'].notna()) & 
                (unified_df['ml_action'].notna())
            ]
            if not completed_with_action.empty:
                action_performance = completed_with_action.groupby('ml_action')['return_pct'].mean() * 100
                st.markdown("**📈 Performance by ML Action:**")
                for action, avg_return in action_performance.items():
                    if action and pd.notna(avg_return):  # Extra safety check
                        try:
                            action_str = str(action) if action else 'Unknown'
                            return_val = float(avg_return)
                            st.write(f"• **{action_str}**: {return_val:.2f}% average return")
                        except (ValueError, TypeError):
                            st.write(f"• **{str(action)}**: Data error")
        
    except Exception as e:
        st.error(f"Could not load unified positions: {e}")


def main():
    """
    Main dashboard application - Streamlined version
    """
    # Page configuration
    st.set_page_config(
        page_title="ASX Banks Trading Dashboard - Streamlined",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Header
    st.title("📊 ASX Banks Trading Dashboard - Streamlined")
    st.markdown("**Real-time sentiment analysis and ML predictions for Australian bank stocks**")
    st.markdown("---")
    
    # Auto-refresh info
    st.sidebar.header("Dashboard Info")
    st.sidebar.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.write(f"**Data Source:** {DATABASE_PATH}")
    st.sidebar.write(f"**Banks Tracked:** {len(ASX_BANKS)}")
    
    if st.sidebar.button("🔄 Refresh Data"):
        # Clear Streamlit cache
        st.cache_data.clear()
        st.rerun()
    
    try:
        # STREAMLINED DASHBOARD STRUCTURE
        with st.spinner("Loading streamlined dashboard..."):
            
            # 1. ML Summary with Completed Positions
            render_streamlined_ml_summary()
            st.markdown("---")
            
            # 2. Important Sentiment Metrics Overview
            render_streamlined_sentiment_metrics()
            st.markdown("---")
            
            # 3. Next Day Predictions
            render_streamlined_next_day_predictions()
            st.markdown("---")
            
            # 4. News Sentiment Important Metrics
            render_streamlined_news_sentiment()
            st.markdown("---")
            
            # 5. Social Sentiment Important Metrics
            render_streamlined_social_sentiment()
            st.markdown("---")
            
            # 6. Technical Analysis Important Metrics
            render_streamlined_technical_analysis()
            st.markdown("---")
            
            # 7. Unified Positions Area (All metrics combined)
            render_unified_positions_area()
        
        # Footer
        st.markdown("---")
        st.markdown("*Streamlined dashboard - All data sourced from live SQL database. Refresh to update.*")
        
    except DatabaseError as e:
        st.error(f"🚨 Database Error: {e}")
        st.info("Please check database connectivity and try again.")
        
    except DataError as e:
        st.error(f"📊 Data Error: {e}")
        st.info("The system may be updating data. Please try refreshing in a moment.")
        
    except Exception as e:
        st.error(f"💥 Unexpected Error: {e}")
        st.info("Please contact system administrator if this persists.")


if __name__ == "__main__":
    main()